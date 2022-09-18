# TODO: alles van v1 verwijderen
# TODO: op de juiste manier rekening houden met nodata in raster
# TODO: aansluiten op QGIS plugin
# TODO: add support for cell that extend beyond dem (fill with nodata?)
# TODO: support for grid refinement
# TODO: support for nodata obstacles (e.g. pand)
# TODO: casussen als amstelstation cell 3138


from typing import List, Tuple, Union

from threedigrid.admin.gridadmin import GridH5Admin
from threedigrid.admin.lines.models import Lines
import numpy as np
from osgeo import ogr
from osgeo import osr
from osgeo import gdal
from scipy.ndimage import label, generate_binary_structure, maximum_position
from scipy.signal import find_peaks

ogr.UseExceptions()
gdal.UseExceptions()

OGR_MEMORY_DRIVER = ogr.GetDriverByName('Memory')
SEARCH_STRUCTURE = generate_binary_structure(2, 2)
TOP = 'top'
RIGHT = 'right'
BOTTOM = 'bottom'
LEFT = 'left'
NA = 'N/A'
# SIDE_INDEX = {
#     TOP: np.index_exp[0, :],
#     RIGHT: np.index_exp[:, -1],
#     BOTTOM: np.index_exp[-1, :],
#     LEFT: np.index_exp[:, 0]
# }
OPPOSITE = {
    LEFT: RIGHT,
    RIGHT: LEFT,
    TOP: BOTTOM,
    BOTTOM: TOP
}
REFERENCE = 'reference'
NEIGH = 'neigh'
MERGED = 'merged'
CREATION_METHOD_CONNECT_MAXIMA = 0
CREATION_METHOD_NEIGH_SEARCH = 1
CREATION_METHOD_FREE_SEARCH = 2
CREATION_METHOD_MOCK = 3
PSEUDO_INFINITE = 9999
COORD_DECIMALS = 5


def read_as_array(
        raster: gdal.Dataset,
        bbox: Union[List, Tuple],
        band_nr: int = 1,
        pad: bool = False,
        decimals: int = 5
) -> np.ndarray:
    """
    Read part of raster that intersects with bounding box in geo coordinates as array

    :param band_nr: band number
    :param raster: input raster dataset
    :param bbox: Bounding box corner coordinates in the input rasters crs: [x0, y0, x1, y1]
    :param pad: pad with nodata value if partially out of extent. alternatively, return only the part of input raster
    that intersects with the bbox
    """
    band = raster.GetRasterBand(band_nr)
    gt = raster.GetGeoTransform()
    inv_gt = gdal.InvGeoTransform(gt)
    x0, y0 = (round(val, decimals) for val in gdal.ApplyGeoTransform(inv_gt, float(bbox[0]), float(bbox[1])))
    x1, y1 = (round(val, decimals) for val in gdal.ApplyGeoTransform(inv_gt, float(bbox[2]), float(bbox[3])))
    xmin, ymin = min(x0, x1), min(y0, y1)
    xmax, ymax = max(x0, x1), max(y0, y1)
    if xmin > raster.RasterXSize or ymin > raster.RasterYSize or xmax < 0 or ymax < 0:
        raise ValueError('bbox does not intersect with raster')

    intersection_xmin, intersection_ymin = max(xmin, 0), max(ymin, 0)
    intersection_xmax, intersection_ymax = min(xmax, raster.RasterXSize), min(ymax, raster.RasterYSize)
    arr = band.ReadAsArray(
        int(intersection_xmin),
        int(intersection_ymin),
        int(intersection_xmax - intersection_xmin),
        int(intersection_ymax - intersection_ymin)
    )
    if pad:
        ndv = band.GetNoDataValue()
        arr_pad = np.pad(
            arr,
            ((int(intersection_ymin - ymin), int(ymax - intersection_ymax)),
             (int(intersection_xmin - xmin), int(xmax - intersection_xmax))),
            'constant',
            constant_values=((ndv, ndv), (ndv, ndv))
        )
        return arr_pad
    else:
        return arr


def filter_lines_by_node_ids(lines: Lines, node_ids: np.array):
    boolean_mask = np.sum(np.isin(lines.line_nodes, node_ids), axis=1) > 0
    line_ids = lines.id[boolean_mask]
    result = lines.filter(id__in=line_ids)
    return result


class Edge:
    """Edge of cell, always shared between two cells.

    Drawing direction is always left -> right or bottom -> top.

    Therefore for a left -> right edge, the neigh_l is up and the neigh_r is down
    """

    def __init__(self,
                 parent,  # Topology
                 cell_1,  # Cell
                 cell_2  # Cell
                 ):
        self.parent = parent
        self.cell_1 = cell_1
        self.cell_2 = cell_2
        side_coords1 = cell_1.side_coords()
        side_coords2 = cell_2.side_coords()
        for side_1 in [TOP, BOTTOM, LEFT, RIGHT]:
            for side_2 in [TOP, BOTTOM, LEFT, RIGHT]:
                intersection_coords = intersection(side_coords1[side_1], side_coords2[side_2])
                if intersection_coords:
                    self.start_coord, self.end_coord = intersection_coords
                    if (side_1 == TOP and side_2 == BOTTOM) or (side_1 == LEFT and side_2 == RIGHT):
                        self.neigh_r = cell_1
                        self.neigh_l = cell_2
                    elif (side_1 == BOTTOM and side_2 == TOP) or (side_1 == RIGHT and side_2 == LEFT):
                        self.neigh_r = cell_2
                        self.neigh_l = cell_1
                    break
            if intersection_coords:
                break
        if not intersection_coords:
            raise ValueError('Input cells do not share an edge')
        cell_1.add_edge(side_1, self)
        cell_2.add_edge(side_2, self)
        self.obstacles = list()

        # calculate exchange levels: 1D array of max of pixel pairs along the edge
        pxsize = self.parent.dem.GetGeoTransform()[1]

        if self.is_bottom_up():
            bbox = [self.start_coord[0] - pxsize, self.start_coord[1], self.end_coord[0] + pxsize, self.end_coord[1]]
        else:
            bbox = [self.start_coord[0], self.start_coord[1] - pxsize, self.end_coord[0], self.end_coord[1] + pxsize]
        # try:
        arr = read_as_array(raster=self.parent.dem, bbox=bbox, pad=True)
        self.exchange_levels = np.nanmax(arr, axis=int(self.is_bottom_up()))
        self.threedi_exchange_level = np.nanmin(self.exchange_levels)
        # except ValueError:  # cell is at model boundary and therefore edge is out of dem extent
        #     self.exchange_levels = None
        #     self.threedi_exchange_level = None

    # @property
    # def neigh_l(self):
    #     return self._neigh_l
    #
    # @neigh_l.setter
    # def neigh_l(self, cell):
    #     self._neigh_l = cell
    #     self.update_is_connected()
    #
    # @property
    # def neigh_r(self):
    #     return self._neigh_r
    #
    # @neigh_r.setter
    # def neigh_r(self, cell):
    #     self._neigh_r = cell
    #     self.update_is_connected()
    #
    # def update_is_connected(self):
    #     if self.neigh_l is None or self.neigh_r is None:
    #         self.is_connected = False
    #     else:
    #         line_nodes_list = self.parent.line_nodes.tolist()
    #         self.is_connected = [self.neigh_l.id, self.neigh_r.id] in line_nodes_list or \
    #                             [self.neigh_r.id, self.neigh_l.id] in line_nodes_list

    def is_bottom_up(self):
        return self.start_coord[0] == self.end_coord[0]

    def generate_connecting_obstacle(self, min_obstacle_height, search_precision):
        """If a high line element in the DEM is slightly skewed relative to the grid, the obstacles it produces may
        contain a gap at the location where it switches sides. This method generates an obstacle that connects the
        two sides, e.g.:

            |                   |
            |         --->      |
            |         --->      |___
                |     --->          |
                |                   |
                |                   |
        """
        if self.neigh_l is None or self.neigh_r is None:
            print("A")
            return
        if self.is_bottom_up():
            print("B")
            side_pairs = [(TOP, BOTTOM), (BOTTOM, TOP)]
        else:
            print("C")
            side_pairs = [(LEFT, RIGHT), (RIGHT, LEFT)]
        for side_1, side_2 in side_pairs:
            neigh_edges_1 = self.neigh_l.edges[side_1]
            neigh_edges_2 = self.neigh_r.edges[side_2]
            print(f"neigh_edges_1: {neigh_edges_1}")
            print(f"neigh_edges_2: {neigh_edges_2}")
            if neigh_edges_1 and neigh_edges_2:
                # find the highest obstacle that applies to all of neigh_edges_1 / neigh_edges_2
                highest_shared_obstacle_1 = highest(shared_obstacles(neigh_edges_1))
                highest_shared_obstacle_2 = highest(shared_obstacles(neigh_edges_2))
                print(f"highest_shared_obstacle_1: {highest_shared_obstacle_1}")
                print(f"highest_shared_obstacle_2: {highest_shared_obstacle_2}")
                if highest_shared_obstacle_1 and highest_shared_obstacle_2:
                    cell_pair = CellPair(reference_cell=self.neigh_l, neigh_cell=self.neigh_r)
                    search_start_pos_in_cell_pair = None
                    search_end_pos_in_cell_pair = None
                    print(f"self: {self}")
                    print(f"highest_shared_obstacle_1.start_edges(): {highest_shared_obstacle_1.start_edges()}")
                    if self in highest_shared_obstacle_1.start_edges():
                        print("self in highest_shared_obstacle_1.start_edges()")
                        search_start_pos = highest_shared_obstacle_1.segments[0].from_pos
                        search_start_pos_in_cell_pair = cell_pair.transform(
                            pos=search_start_pos,
                            from_array=REFERENCE,
                            to_array=MERGED
                        )
                    print(f"highest_shared_obstacle_1.end_edges(): {highest_shared_obstacle_1.end_edges()}")
                    if self in highest_shared_obstacle_1.end_edges():
                        print("self in highest_shared_obstacle_1.end_edges()")
                        search_start_pos = highest_shared_obstacle_1.segments[-1].to_pos
                        search_start_pos_in_cell_pair = cell_pair.transform(
                            pos=search_start_pos,
                            from_array=REFERENCE,
                            to_array=MERGED
                        )
                    print(f"highest_shared_obstacle_2.start_edges(): {highest_shared_obstacle_2.start_edges()}")
                    if self in highest_shared_obstacle_2.start_edges():
                        print("self in highest_shared_obstacle_2.start_edges()")
                        search_end_pos = highest_shared_obstacle_2.segments[0].from_pos
                        search_end_pos_in_cell_pair = cell_pair.transform(
                            pos=search_end_pos,
                            from_array=NEIGH,
                            to_array=MERGED
                        )
                    print(f"highest_shared_obstacle_2.end_edges(): {highest_shared_obstacle_2.end_edges()}")
                    if self in highest_shared_obstacle_2.end_edges():
                        print("self in highest_shared_obstacle_2.end_edges()")
                        search_end_pos = highest_shared_obstacle_2.segments[-1].to_pos
                        search_end_pos_in_cell_pair = cell_pair.transform(
                            pos=search_end_pos,
                            from_array=NEIGH,
                            to_array=MERGED
                        )
                    if search_start_pos_in_cell_pair is not None and search_end_pos_in_cell_pair is not None:
                        connecting_obstacle_segment = ObstacleSegment.from_pixels(
                            pixels=cell_pair.pixels,
                            creation_method=CREATION_METHOD_NEIGH_SEARCH,
                            from_side=None,
                            from_pos=search_start_pos_in_cell_pair,
                            to_side=None,
                            to_positions=search_end_pos_in_cell_pair,
                            search_precision=search_precision
                        )
                        if connecting_obstacle_segment is not None:
                            connecting_obstacle_segment.parent = self.neigh_l
                            connecting_obstacle_segment.from_pos = cell_pair.clip(
                                pos=cell_pair.transform(
                                    pos=connecting_obstacle_segment.from_pos,
                                    from_array=MERGED,
                                    to_array=REFERENCE
                                ),
                                clip_array=REFERENCE
                            )
                            connecting_obstacle_segment.to_pos = cell_pair.clip(
                                pos=cell_pair.transform(
                                    pos=connecting_obstacle_segment.to_pos,
                                    from_array=MERGED,
                                    to_array=REFERENCE
                                ),
                                clip_array=REFERENCE
                            )
                            connecting_obstacle_segment.calculate_coords()
                            if connecting_obstacle_segment.height > \
                                    self.threedi_exchange_level + \
                                    min_obstacle_height - \
                                    search_precision:
                                obstacle = Obstacle(segments=[connecting_obstacle_segment], edges=[self])
                                self.obstacles.append(obstacle)
                                self.parent.obstacles.append(obstacle)
                                return

    def filter_obstacles(self, min_obstacle_height: float, search_precision: float):
        """Filter obstacles of this edge based on several criteria. Updates self.obstacles"""
        return
        # filtered_obstacles = list()
        # for obstacle in self.obstacles:
        #     select_this_obstacle = True
        #
        #     # keep Obstacles based on 'free search' connection to other side only if
        #     # both neighbouring exchange levels are significantly lower then the obstacle crest level
        #     obstacle_has_free_search_segment = False
        #     for segment in obstacle.segments:
        #         if segment.creation_method == CREATION_METHOD_FREE_SEARCH:
        #             obstacle_has_free_search_segment = True
        #
        #     if obstacle_has_free_search_segment:
        #         if self.is_bottom_up():
        #             opposite_edges_left = self.neigh_l.edges[LEFT]
        #             opposite_edges_right = self.neigh_r.edges[RIGHT]
        #         else:
        #             opposite_edges_left = self.neigh_l.edges[TOP]
        #             opposite_edges_right = self.neigh_r.edges[BOTTOM]
        #         if opposite_edges_left:
        #             opposite_left_exchange_level = lowest(opposite_edges_left).threedi_exchange_level
        #         else:
        #             opposite_left_exchange_level = PSEUDO_INFINITE
        #         print(f"opposite_edges_right: {opposite_edges_right}")
        #         if opposite_edges_right:
        #             opposite_right_exchange_level = lowest(opposite_edges_right).threedi_exchange_level
        #         else:
        #             opposite_right_exchange_level = PSEUDO_INFINITE
        #         print(f"obstacle.height: {obstacle.height}")
        #         print(f"opposite_left_exchange_level: {opposite_left_exchange_level}")
        #         print(f"opposite_right_exchange_level: {opposite_right_exchange_level}")
        #         if obstacle.height < opposite_left_exchange_level + min_obstacle_height - search_precision \
        #                 or obstacle.height < opposite_right_exchange_level + min_obstacle_height - search_precision:
        #             select_this_obstacle = False
        #
        #     if select_this_obstacle:
        #         filtered_obstacles.append(obstacle)
        # self.obstacles = filtered_obstacles

    def geometry(self):
        geom = ogr.Geometry(ogr.wkbLineString)
        geom.AddPoint(self.start_coord[0], self.start_coord[1])
        geom.AddPoint(self.end_coord[0], self.end_coord[1])
        return geom

    @property
    def highest_obstacle(self):
        return highest(self.obstacles)


class Topology:
    """
    Holds group of edges, cells and their topological relations
    """

    def __init__(
            self,
            gr: GridH5Admin,
            cell_ids: List,
            dem: gdal.Dataset
    ):
        """Note: cells in topology will also include neighbours of cells indicated by cell_ids"""
        self.dem = dem
        self.obstacles = list()
        self.final_obstacle_segments = dict()

        # Get all flowlines that are connected to any of the cell_ids
        flowlines = filter_lines_by_node_ids(gr.lines.subset('2D_OPEN_WATER'), node_ids=cell_ids)

        # get node coordinates
        self.line_nodes = flowlines.line_nodes

        # get cell coordinates
        threedigrid_cells = gr.cells.filter(id__in=self.line_nodes.flatten())
        cell_properties = threedigrid_cells.only('id', 'cell_coords').data
        self.cell_coords = dict(zip(cell_properties['id'], np.round(cell_properties['cell_coords'].T, COORD_DECIMALS)))

        self.cells = dict()
        for cell_id_i, cell_coords_i in self.cell_coords.items():
            try:
                self.cells[cell_id_i] = Cell(parent=self, id=cell_id_i, coords=cell_coords_i)
            except KeyError:
                continue

        self.cell_topologies = dict()
        for cell in self.cells.values():
            cell_topology = {TOP: [], RIGHT: [], BOTTOM: [], LEFT: []}
            cell_x_coords = cell.coords[[0, 2]]
            cell1_xmax = np.max(cell_x_coords)
            cell1_xmin = np.min(cell_x_coords)

            # next_cells: cells up / to the right
            next_cell_ids = self.line_nodes[np.where(self.line_nodes[:, 0] == cell.id), 1].flatten()
            for next_cell_id in next_cell_ids:
                cell2_xmin = np.min(self.cells[next_cell_id].coords[[0, 2]])
                if cell1_xmax == cell2_xmin:  # aligned horizontally if True
                    cell_topology[RIGHT].append(self.cells[next_cell_id])
                else:
                    cell_topology[TOP].append(self.cells[next_cell_id])

            # previous_cells: cells down / to the left
            previous_cell_ids = self.line_nodes[np.where(self.line_nodes[:, 1] == cell.id), 0].flatten()
            for previous_cell_id in previous_cell_ids:
                cell2_xmax = np.max(self.cells[previous_cell_id].coords[[0, 2]])
                if cell1_xmin == cell2_xmax:  # aligned horizontally if True
                    cell_topology[LEFT].append(self.cells[previous_cell_id])
                else:
                    cell_topology[BOTTOM].append(self.cells[previous_cell_id])
            self.cell_topologies[cell.id] = cell_topology

        # edges
        self.edges = dict()  # {line_nodes: Edge}
        for line_nodes in self.line_nodes.tolist():
            start_cell = self.cells[line_nodes[0]]
            end_cell = self.cells[line_nodes[1]]
            edge = Edge(parent=self, cell_1=start_cell, cell_2=end_cell)
            self.edges[tuple(line_nodes)] = edge

    def neigh_cells(self, cell_id: int, location: str):
        return self.cell_topologies[cell_id][location]

    def filter_obstacles(self, min_obstacle_height: float, search_precision: float):
        """Filter obstacles of all edges based on several criteria. Updates obstacles for all edges in this Topology"""
        for edge in self.edges.values():
            edge.filter_obstacles(min_obstacle_height=min_obstacle_height, search_precision=search_precision)

    def deduplicate_obstacles(self, search_precision):
        result = []
        print("Deduplicate obstacles...")
        for i, obstacle in enumerate(self.obstacles):
            has_duplicate = False
            print(f"processing obstacle {i}: {obstacle.geometry.ExportToWkt()}")
            for comparison in self.obstacles[i+1:]:
                print(f"comparing with obstacle: {comparison.geometry.ExportToWkt()}")
                print(f"equals volgens ogr: {obstacle.geometry.Equals(comparison.geometry)}")
                print(f"abs(obstacle.height - comparison.height): {abs(obstacle.height - comparison.height)}")
                if obstacle.geometry.Equals(comparison.geometry) and \
                        abs(obstacle.height - comparison.height) < search_precision:
                    has_duplicate = True
                    break
            if not has_duplicate:
                result.append(obstacle)

        # update topology obstacles
        self.obstacles = result

        # remove obstacles from edge if they are no longer part of this topology
        for edge in self.edges.values():
            edge.obstacles = [obstacle for obstacle in edge.obstacles if obstacle in result]

    def select_final_obstacle_segments(self):
        for edge in self.edges.values():
            if edge.highest_obstacle is not None:
                for segment in edge.highest_obstacle.segments:
                    segment_to_add = segment.clone()
                    segment_to_add.height = edge.highest_obstacle.height
                    segment_to_add.edges = [edge]
                    key = ((segment_to_add.from_x, segment_to_add.from_y), (segment_to_add.to_x, segment_to_add.to_y))
                    # replace existing segment with this segment if it has higher height
                    try:
                        if segment_to_add.height > self.final_obstacle_segments[key].height:
                            self.final_obstacle_segments[key] = segment_to_add
                    except KeyError:
                        self.final_obstacle_segments[key] = segment_to_add


class ObstacleSegment:
    """
    Connection between maxima on two sides (LEFT|RIGHT|TOP|BOTTOM) of a cell
    """
    def __init__(self,
                 parent,  # Cell
                 creation_method: int,
                 from_side: str = None,
                 to_side: str = None,
                 from_pos: tuple = None,
                 to_pos: tuple = None,
                 height: float = None,
                 search_precision: float = None
                 ):
        self.parent = parent
        self.creation_method = creation_method
        self.from_side = from_side
        self.to_side = to_side
        self.from_pos = from_pos  # index in parent cell pixels array
        self.to_pos = to_pos  # index in parent cell pixels array
        self.height = height
        self.search_precision = search_precision
        self.from_x, self.from_y, self.to_x, self.to_y = None, None, None, None
        self._edges = None

    def __str__(self):
        return str(self.__dict__)

    @staticmethod
    def from_pixels(
            pixels,
            creation_method: int,
            from_side,
            to_side,
            from_pos,
            to_positions,
            search_precision,
            search_structure=SEARCH_STRUCTURE
    ):
        """
        Find obstacle segment in 2D numpy array of DEM pixels

        Returns None if no obstacle is found
        """
        # from_val or max_to_val is not significantly higher than lowest point in flow domain
        # i.e., flat or smoothly sloping cell
        # print(f"pixels: {pixels}")
        # print(f"from_pos: {from_pos}")

        from_val = pixels[from_pos]
        max_to_val = np.nanmax(pixels[to_positions])
        if np.nanmin([from_val, max_to_val]) - np.nanmin(pixels) < search_precision:
            return None

        # find maximum position within to_positions
        mask = np.zeros(pixels.shape, np.bool)
        mask[to_positions] = True

        # now find the obstacle height iteratively
        hmin = np.nanmin(pixels)
        hmax = np.nanmax([from_val, max_to_val])

        # case: from and to positions already connect at hmax
        labelled_pixels, labelled_pixels_nr_features = label(pixels >= hmax, structure=search_structure)
        from_pixel_label = int(labelled_pixels[from_pos])
        to_pixel_labels = labelled_pixels[to_positions]
        if from_pixel_label != 0 and np.any(to_pixel_labels == from_pixel_label):
            obstacle_segment_height = hmax

        else:
            while (hmax - hmin) > search_precision:
                hcurrent = np.nanmean([hmin, hmax])
                labelled_pixels, _ = label(pixels > hcurrent, structure=search_structure)
                from_pixel_label = int(labelled_pixels[from_pos])
                to_pixel_labels = labelled_pixels[to_positions]
                if from_pixel_label != 0 and np.any(to_pixel_labels == from_pixel_label):
                    # the two sides are connected at this threshold
                    hmin = hcurrent
                else:
                    # the two sides are NOT connected at this threshold
                    hmax = hcurrent

            obstacle_segment_height = np.mean([hmin, hmax])
            # exluding pixels from to_pixels that are not connected to from_pos
            labelled_pixels_hmin, _ = label(pixels > hmin, structure=search_structure)
            mask[labelled_pixels_hmin != labelled_pixels_hmin[from_pos]] = False

        to_pixels = pixels.copy()
        to_pixels[mask==False] = -PSEUDO_INFINITE
        to_positions_max_pos = maximum_position(to_pixels)
        obstacle_segment = ObstacleSegment(
            parent=None,
            creation_method=creation_method,
            from_side=from_side,
            to_side=to_side,
            from_pos=from_pos,
            to_pos=to_positions_max_pos,
            search_precision=search_precision
        )
        obstacle_segment.height = obstacle_segment_height
        return obstacle_segment

    @property
    def edges(self):
        """
        Return the edges that the obstacle segment belongs to. Valid only for left/right or top/bottom obstacle segments.
        Returns None for diagonal obstacle segments
        """
        if self._edges is None:
            cell_height, cell_width = self.parent.pixels.shape
            labelled_pixels, labelled_pixels_nr_features = label(
                self.parent.pixels >= self.height - self.search_precision,
                structure=SEARCH_STRUCTURE
            )
            try:
                obstacle_pixels = labelled_pixels == labelled_pixels[self.from_pos]
            except Exception as e:
                print(f'Something went wrong with an obstacle segment in cell {self.parent.id}')
                raise e
            nr_obstacle_pixels_left = np.nansum(obstacle_pixels[:, 0:int(cell_width / 2)] == 1)
            nr_obstacle_pixels_right = np.nansum(obstacle_pixels[:, int(cell_width / 2):] == 1)
            nr_obstacle_pixels_top = np.nansum(obstacle_pixels[0:int(cell_height / 2), :] == 1)
            nr_obstacle_pixels_bottom = np.nansum(obstacle_pixels[int(cell_height / 2):, :] == 1)

            is_single = True
            if (self.starts_at(TOP) and self.ends_at(BOTTOM)) or (self.starts_at(BOTTOM) and self.ends_at(TOP)):
                if nr_obstacle_pixels_left > nr_obstacle_pixels_right:
                    preferred_side = LEFT
                else:
                    preferred_side = RIGHT
            elif (self.starts_at(LEFT) and self.ends_at(RIGHT)) or (self.starts_at(RIGHT) and self.ends_at(LEFT)):
                if nr_obstacle_pixels_top > nr_obstacle_pixels_bottom:
                    preferred_side = TOP
                else:
                    preferred_side = BOTTOM
            else:
                is_single = False
                self._edges = None
            if is_single:
                if len(self.parent.edges[preferred_side]) > 0:
                    self._edges = self.parent.edges[preferred_side]
                else:
                    self._edges = self.parent.edges[OPPOSITE[preferred_side]]

        return self._edges

    @edges.setter
    def edges(self, edge: Edge):
        # TODO [HIER VERDER GAAN] met grid refinement kan een obstacle segment aan twee edges toebehoren die in elkaars
        #  verlengde liggen. Omzetting van `edge` naar `edges` is halverwege
        self._edges = edge

    def is_valid(self, min_obstacle_height: float):
        """Test obstacle segment against a set of criteria, ie.e. should """
        return True

        # If obstacle segment is direct (top->bottom or left->right), it is always valid
        # if ((self.starts_at(TOP) and self.ends_at(BOTTOM)) or
        #         (self.starts_at(BOTTOM) and self.ends_at(TOP)) or
        #         (self.starts_at(LEFT) and self.ends_at(RIGHT)) or
        #         (self.starts_at(RIGHT) and self.ends_at(LEFT))
        # ):
        #     return True
        #
        # # TODO: I think the validity check below should be moved to Edge.filter_obstacles(). it is not possible to
        # #  check this for Obstacle Segments, because they have not yet been assigned to an edge
        # # stricter filtering for diagonal obstacles:
        # # obstacle must be significantly higher than *highest* exchange height of the obstacle-side edges
        # # and significantly higher than the *lowest* exchange height on the opposite side edges
        # from_side_edges = self.parent.edges[self.from_side]
        # from_side_exchange_level = from_side_edge.threedi_exchange_level if from_side_edge else PSEUDO_INFINITE
        # to_side_edge = self.parent.edges[self.to_side]
        # to_side_exchange_level = to_side_edge.threedi_exchange_level if to_side_edge else PSEUDO_INFINITE
        # opposite_from_side_edge = self.parent.edges[OPPOSITE[self.from_side]]
        # opposite_from_side_exchange_level = opposite_from_side_edge.threedi_exchange_level if opposite_from_side_edge \
        #     else PSEUDO_INFINITE
        # opposite_to_side_edge = self.parent.edges[OPPOSITE[self.to_side]]
        # opposite_to_side_exchange_level = opposite_to_side_edge.threedi_exchange_level if opposite_to_side_edge \
        #     else PSEUDO_INFINITE
        #
        # if self.height > max(from_side_exchange_level, to_side_exchange_level) + min_obstacle_height and \
        #         self.height > min(opposite_from_side_exchange_level, opposite_to_side_exchange_level) + \
        #         min_obstacle_height:
        #     return True
        # else:
        #     return False

    def starts_at(self, side):
        """Find out if the obstacle segment starts at `side`, including cases where the obstacle segment's from_side is
        not `side`, but the obstacle segment starts in the corner pixel of the cell"""
        if self.from_side == side:
            return True
        if side == TOP and self.from_pos[0] == 0:
            return True
        if side == RIGHT and self.from_pos[1] in [-1, self.parent.pixels.shape[1] - 1]:
            return True
        if side == BOTTOM and self.from_pos[0] in [-1, self.parent.pixels.shape[0] - 1]:
            return True
        if side == LEFT and self.from_pos[1] == 0:
            return True
        return False

    def ends_at(self, side):
        """Find out if the obstacle segment ends at `side`, including cases where the obstacle segment's to_side is
        not `side`, but the obstacle segment ends in the corner pixel of the cell"""
        if self.to_side == side:
            return True
        if side == TOP and self.to_pos[0] == 0:
            return True
        if side == RIGHT and self.to_pos[1] in [-1, self.parent.pixels.shape[1] - 1]:
            return True
        if side == BOTTOM and self.to_pos[0] in [-1, self.parent.pixels.shape[0] - 1]:
            return True
        if side == LEFT and self.to_pos[1] == 0:
            return True
        return False

    def start_edges(self):
        result = []
        for side in [TOP, RIGHT, BOTTOM, LEFT]:
            if self.starts_at(side):
                result += self.parent.edges[side]
        return result

    def end_edges(self):
        result = []
        for side in [TOP, RIGHT, BOTTOM, LEFT]:
            if self.ends_at(side):
                result += self.parent.edges[side]
        return result

    def clone(self):
        result = ObstacleSegment(
            parent=self.parent,
            creation_method=self.creation_method,
            from_side=self.from_side,
            to_side=self.to_side,
            from_pos=self.from_pos,
            to_pos=self.to_pos,
            height=self.height,
            search_precision=self.search_precision
        )
        result.edges = self.edges
        result.from_x = self.from_x
        result.from_y = self.from_y
        result.to_x = self.to_x
        result.to_y = self.to_y
        return result

    def reverse(self):

        from_side = self.from_side
        to_side = self.to_side
        from_pos = self.from_pos
        to_pos = self.to_pos

        self.from_side = to_side
        self.to_side = from_side
        self.from_pos = to_pos
        self.to_pos = from_pos  # index in parent cell pixels array

        if self.from_x is not None and self.from_y is not None and self.to_x is not None and self.to_y is not None:
            self.calculate_coords()

    def calculate_coords(self):
        gt = self.parent.parent.dem.GetGeoTransform()

        # translate -1 index to positive index
        if self.from_pos[0] >= 0:
            from_pos_y = self.from_pos[0]
        else:
            from_pos_y = self.parent.pixels.shape[0] + self.from_pos[0]

        if self.from_pos[1] >= 0:
            from_pos_x = self.from_pos[1]
        else:
            from_pos_x = self.parent.pixels.shape[1] + self.from_pos[1]

        if self.to_pos[0] >= 0:
            to_pos_y = self.to_pos[0]
        else:
            to_pos_y = self.parent.pixels.shape[0] + self.to_pos[0]

        if self.to_pos[1] >= 0:
            to_pos_x = self.to_pos[1]
        else:
            to_pos_x = self.parent.pixels.shape[1] + self.to_pos[1]

        self.from_x = self.parent.coords[0] + from_pos_x * abs(gt[1]) + abs(gt[1]) / 2
        self.to_x = self.parent.coords[0] + to_pos_x * abs(gt[1]) + abs(gt[1]) / 2
        self.from_y = self.parent.coords[3] - (from_pos_y * abs(gt[5]) + abs(gt[5]) / 2)
        self.to_y = self.parent.coords[3] - (to_pos_y * abs(gt[5]) + abs(gt[5]) / 2)

        # snap to cell border
        # use array idx instead of 'side' to snap to cell corner where relevant
        if self.from_pos[1] == 0:  # left
            self.from_x -= abs(gt[1]) / 2
        elif self.from_pos[1] in [-1, self.parent.pixels.shape[1] - 1]:  # right
            self.from_x += abs(gt[1]) / 2
        if self.from_pos[0] == 0:  # top
            self.from_y += abs(gt[5]) / 2
        elif self.from_pos[0] in [-1, self.parent.pixels.shape[0] - 1]:  # bottom
            self.from_y -= abs(gt[5]) / 2

        if self.to_pos[1] == 0:  # left
            self.to_x -= abs(gt[1]) / 2
        elif self.to_pos[1] in [-1, self.parent.pixels.shape[1] - 1]:  # right
            self.to_x += abs(gt[1]) / 2
        if self.to_pos[0] == 0:  # top
            self.to_y += abs(gt[5]) / 2
        elif self.to_pos[0] in [-1, self.parent.pixels.shape[0] - 1]:  # bottom
            self.to_y -= abs(gt[5]) / 2

    def geometry(self):
        geom = ogr.Geometry(ogr.wkbLineString)
        geom.AddPoint(self.from_x, self.from_y)
        geom.AddPoint(self.to_x, self.to_y)
        return geom


class Obstacle:
    """
    Group of one or more ObstacleSegments that cross a cell or two neighbouring cells from bottom to top or
    from left to right
    """

    def __init__(self, segments: List[ObstacleSegment], edges: List[Edge]):
        self.segments = segments
        self.edges = edges

    def start_edges(self) -> [Edge]:
        """
        Returns the edge or edges at which this obstacle starts
        """
        return self.segments[0].start_edges()

    def end_edges(self) -> [Edge]:
        """
        Returns the edge or edges at which this obstacle ends
        """
        return self.segments[-1].end_edges()

    @property
    def height(self):
        min_height = PSEUDO_INFINITE
        for segment in self.segments:
            if segment.height < min_height:
                min_height = segment.height
        return min_height

    @property
    def geometry(self):
        if len(self.segments) == 1:
            return self.segments[0].geometry()
        else:
            coords = set()
            for segment in self.segments:
                coords.add((segment.from_x, segment.from_y))
                coords.add((segment.to_x, segment.to_y))
            coords_list = list(coords)
            coords_list.sort()
        geom = ogr.Geometry(ogr.wkbLineString)
        for coord in coords_list:
            geom.AddPoint(coord[0], coord[1])
        return geom

    def as_ogr_feature(self):
        feature_defn = ogr.FeatureDefn()

        field_defn_id = ogr.FieldDefn('id', ogr.OFTInteger)
        # field_defn_3di = ogr.FieldDefn('exchange_level_3di', ogr.OFTReal)
        field_defn_crest_level = ogr.FieldDefn('crest_level', ogr.OFTReal)

        feature_defn.AddFieldDefn(field_defn_id)  # not yet set in this function
        # feature_defn.AddFieldDefn(field_defn_3di)
        feature_defn.AddFieldDefn(field_defn_crest_level)

        feature_defn.SetGeomType(ogr.wkbLineString)
        feature = ogr.Feature(feature_defn)

        feature.SetGeometry(self.geometry)
        feature['id'] = -1
        # feature['exchange_level_3di'] = obstacle.threedi_exchange_level
        feature['crest_level'] = self.height

        return feature


class Cell:
    def __init__(self,
                 parent: Topology,
                 id: int,
                 coords: Union[List, Tuple]
                 ):
        self.id = id
        self.coords = coords
        self.parent = parent
        self.pixels_from_dem(dem=parent.dem)
        self.width = self.pixels.shape[1]
        self.height = self.pixels.shape[0]
        self.obstacle_segments = list()
        self.maxima = None
        self.edges = {TOP: [], RIGHT: [], BOTTOM: [], LEFT: []}

    def __str__(self):
        return str(self.__dict__)

    def pixels_from_dem(self, dem):
        self.pixels = read_as_array(raster=dem, bbox=self.coords, pad=True)
        band = dem.GetRasterBand(1)
        ndv = band.GetNoDataValue()
        maxval = np.nanmax(self.pixels)
        self.pixels[self.pixels == ndv] = maxval + 100
        # TODO replace 100 by min_obstacle_height + search_precision

    def coordinates_to_pixel_position(self, x: float, y: float):
        gt = (self.coords[0],
              self.parent.dem.RasterXSize,
              0,
              self.coords[1],
              0,
              self.parent.dem.RasterYSize
              )
        inv_gt = gdal.InvGeoTransform(gt)
        return gdal.ApplyGeoTransform(inv_gt, x, y)

    def side_coords(self):
        """Return dict with the coordinates of all sides of the cell"""
        xmin, ymin, xmax, ymax = self.coords
        return {
            TOP: ((xmin, ymax), (xmax, ymax)),
            BOTTOM: ((xmin, ymin), (xmax, ymin)),
            LEFT: ((xmin, ymin), (xmin, ymax)),
            RIGHT: ((xmax, ymin), (xmax, ymax)),
        }

    def add_edge(self, side: str, edge: Edge):
        try:
            existing_edges = self.edges[side]
        except KeyError:
            existing_edges = []
        if not edge in existing_edges:
            existing_edges.append(edge)
        self.edges[side] = existing_edges

    def side_of_edge(self, edge):
        for side in [TOP, BOTTOM, LEFT, RIGHT]:
            for cell_edge in self.edges[side]:
                if edge == cell_edge:
                    return side
        return None

    def filtered_obstacle_segments(self, from_side: str = None, to_side: str = None):
        return [segment for segment in self.obstacle_segments if
                (from_side is None or segment.from_side == from_side) and
                (to_side is None or segment.to_side == to_side)
                ]

    def find_maxima(self, min_peak_prominence):
        self.maxima = dict()
        exchange_levels_around_cell = np.hstack((
            self.pixels[0, :],  # top
            self.pixels[:, -1],  # right
            np.flip(self.pixels[-1, :]),  # bottom
            np.flip(self.pixels[:, 0])  # left
        ))
        exchange_levels_around_cell_head_to_tail = np.hstack([exchange_levels_around_cell] * 3)

        peaks, _ = find_peaks(exchange_levels_around_cell_head_to_tail, prominence=min_peak_prominence)
        peaks_original_idx = peaks - (len(exchange_levels_around_cell))
        real_peaks = peaks_original_idx[
            np.logical_and(
                peaks_original_idx >= 0,
                peaks_original_idx < len(exchange_levels_around_cell)
            )
        ]

        side_len = len(exchange_levels_around_cell) / 4
        for i, side in enumerate([TOP, RIGHT, BOTTOM, LEFT]):
            side_maxima = real_peaks[
                              np.logical_and(
                                  real_peaks >= i * side_len,
                                  real_peaks < (i + 1) * side_len
                              )
                          ] - i * side_len
            if side in [BOTTOM, LEFT]:
                side_maxima = np.flip((side_len - 1) - side_maxima)
            self.maxima[side] = side_maxima.astype(int)

    def connect_maxima(self, search_precision: float, min_obstacle_height: float):
        """Calculate the obstacle heights between all maxima that are not on the same side
        :param search_precision: higher precision results in more accurate obstacle heights, but takes longer to calculate
        :param min_obstacle_height: passed to obstacle_segment.is_valid()
        """
        for fro, to in [
            (TOP, RIGHT),
            (TOP, BOTTOM),
            (TOP, LEFT),
            (LEFT, RIGHT),
            (LEFT, BOTTOM),
            (RIGHT, BOTTOM)
        ]:
            # skip cells at model edge
            if len(self.edges[fro]) == 0 or len(self.edges[to]) == 0:
                continue

            pixels = self.pixels
            maxima_fro = self.maxima[fro]
            maxima_to = self.maxima[to]
            for start_pos_1d in maxima_fro:
                if fro == TOP:
                    from_pos = (0, start_pos_1d)
                elif fro == RIGHT:
                    from_pos = (start_pos_1d, self.pixels.shape[1] - 1)
                elif fro == BOTTOM:
                    from_pos = (self.pixels.shape[0] - 1, start_pos_1d)
                elif fro == LEFT:
                    from_pos = (start_pos_1d, 0)
                else:
                    raise ValueError

                for end_pos_1d in maxima_to:
                    if to == TOP:
                        to_pos = (0, end_pos_1d)
                    elif to == RIGHT:
                        to_pos = (end_pos_1d, self.pixels.shape[1] - 1)
                    elif to == BOTTOM:
                        to_pos = (self.pixels.shape[0] - 1, end_pos_1d)
                    elif to == LEFT:
                        to_pos = (end_pos_1d, 0)
                    else:
                        raise ValueError

                    obstacle_segment = ObstacleSegment.from_pixels(
                        pixels=pixels,
                        creation_method=CREATION_METHOD_CONNECT_MAXIMA,
                        from_side=fro,
                        to_side=to,
                        from_pos=from_pos,
                        to_positions=to_pos,
                        search_precision=search_precision
                    )
                    if obstacle_segment is not None:
                        obstacle_segment.parent = self
                    if obstacle_segment.is_valid(min_obstacle_height=min_obstacle_height):
                        obstacle_segment.calculate_coords()
                        self.obstacle_segments.append(obstacle_segment)

    def connect_to_opposite_side(
            self,
            obstacle_segment: ObstacleSegment,
            obstacle_segment_from_side: str,
            obstacle_segment_to_side: str,
            search_forward: bool,
            search_precision: float,
            min_obstacle_height: float
    ) -> List[Obstacle]:
        """Starting from the start or end of a given obstacle segment in this cell,
        Try to reach the opposite side of the cell. The opposite side may also be reached by traversing
        a neighbouring cell. CellPairs with all relevant neighbouring cells are created to conduct the search

        :returns: a list of obstacles that have been identified in the search
        """

        obstacles = list()
        if search_forward:
            search_start_side = obstacle_segment_to_side
            search_start_pos = obstacle_segment.to_pos
            obstacle_segment_begin_side = obstacle_segment_from_side
        else:
            search_start_side = obstacle_segment_from_side
            search_start_pos = obstacle_segment.from_pos
            obstacle_segment_begin_side = obstacle_segment_to_side

        neigh_cells = self.parent.neigh_cells(self.id, search_start_side)
        for neigh_cell in neigh_cells:
            cell_pair = CellPair(reference_cell=self, neigh_cell=neigh_cell)
            target_side = OPPOSITE[obstacle_segment_begin_side]
            additional_obstacle_segments = cell_pair.connect_in_cell_pair(
                search_start_pos_in_reference_cell=search_start_pos,
                target_side=target_side,
                search_forward=search_forward,
                search_precision=search_precision
            )
            if len(additional_obstacle_segments) > 0:  # i.e. other side has been reached
                print(f"search_forward: {search_forward}")
                print(f"cell_pair: ref: {cell_pair.reference_cell.id}, neigh: {cell_pair.neigh_cell.id}")
                if search_forward:
                    obstacle_segments = [obstacle_segment] + additional_obstacle_segments
                else:
                    obstacle_segments = additional_obstacle_segments + [obstacle_segment]
                # determine which edges the Obstacle should be assigned to
                if not cell_pair.smallest():  # cells are of equal size
                    print("cells are of equal size")
                    edges = [cell_pair.edge]
                elif self == cell_pair.smallest():  # cells are of different size, self is smaller
                    print("cells are of different size, self is smaller")
                    ref_cell_location = cell_pair.locate(REFERENCE)
                    print(f"ref_cell_location: {ref_cell_location}")
                    print(f"obstacle_segment_begin_side: {obstacle_segment_begin_side}")
                    if ref_cell_location[1] == obstacle_segment_begin_side:  # [1] = secondary location
                        # e.g. obstacle goes to TOP of smaller, neighbouring cell whose secondary location is TOP
                        edges = cell_pair.neigh_cell.edges[ref_cell_location[0]]  # [0] = primary location
                        print(f"A edges: {edges}")
                    else:
                        # e.g. obstacle goes to TOP of smaller, neighbouring cell whose secondary location is BOTTOM
                        edges = [cell_pair.edge]
                        print(f"B edges: {edges}")
                else:  # cells are of different size, neigh is smaller
                    print("cells are of different size, neigh is smaller")
                    neigh_cell_location = cell_pair.locate(NEIGH)
                    print(f"neigh_cell_location: {neigh_cell_location}")
                    print(f"target_side: {target_side}")
                    if neigh_cell_location[1] == target_side:  # [1] = secondary location
                        # e.g. obstacle starts at BOTTOM of ref cell whose secondary location is BOTTOM, and goes to TOP
                        # of larger neighbouring cell
                        edges = self.edges[neigh_cell_location[0]]
                        print(f"C edges: {edges}")
                    else:
                        # e.g. obstacle starts at BOTTOM of ref cell whose secondary location is TOP, and goes to TOP
                        # of larger neighbouring cell
                        edges = [cell_pair.edge]
                        print(f"D edges: {edges}")
                obstacles.append(Obstacle(segments=obstacle_segments, edges=edges))
        return obstacles

    def create_obstacles_from_segments(self, direct_connection_preference: float,
                                       search_precision: float,
                                       min_obstacle_height: float):
        """
        Create Obstacles from all ObstacleSegments in this Cell

        These include left->right and top->bottom obstacles, pairs of obstacle segments in neighbouring cells
        that as a pair connect opposite sides of the cell.

        Only works when obstacle segments of the cell and all neighbouring cells have been identified first.
        """
        # TODO: voor obstacle segments die top-bottom connecten zoeken of die (evt. met extra obstacle segment aan begin
        #  en/of aan het eind) ook left-right verbinding kan vormen
        direct_connection_obstacles = list()
        indirect_connection_obstacles = list()
        for obstacle_segment in self.obstacle_segments:
            # Loop through both the from_side and the to_side to correctly handle obstacle segments that start and/or
            # end in a cell corner. E.g. the most extreme case, an obstacle segment that goes from top-left to
            # bottom-right. This obstacle starts at top and ends at bottom, starts at top and ends at right, etc.
            for obstacle_segment_from_side in [TOP, LEFT, BOTTOM, RIGHT]:
                if obstacle_segment.starts_at(obstacle_segment_from_side):
                    if obstacle_segment.ends_at(OPPOSITE[obstacle_segment_from_side]):
                        # Obstacle segment DOES constitute an obstacle on its own
                        # Now assign the edges to it
                        if obstacle_segment.from_side == obstacle_segment_from_side and \
                                obstacle_segment.to_side == OPPOSITE[obstacle_segment_from_side]:
                            edges = obstacle_segment.edges
                        else:
                            # find correct edges
                            mock_obstacle_segment = obstacle_segment.clone()
                            mock_obstacle_segment.from_side = obstacle_segment_from_side
                            mock_obstacle_segment.to_side = OPPOSITE[obstacle_segment_from_side]
                            mock_obstacle_segment.edges = None
                            edges = mock_obstacle_segment.edges  # will be calculated because it is None
                        if len(edges) > 0:
                            obstacle = Obstacle([obstacle_segment], edges)
                            for edge in edges:
                                # add to direct_connection_obstacles if obstacle is significanly higher than any of the
                                # edges it belongs to
                                if obstacle.height > edge.threedi_exchange_level + min_obstacle_height:
                                    direct_connection_obstacles.append(obstacle)
                                    break
                    else:
                        # Obstacle segment does NOT constitute an obstacle on its own
                        for obstacle_segment_to_side in [TOP, LEFT, BOTTOM, RIGHT]:
                            if obstacle_segment.ends_at(obstacle_segment_to_side):
                                obstacles_search_forward = self.connect_to_opposite_side(
                                    obstacle_segment=obstacle_segment,
                                    obstacle_segment_from_side=obstacle_segment_from_side,
                                    obstacle_segment_to_side=obstacle_segment_to_side,
                                    search_forward=True,
                                    search_precision=search_precision,
                                    min_obstacle_height=min_obstacle_height
                                )
                                obstacles_search_backward = self.connect_to_opposite_side(
                                    obstacle_segment=obstacle_segment,
                                    obstacle_segment_from_side=obstacle_segment_from_side,
                                    obstacle_segment_to_side=obstacle_segment_to_side,
                                    search_forward=False,
                                    search_precision=search_precision,
                                    min_obstacle_height=min_obstacle_height
                                )
                                for obstacle in obstacles_search_forward + obstacles_search_backward:
                                    if obstacle.height > \
                                            highest(obstacle.edges).threedi_exchange_level + min_obstacle_height:
                                        indirect_connection_obstacles.append(obstacle)
        # simpler obstacles (i.e. direct left->right / top->bottom, or consisting of fewer
        # obstacle segments get preference above more complex ones, as long as their height is
        # the same (with margin direct_connection_preference).
        final_obstacles = direct_connection_obstacles
        for obstacle in indirect_connection_obstacles:
            remove_obstacle = False
            for side1, side2 in [(TOP, BOTTOM), (LEFT, RIGHT)]:
                if remove_obstacle:
                    break
                if obstacle.segments[0].starts_at(side1) and obstacle.segments[-1].ends_at(side2):
                    for compare_obstacle in direct_connection_obstacles:
                        if compare_obstacle.segments[0].starts_at(side1) and \
                                compare_obstacle.segments[-1].ends_at(side2) and \
                                len(obstacle.segments) > len(compare_obstacle.segments) and \
                                obstacle.height < compare_obstacle.height + direct_connection_preference:
                            remove_obstacle = True
                            break
            if not remove_obstacle:
                final_obstacles.append(obstacle)

        for obstacle in final_obstacles:
            for edge in obstacle.edges:
                edge.obstacles.append(obstacle)

        self.parent.obstacles += final_obstacles


class CellPair:
    def __init__(self, reference_cell: Cell, neigh_cell: Cell):
        # TODO build cell pair from edge argument instead of two cells as argument
        self.reference_cell = reference_cell
        self.neigh_cell = neigh_cell
        # print(f'Creating cell pair of (ref) {reference_cell.id} and (neigh) {neigh_cell.id}')
        self.topo = reference_cell.parent
        try:
            self.edge = self.topo.edges[(reference_cell.id, neigh_cell.id)]
        except KeyError:
            self.edge = self.topo.edges[(neigh_cell.id, reference_cell.id)]
        neigh_primary_location, neigh_secondary_location = self.locate(NEIGH)
        reference_primary_location, reference_secondary_location = self.locate(REFERENCE)
        smallest_cell = self.smallest()
        if smallest_cell:
            fill_array = smallest_cell.pixels * 0 - min(np.nanmin(reference_cell.pixels), np.nanmin(neigh_cell.pixels))
            if reference_cell.id == smallest_cell.id:
                smallest_secondary_location = reference_secondary_location
            else:
                smallest_secondary_location = neigh_secondary_location

        # print(f"neigh_primary_location: {neigh_primary_location}, neigh_secondary_location: {neigh_secondary_location}")
        # print(f"reference_primary_location: {reference_primary_location}, reference_secondary_location: {reference_secondary_location}")
        if neigh_primary_location == TOP:
            if not smallest_cell:
                self.pixels = np.vstack([neigh_cell.pixels, reference_cell.pixels])
            else:
                if smallest_secondary_location == LEFT:
                    smallest_cell_pixels = np.hstack([smallest_cell.pixels, fill_array])
                else:
                    smallest_cell_pixels = np.hstack([fill_array, smallest_cell.pixels])
                if reference_cell.id == smallest_cell.id:
                    self.pixels = np.vstack([neigh_cell.pixels, smallest_cell_pixels])
                else:
                    self.pixels = np.vstack([smallest_cell_pixels, reference_cell.pixels])

        elif neigh_primary_location == RIGHT:
            if not smallest_cell:
                self.pixels = np.hstack([reference_cell.pixels, neigh_cell.pixels])
            else:
                if smallest_secondary_location == TOP:
                    smallest_cell_pixels = np.vstack([smallest_cell.pixels, fill_array])
                else:
                    smallest_cell_pixels = np.vstack([fill_array, smallest_cell.pixels])
                if reference_cell.id == smallest_cell.id:
                    self.pixels = np.hstack([smallest_cell_pixels, neigh_cell.pixels])
                else:
                    self.pixels = np.hstack([reference_cell.pixels, smallest_cell_pixels])

        elif neigh_primary_location == BOTTOM:
            if not smallest_cell:
                self.pixels = np.vstack([reference_cell.pixels, neigh_cell.pixels])
            else:
                if smallest_secondary_location == LEFT:
                    smallest_cell_pixels = np.hstack([smallest_cell.pixels, fill_array])
                else:
                    smallest_cell_pixels = np.hstack([fill_array, smallest_cell.pixels])
                if reference_cell.id == smallest_cell.id:
                    self.pixels = np.vstack([smallest_cell_pixels, neigh_cell.pixels])
                else:
                    self.pixels = np.vstack([reference_cell.pixels, smallest_cell_pixels])

        elif neigh_primary_location == LEFT:
            if not smallest_cell:
                self.pixels = np.hstack([neigh_cell.pixels, reference_cell.pixels])
            else:
                if smallest_secondary_location == TOP:
                    smallest_cell_pixels = np.vstack([smallest_cell.pixels, fill_array])
                else:
                    smallest_cell_pixels = np.vstack([fill_array, smallest_cell.pixels])
                if reference_cell.id == smallest_cell.id:
                    self.pixels = np.hstack([neigh_cell.pixels, smallest_cell_pixels])
                else:
                    self.pixels = np.hstack([smallest_cell_pixels, reference_cell.pixels])
        else:
            raise ValueError("Input cells are not neighbours")

        # Determine shifts, i.e. paramaters to transform coordinates between ref cell, neigh cell and merged
        # {pos in ref cell} + self.reference_cell_shift = {pos in merged pixels}
        # {pos in neigh cell} + self.neigh_cell_shift = {pos in merged pixels}

        # Reference
        # x
        if neigh_primary_location == LEFT:
            reference_cell_shift_x = self.neigh_cell.width
        elif reference_secondary_location == RIGHT:
            reference_cell_shift_x = self.reference_cell.width
        else:
            reference_cell_shift_x = 0

        # y
        if neigh_primary_location == TOP:
            reference_cell_shift_y = self.neigh_cell.height
        elif reference_secondary_location == BOTTOM:
            reference_cell_shift_y = self.reference_cell.height
        else:
            reference_cell_shift_y = 0

        # Neigh
        # x
        if neigh_primary_location == RIGHT:
            neigh_cell_shift_x = self.reference_cell.width
        elif neigh_secondary_location == RIGHT:
            neigh_cell_shift_x = self.neigh_cell.width
        else:
            neigh_cell_shift_x = 0

        # y
        if neigh_primary_location == BOTTOM:
            neigh_cell_shift_y = self.reference_cell.height
        elif neigh_secondary_location == BOTTOM:
            neigh_cell_shift_y = self.neigh_cell.height
        else:
            neigh_cell_shift_y = 0

        self.reference_cell_shift = (reference_cell_shift_y, reference_cell_shift_x)
        # print(f"reference_cell_shift: {self.reference_cell_shift}")
        self.neigh_cell_shift = (neigh_cell_shift_y, neigh_cell_shift_x)
        # print(f"neigh_cell_shift: {self.neigh_cell_shift}")

    def smallest(self) -> Cell:
        """
        Returns the smallest cell of self.`reference_cell` and self.`neigh_cell` or None if cells have the same width
        """
        if self.reference_cell.width < self.neigh_cell.width:
            return self.reference_cell
        elif self.reference_cell.width > self.neigh_cell.width:
            return self.neigh_cell
        else:
            return None

    def locate(self, which_cell: str, decimals: int = 5) -> Tuple[str, str]:
        """
        Return primary and secondary location of `which_cell` relative to the other cell in the pair
        If `which_cell` is the largest of the two or both cells are of the same size, secondary location is NA
        :param which_cell: REFERENCE or NEIGH
        """
        # print(f"locating: {which_cell}")
        # preparations
        if which_cell == REFERENCE:
            cell_to_locate = self.reference_cell
            other_cell = self.neigh_cell
        elif which_cell == NEIGH:
            cell_to_locate = self.neigh_cell
            other_cell = self.reference_cell
        else:
            raise ValueError(f"Argument 'which_cell' must be '{REFERENCE}' or '{NEIGH}'")

        # primary location
        primary_location = None
        for where in [TOP, RIGHT, BOTTOM, LEFT]:
            if cell_to_locate in self.topo.neigh_cells(other_cell.id, where):
                primary_location = where
                break
        if not primary_location:
            raise ValueError("Could determine primary location with given arguments")

        # secondary location
        # print(cell_to_locate.width)
        # print(other_cell.width)
        if cell_to_locate.width >= other_cell.width:
            secondary_location = NA
        elif primary_location in [LEFT, RIGHT]:
            bottom_aligned = round(self.reference_cell.coords[1], decimals) == round(self.neigh_cell.coords[1], decimals)
            # print(f"bottom_aligned: {bottom_aligned}")
            top_aligned = round(self.reference_cell.coords[3], decimals) == round(self.neigh_cell.coords[3], decimals)
            # print(f"top_aligned: {top_aligned}")
            if bottom_aligned and top_aligned:
                secondary_location = NA
            elif bottom_aligned:
                secondary_location = BOTTOM
            elif top_aligned:
                secondary_location = TOP
            else:
                raise ValueError("Could not locate with given arguments")
        elif primary_location in [TOP, BOTTOM]:
            left_aligned = round(self.reference_cell.coords[0], decimals) == round(self.neigh_cell.coords[0], decimals)
            # print(f"left_aligned: {left_aligned}")
            right_aligned = round(self.reference_cell.coords[2], decimals) == round(self.neigh_cell.coords[2], decimals)
            # print(f"right_aligned: {right_aligned}")
            if left_aligned and right_aligned:
                secondary_location = NA
            elif left_aligned:
                secondary_location = LEFT
            elif right_aligned:
                secondary_location = RIGHT
            else:
                raise ValueError("Could not locate with given arguments")
        else:
            raise ValueError("Could not locate with given arguments")
        return primary_location, secondary_location

    def transform(self, pos, from_array, to_array):
        """
        Transforms pixel position from one array to another

        :param from_array: 'reference', 'neigh', or 'merged'
        :param to_array: 'reference', 'neigh' or 'merged'
        """
        if from_array == REFERENCE and to_array == MERGED:
            return (
                pos[0] + self.reference_cell_shift[0],
                pos[1] + self.reference_cell_shift[1]
            )
        if from_array == MERGED and to_array == REFERENCE:
            return (
                pos[0] - self.reference_cell_shift[0],
                pos[1] - self.reference_cell_shift[1]
            )
        if from_array == NEIGH and to_array == MERGED:
            return (
                pos[0] + self.neigh_cell_shift[0],
                pos[1] + self.neigh_cell_shift[1]
             )
        if from_array == MERGED and to_array == NEIGH:
            return (
                pos[0] - self.neigh_cell_shift[0],
                pos[1] - self.neigh_cell_shift[1]
             )

    def clip(self, pos, clip_array):
        """ Clips pixel position to bounds of to_array"""
        bound_min_x, bound_min_y = 0, 0

        if clip_array == REFERENCE:
            array_shape = self.reference_cell.pixels.shape
        elif clip_array == NEIGH:
            array_shape = self.neigh_cell.pixels.shape
        elif clip_array == MERGED:
            array_shape = self.pixels.shape
        else:
            raise ValueError()

        bound_max_x = self.reference_cell.pixels.shape[0] - 1
        bound_max_y = self.reference_cell.pixels.shape[1] - 1

        return (
                   min(max(pos[0], bound_min_x), bound_max_x),
                   min(max(pos[1], bound_min_y), bound_max_y)
        )

    def indices(self, side: str):
        """Return the (merged pixels') indices of the top/left/bottom/right of the two cells in this pair"""
        reference_cell_indices = np.indices(self.reference_cell.pixels.shape)
        neigh_cell_indices = np.indices(self.neigh_cell.pixels.shape)
        if side == TOP:
            ref_side_idx = (0, reference_cell_indices[0, :, 0])  # (row, [axis, col, row])
            neigh_side_idx = (0, neigh_cell_indices[0, :, 0])
        elif side == BOTTOM:
            ref_side_idx = (self.reference_cell.height - 1, reference_cell_indices[0, :, 0])
            neigh_side_idx = (self.neigh_cell.height - 1, neigh_cell_indices[0, :, 0])
        elif side == LEFT:
            ref_side_idx = (reference_cell_indices[0, 0, :], 0)
            neigh_side_idx = (neigh_cell_indices[0, 0, :], 0)
        elif side == RIGHT:
            ref_side_idx = (reference_cell_indices[0, 0, :], self.reference_cell.width - 1)
            neigh_side_idx = (neigh_cell_indices[0, 0, :], self.neigh_cell.height - 1)
        else:
            raise ValueError("Invalid value for argument 'side'")

        ref_side_idx_in_merged = self.transform(ref_side_idx, from_array=REFERENCE, to_array=MERGED)
        neigh_side_idx_in_merged = self.transform(neigh_side_idx, from_array=NEIGH, to_array=MERGED)
        result = self.pixels.copy().astype(bool)
        result[::] = False
        result[ref_side_idx_in_merged] = True
        result[neigh_side_idx_in_merged] = True
        return result

    def connect_in_cell_pair(
            self,
            search_start_pos_in_reference_cell: tuple,
            target_side: str,
            search_forward: bool,
            search_precision: float
    ) -> List[ObstacleSegment]:
        """
        Try to get to the `target_side` in the neigh cell by connecting obstacle segments.
        First, it will be attempted to connect to relevant existing obstacle segments in neigh cell.
        If that fails, it will be attempted to reach the `target_side` by free search.

        Before using this method, make sure to identify the obstacle segments in each cell using cell.find_maxima() and
        cell.connect_maxima() first.

        :param search_forward: True if `search_start_pos_in_reference_cell` is the end point of an obstacle segment
        or False if it is the start point
        :returns: A list of obstacle segments that together connect the `search_start_pos_in_reference_cell` to the
        `target_side`
        """
        obstacle_segments = []
        search_start_pos_in_cell_pair = self.transform(
            search_start_pos_in_reference_cell,
            from_array=REFERENCE,
            to_array=MERGED
        )

        #################################################
        # CONNECT TO EXISTING OBSTACLE SEGMENT
        # First we try to connect to the start position of any obstacle segment that reaches
        # the opposite side in the neighbouring cell, saving the highest connection that was found
        # The code below takes into account the drawing direction of the obstacles
        # as defined in self.connect_maxima()
        ##################################################
        opposite_side_reached = False
        highest_so_far = -PSEUDO_INFINITE
        for neigh_obstacle_segment in self.neigh_cell.obstacle_segments:
            if neigh_obstacle_segment.ends_at(target_side):
                neigh_obstacle_segment_is_relevant = True
                search_end_pos_in_neigh_cell = neigh_obstacle_segment.from_pos
            elif neigh_obstacle_segment.starts_at(target_side):
                search_end_pos_in_neigh_cell = neigh_obstacle_segment.to_pos
                neigh_obstacle_segment_is_relevant = True
            else:
                neigh_obstacle_segment_is_relevant = False

            if neigh_obstacle_segment_is_relevant:
                search_end_pos_in_cell_pair = self.transform(
                    search_end_pos_in_neigh_cell,
                    from_array=NEIGH,
                    to_array=MERGED
                )

                tmp_new_obstacle_segment = ObstacleSegment.from_pixels(
                    pixels=self.pixels,
                    creation_method=CREATION_METHOD_NEIGH_SEARCH,
                    from_side=None,
                    from_pos=search_start_pos_in_cell_pair,
                    to_side=None,
                    to_positions=search_end_pos_in_cell_pair,
                    search_precision=search_precision
                )
                if tmp_new_obstacle_segment is not None:
                    if lowest([tmp_new_obstacle_segment, neigh_obstacle_segment]).height > highest_so_far:
                        highest_so_far = lowest([tmp_new_obstacle_segment, neigh_obstacle_segment]).height
                        tmp_new_obstacle_segment.parent = self.reference_cell
                        tmp_new_obstacle_segment.from_pos = search_start_pos_in_reference_cell
                        tmp_new_obstacle_segment.to_side = target_side
                        #  clip is used to keep the new obstacle segment within the boundaries of the cell
                        #  the obstacle segment geometry coordinates will be snapped to the cell boundary later on
                        #  so for that it does not matter if the end point is in the pixel at one or the other side of the
                        #  cell boundary
                        tmp_new_obstacle_segment.to_pos = self.clip(
                            self.transform(
                                search_end_pos_in_cell_pair,
                                from_array=MERGED,
                                to_array=REFERENCE
                            ),
                            clip_array=REFERENCE
                        )
                        new_obstacle_segment = tmp_new_obstacle_segment.clone()
                        new_obstacle_segment.calculate_coords()
                        if search_forward:
                            obstacle_segments = [new_obstacle_segment, neigh_obstacle_segment]
                        else:
                            new_obstacle_segment.reverse()
                            obstacle_segments = [neigh_obstacle_segment, new_obstacle_segment]
                        opposite_side_reached = True

        #################################################
        # CONNECT TO OPPOSITE SIDE 'FREE SEARCH'
        # Now we try to reach the opposite side of the neighbouring cell regardless of any pre-identified
        # obstacle_segments in that cell
        #################################################
        if not opposite_side_reached:
            new_obstacle_segment_to_side = target_side
            to_positions = self.indices(target_side)
            new_obstacle_segment = ObstacleSegment.from_pixels(
                pixels=self.pixels,
                creation_method=CREATION_METHOD_FREE_SEARCH,
                from_side=None,
                from_pos=search_start_pos_in_cell_pair,
                to_side=new_obstacle_segment_to_side,
                to_positions=to_positions,
                search_precision=search_precision
            )
            if new_obstacle_segment is not None:
                # check if new obstacle ends in neighbouring cell or in this cell
                new_obstacle_segment_to_pos_in_reference_cell = self.transform(
                    new_obstacle_segment.to_pos,
                    from_array=MERGED,
                    to_array=REFERENCE
                )
                to_pos_is_in_neigh_cell = new_obstacle_segment_to_pos_in_reference_cell != self.clip(
                    new_obstacle_segment_to_pos_in_reference_cell,
                    clip_array=REFERENCE
                )
                if to_pos_is_in_neigh_cell:
                    new_obstacle_segment.parent = self.neigh_cell
                    new_obstacle_segment.from_pos = self.clip(
                        self.transform(new_obstacle_segment.from_pos, from_array=MERGED, to_array=NEIGH),
                        clip_array=NEIGH
                    )
                    new_obstacle_segment.to_pos = self.clip(
                        self.transform(new_obstacle_segment.to_pos, from_array=MERGED, to_array=NEIGH),
                        clip_array=NEIGH
                    )
                    new_obstacle_segment.edges = [self.edge]
                else:  # to_pos is in this cell
                    new_obstacle_segment.parent = self.reference_cell
                    new_obstacle_segment.from_pos = search_start_pos_in_reference_cell

                    # translate the pixel positions from the merged pixels to the parent cell pixels
                    new_obstacle_segment.to_pos = self.transform(
                        new_obstacle_segment.to_pos,
                        from_array=MERGED,
                        to_array=REFERENCE
                    )

                new_obstacle_segment.calculate_coords()
                if not search_forward:
                    new_obstacle_segment.reverse()
                obstacle_segments = [new_obstacle_segment]
        return obstacle_segments


def highest(elements: List[Union[ObstacleSegment, Obstacle, Edge]]):
    """Return the highest element from a list of obstacles, obstacle segments, or edges.

    For Obstacle lists, obstacles with fewer segments will be preferred over
    obstacles of equal height with more segments
    """
    max_element_height = -PSEUDO_INFINITE
    highest_element = None
    for element in elements:
        attr_name = 'threedi_exchange_level' if isinstance(element, Edge) else 'height'
        if getattr(element, attr_name) >= max_element_height:
            if isinstance(element, Obstacle):
                if element.height == max_element_height and len(element.segments) > len(highest_element.segments):
                    continue
            max_element_height = getattr(element, attr_name)
            highest_element = element
    return highest_element


def lowest(elements: List[Union[ObstacleSegment, Obstacle, Edge]]):
    """Return the lowest element from a list of obstacles, obstacle segments, or edges.

    For Obstacle lists, obstacles with fewer segments will be preferred over
    obstacles of equal height with more segments
    """
    min_element_height = PSEUDO_INFINITE
    lowest_element = None
    for element in elements:
        attr_name = 'threedi_exchange_level' if isinstance(element, Edge) else 'height'
        if getattr(element, attr_name) <= min_element_height:
            if isinstance(element, Obstacle):
                if element.height == min_element_height and len(element.segments) > len(lowest_element.segments):
                    continue
            min_element_height = getattr(element, attr_name)
            lowest_element = element
    return lowest_element


def shared_obstacles(edges: List[Edge]):
    """Return the obstacles that apply to all `edges`"""
    obstacles = []
    result = []
    for edge in edges:
        obstacles += edge.obstacles
    for obstacle in obstacles:
        shared = True
        for edge in edges:
            if edge not in obstacle.edges:
               shared = False
        if shared:
            result.append(obstacle)
    return result


def intersection(line_coords1, line_coords2, decimals: int = 5):
    (start_x1, start_y1), (end_x1, end_y1) = np.round(line_coords1, decimals)
    (start_x2, start_y2), (end_x2, end_y2) = np.round(line_coords2, decimals)
    if start_x1 == end_x1 == start_x2 == end_x2 == start_x1:
        x = start_x1
        if (start_y1 >= start_y2 and end_y1 <= end_y2) or (start_y2 >= start_y1 and end_y2 <= end_y1):
            return (x, max(start_y1, start_y2)), (x, min(end_y1, end_y2))
    elif start_y1 == end_y1 == start_y2 == end_y2:
        y = start_y1
        if (start_x1 >= start_x2 and end_x1 <= end_x2) or (start_x2 >= start_x1 and end_x2 <= end_x1):
            return (max(start_x1, start_x2), y), (min(end_x1, end_x2), y)
    return None


def edge_coordinates(cell1, cell2):
    """Return tuple of (edge coordinates, neigh_r, neigh_l) or (None, None, None) if cells don't share an edge"""
    side_coords1 = cell1.side_coords()
    side_coords2 = cell2.side_coords()
    for side1 in [TOP, BOTTOM, LEFT, RIGHT]:
        for side2 in [TOP, BOTTOM, LEFT, RIGHT]:
            intersection_coords = intersection(side_coords1[side1], side_coords2[side2])
            if intersection_coords:
                if (side1 == TOP and side2 == BOTTOM) or (side1 == LEFT and side2 == RIGHT):
                    return intersection, cell1, cell2
                elif (side1 == BOTTOM and side2 == TOP) or (side1 == RIGHT and side2 == LEFT):
                    return intersection, cell2, cell1
    return None, None, None


def identify_obstacles(dem: gdal.Dataset,
                       gr: GridH5Admin,
                       cell_ids: List,
                       min_peak_prominence: float,
                       search_precision: float,
                       min_obstacle_height: float,
                       output_fn: str,
                       driver_name='Memory'
                       ):
    print('constructing topology...')
    topo = Topology(gr=gr, cell_ids=cell_ids, dem=dem)

    # find obstacle segments within cell
    for nr, cell_i in enumerate(topo.cells.values()):
        print(f'find obstacles within cell {cell_i.id} ({nr} of {len(topo.cells)})')
        try:
            cell_i.find_maxima(min_peak_prominence=min_peak_prominence)
            cell_i.connect_maxima(search_precision=search_precision, min_obstacle_height=min_obstacle_height)
        except (KeyError, ValueError):
            # KeyError in case user requests ids that do not exist, e.g. by using list(gr.cells.id)
            # ValueError - I think this has to do with cases where cell is partly outside raster extent?
            continue

    # Create obstacles from segments
    for cell_i in topo.cells.values():
        print(f'Create obstacles from segments for cell {cell_i.id} of {len(topo.cells)}')
        cell_i.create_obstacles_from_segments(
            direct_connection_preference=min_obstacle_height,
            search_precision=search_precision,
            min_obstacle_height=min_obstacle_height
        )

    # filter obstacles
    for nr, (edge_key, edge) in enumerate(topo.edges.items()):
        print(f'filter obstacles for edge {nr} of {len(topo.edges)}')
        edge.filter_obstacles(min_obstacle_height=min_obstacle_height, search_precision=search_precision)

    # generate connecting obstacles
    for nr, (edge_key, edge) in enumerate(topo.edges.items()):
        print(f'generate_connecting_obstacle for edge {nr} of {len(topo.edges)}')
        edge.generate_connecting_obstacle(min_obstacle_height=min_obstacle_height, search_precision=search_precision)

    # collect unique obstacle segments
    topo.select_final_obstacle_segments()

    # export result to geopackage
    drv = ogr.GetDriverByName(driver_name)
    ds = drv.CreateDataSource(output_fn)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(int(gr.epsg_code))

    ####
    # Export all obstacle segments
    ####
    lyr = ds.CreateLayer('obstacle_segments', srs, geom_type=ogr.wkbLineString, options=['FID=id'])

    # add fields
    field_defn_id = ogr.FieldDefn('id', ogr.OFTInteger)
    field_defn_crest_level = ogr.FieldDefn('crest_level', ogr.OFTReal)

    lyr.CreateField(field_defn_id)
    lyr.CreateField(field_defn_crest_level)

    lyr.StartTransaction()
    id_counter = 1
    for cell in topo.cells.values():
        for segment in cell.obstacle_segments:
            feat = ogr.Feature(lyr.GetLayerDefn())
            feat['id'] = id_counter
            feat['crest_level'] = segment.height
            feat.SetGeometry(segment.geometry())
            lyr.CreateFeature(feat)
            id_counter += 1
    lyr.CommitTransaction()

    ####
    # Export final obstacle segments
    ####
    lyr = ds.CreateLayer('final_obstacle_segments', srs, geom_type=ogr.wkbLineString, options=['FID=id'])

    # add fields
    field_defn_id = ogr.FieldDefn('id', ogr.OFTInteger)
    field_defn_crest_level = ogr.FieldDefn('crest_level', ogr.OFTReal)

    lyr.CreateField(field_defn_id)
    lyr.CreateField(field_defn_crest_level)

    lyr.StartTransaction()
    id_counter = 1
    for segment in topo.final_obstacle_segments.values():
        print(segment)
        feat = ogr.Feature(lyr.GetLayerDefn())
        feat['id'] = id_counter
        feat['crest_level'] = segment.height
        feat.SetGeometry(segment.geometry())
        lyr.CreateFeature(feat)
        id_counter += 1
    lyr.CommitTransaction()

    ####
    # Export edges that have obstacles
    ####
    lyr = ds.CreateLayer('edge_with_obstacle', srs, geom_type=ogr.wkbLineString, options=['FID=id'])

    # add fields
    field_defn_id = ogr.FieldDefn('id', ogr.OFTInteger)
    field_defn_3di = ogr.FieldDefn('exchange_level_3di', ogr.OFTReal)
    field_defn_crest_level = ogr.FieldDefn('crest_level', ogr.OFTReal)

    lyr.CreateField(field_defn_id)
    lyr.CreateField(field_defn_3di)
    lyr.CreateField(field_defn_crest_level)

    lyr.StartTransaction()
    id_counter = 1
    for edge in topo.edges.values():
        obstacle = edge.highest_obstacle
        if obstacle is not None:
            feat = ogr.Feature(lyr.GetLayerDefn())
            feat['id'] = id_counter
            feat['crest_level'] = obstacle.height
            feat['exchange_level_3di'] = edge.threedi_exchange_level
            feat.SetGeometry(edge.geometry())
            lyr.CreateFeature(feat)
            id_counter += 1
    lyr.CommitTransaction()

    return ds
