# TODO: alles van v1 verwijderen
# TODO: op de jusite manier rekening houden met nodata in raster
# TODO: aansluiten op QGIS plugin
# TODO: add support for cell that extend beyond dem (fill with nodata?)
# TODO: support for grid refinement
# TODO: support for nodata obstacles (e.g. pand)
# TODO: casussen als amstelstation cell 3138


from typing import List, Tuple, Union

from threedigrid.admin.gridadmin import GridH5Admin
from threedigrid.admin.lines.models import Lines
import numpy as np
from osgeo import gdal, ogr, osr
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
SIDE_INDEX = {
    TOP: np.index_exp[0, :],
    RIGHT: np.index_exp[:, -1],
    BOTTOM: np.index_exp[-1, :],
    LEFT: np.index_exp[:, 0]
}
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


def read_as_array(raster: gdal.Dataset, bbox: Union[List, Tuple], band_nr: int = 1, pad: bool = False) -> np.ndarray:
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
    x0, y0 = gdal.ApplyGeoTransform(inv_gt, float(bbox[0]), float(bbox[1]))
    x1, y1 = gdal.ApplyGeoTransform(inv_gt, float(bbox[2]), float(bbox[3]))
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
    """Edge of cell, may be shared between two cells.

    Drawing direction is always left -> right or bottom -> top.

    Therefore for a left -> right edge, the neigh_l is up and the neigh_r is down
    """

    def __init__(self,
                 parent,  # Topology
                 start_coord: tuple,
                 end_coord: tuple,
                 neigh_r=None,
                 neigh_l=None,
                 ):
        if not (
                (start_coord[0] == end_coord[0] and start_coord[1] < end_coord[1])
                or
                (start_coord[1] == end_coord[1] and start_coord[0] < end_coord[0])
        ):
            raise ValueError('Invalid coordinates for edge')
        self.parent = parent
        self.start_coord = start_coord
        self.end_coord = end_coord
        self.neigh_r = neigh_r
        self.neigh_l = neigh_l
        self.obstacles = list()

        # calculate exchange levels: 1D array of max of pixel pairs along the edge
        pxsize = self.parent.dem.GetGeoTransform()[1]

        if self.is_bottom_up():
            bbox = [self.start_coord[0] - pxsize, self.start_coord[1], self.end_coord[0] + pxsize, self.end_coord[1]]
        else:
            bbox = [self.start_coord[0], self.start_coord[1] - pxsize, self.end_coord[0], self.end_coord[1] + pxsize]
        try:
            arr = read_as_array(raster=self.parent.dem, bbox=bbox)
            self.exchange_levels = np.nanmax(arr, axis=int(self.is_bottom_up()))
            self.threedi_exchange_level = np.nanmin(self.exchange_levels)
        except ValueError:  # cell is at model boundary and therefore edge is out of dem extent
            self.exchange_levels = None
            self.threedi_exchange_level = None

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
            return
        if self.is_bottom_up():
            side_pairs = [(TOP, BOTTOM), (BOTTOM, TOP)]
        else:
            side_pairs = [(LEFT, RIGHT), (RIGHT, LEFT)]
        for side_1, side_2 in side_pairs:
            neigh_edge_1 = self.neigh_l.edge(side_1)
            neigh_edge_2 = self.neigh_r.edge(side_2)
            if neigh_edge_1 is not None and neigh_edge_2 is not None:
                if neigh_edge_1.highest_obstacle is not None and neigh_edge_2.highest_obstacle is not None:
                    cell_pair = CellPair(reference_cell=self.neigh_l, neigh_cell=self.neigh_r)
                    search_start_pos_in_cell_pair = None
                    search_end_pos_in_cell_pair = None
                    if self in neigh_edge_1.highest_obstacle.start_edges():
                        search_start_pos = neigh_edge_1.highest_obstacle.segments[0].from_pos
                        search_start_pos_in_cell_pair = cell_pair.transform(
                            pos=search_start_pos,
                            from_array=REFERENCE,
                            to_array=MERGED
                        )
                    if self in neigh_edge_1.highest_obstacle.end_edges():
                        search_start_pos = neigh_edge_1.highest_obstacle.segments[-1].to_pos
                        search_start_pos_in_cell_pair = cell_pair.transform(
                            pos=search_start_pos,
                            from_array=REFERENCE,
                            to_array=MERGED
                        )
                    if self in neigh_edge_2.highest_obstacle.start_edges():
                        search_end_pos = neigh_edge_2.highest_obstacle.segments[0].from_pos
                        search_end_pos_in_cell_pair = cell_pair.transform(
                            pos=search_end_pos,
                            from_array=NEIGH,
                            to_array=MERGED
                        )
                    if self in neigh_edge_2.highest_obstacle.end_edges():
                        search_end_pos = neigh_edge_1.highest_obstacle.segments[-1].to_pos
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
                            if connecting_obstacle_segment.height > self.threedi_exchange_level + min_obstacle_height - search_precision:
                                obstacle = Obstacle(segments=[connecting_obstacle_segment], edge=self)
                                self.obstacles.append(obstacle)
                                self.parent.obstacles.append(obstacle)
                                return

    def filter_obstacles(self, min_obstacle_height: float, search_precision: float):
        """Filter obstacles of this edge based on several criteria. Updates self.obstacles"""
        filtered_obstacles = list()
        for obstacle in self.obstacles:
            select_this_obstacle = True

            # keep Obstacles based on 'free search' connection to other side only if
            # both neighbouring exchange levels are significantly higher then the obstacle crest level
            obstacle_has_free_search_segment = False
            for segment in obstacle.segments:
                if segment.creation_method == CREATION_METHOD_FREE_SEARCH:
                    obstacle_has_free_search_segment = True

            if obstacle_has_free_search_segment:
                if self.is_bottom_up():
                    opposite_edge_left = self.neigh_l.edge(LEFT)
                    opposite_edge_right = self.neigh_r.edge(RIGHT)
                else:
                    opposite_edge_left = self.neigh_l.edge(TOP)
                    opposite_edge_right = self.neigh_r.edge(BOTTOM)
                if obstacle.height < opposite_edge_left.threedi_exchange_level + min_obstacle_height - search_precision \
                        or obstacle.height < opposite_edge_right.threedi_exchange_level + min_obstacle_height - search_precision:
                    select_this_obstacle = False

            if select_this_obstacle:
                filtered_obstacles.append(obstacle)
        self.obstacles = filtered_obstacles

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
        node_ids = flowlines.line_nodes

        # get cell coordinates
        threedigrid_cells = gr.cells.filter(id__in=node_ids.flatten())
        cell_properties = threedigrid_cells.only('id', 'cell_coords').data
        self.cell_coords = dict(zip(cell_properties['id'], cell_properties['cell_coords'].T))

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
            next_cell_ids = node_ids[np.where(node_ids[:, 0] == cell.id), 1].flatten()
            for next_cell_id in next_cell_ids:
                cell2_xmin = np.min(self.cells[next_cell_id].coords[[0, 2]])
                if cell1_xmax == cell2_xmin:  # aligned horizontally if True
                    cell_topology[RIGHT].append(self.cells[next_cell_id])
                else:
                    cell_topology[TOP].append(self.cells[next_cell_id])

            # previous_cells: cells down / to the left
            previous_cell_ids = node_ids[np.where(node_ids[:, 1] == cell.id), 0].flatten()
            for previous_cell_id in previous_cell_ids:
                cell2_xmax = np.max(self.cells[previous_cell_id].coords[[0, 2]])
                if cell1_xmin == cell2_xmax:  # aligned horizontally if True
                    cell_topology[LEFT].append(self.cells[previous_cell_id])
                else:
                    cell_topology[BOTTOM].append(self.cells[previous_cell_id])
            self.cell_topologies[cell.id] = cell_topology

        # edges
        self.edges = dict()
        for cell in self.cells.values():
            # all edges' drawing directions are bottom -> top or left -> right
            # TODO support grid refinement
            xmin, ymin, xmax, ymax = cell.coords

            bl = (xmin, ymin)
            br = (xmax, ymin)
            tl = (xmin, ymax)
            tr = (xmax, ymax)

            # bottom left -> top left
            try:
                self.edges[(bl, tl)].neigh_r = cell
            except KeyError:
                self.edges[(bl, tl)] = Edge(parent=self, start_coord=bl, end_coord=tl, neigh_r=cell)
            cell.edges[LEFT] = self.edges[(bl, tl)]

            # bottom right -> top right
            try:
                self.edges[(br, tr)].neigh_l = cell
            except KeyError:
                self.edges[(br, tr)] = Edge(parent=self, start_coord=br, end_coord=tr, neigh_l=cell)
            cell.edges[RIGHT] = self.edges[(br, tr)]

            # top left -> top right
            try:
                self.edges[(tl, tr)].neigh_r = cell
            except KeyError:
                self.edges[(tl, tr)] = Edge(parent=self, start_coord=tl, end_coord=tr, neigh_r=cell)
            cell.edges[TOP] = self.edges[(tl, tr)]

            # bottom left -> bottom right
            try:
                self.edges[(bl, br)].neigh_l = cell
            except KeyError:
                self.edges[(bl, br)] = Edge(parent=self, start_coord=bl, end_coord=br, neigh_l=cell)
            cell.edges[BOTTOM] = self.edges[(bl, br)]

    def neigh_cells(self, cell_id: int, location: str):
        return self.cell_topologies[cell_id][location]

    def select_final_obstacle_segments(self):
        for edge in self.edges.values():
            if edge.highest_obstacle is not None:
                for segment in edge.highest_obstacle.segments:
                    segment_to_add = segment.clone()
                    segment_to_add.height = edge.highest_obstacle.height
                    segment_to_add.edge = edge
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
        self._edge = None

    def __str__(self):
        return str(self.__dict__)

    @staticmethod
    def from_pixels(
            pixels,
            creation_method: int,
            from_side,  # TODO: determine from_side and to_side from from_pos and to_pos
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
        to_pixels[mask == False] = -9999
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
    def edge(self):
        """
        Return the edge that the obstacle segment belongs to. Valid only for left/right or top/bottom obstacle segments.
        Returns None for diagonal obstacle segments
        """
        if self._edge is None:
            cell_height, cell_width = self.parent.pixels.shape
            labelled_pixels, labelled_pixels_nr_features = label(
                self.parent.pixels >= self.height - self.search_precision,
                structure=SEARCH_STRUCTURE
            )
            try:
                obstacle_pixels = labelled_pixels == labelled_pixels[self.from_pos]
            except:
                print(f'Something went wrong with an obstacle segment in cell {self.parent.id}')
                raise
            nr_obstacle_pixels_left = np.nansum(obstacle_pixels[:, 0:int(cell_width / 2)] == 1)
            nr_obstacle_pixels_right = np.nansum(obstacle_pixels[:, int(cell_width / 2):] == 1)
            nr_obstacle_pixels_top = np.nansum(obstacle_pixels[0:int(cell_height / 2), :] == 1)
            nr_obstacle_pixels_bottom = np.nansum(obstacle_pixels[int(cell_height / 2):, :] == 1)

            if (self.starts_at(TOP) and self.ends_at(BOTTOM)) or (self.starts_at(BOTTOM) and self.ends_at(TOP)):
                if nr_obstacle_pixels_left > nr_obstacle_pixels_right:
                    self._edge = self.parent.edge(LEFT)
                else:
                    self._edge = self.parent.edge(RIGHT)
            elif (self.starts_at(LEFT) and self.ends_at(RIGHT)) or (self.starts_at(RIGHT) and self.ends_at(LEFT)):
                if nr_obstacle_pixels_top > nr_obstacle_pixels_bottom:
                    self._edge = self.parent.edge(TOP)
                else:
                    self._edge = self.parent.edge(BOTTOM)
            else:
                self._edge = None

        return self._edge

    @edge.setter
    def edge(self, edge: Edge):
        self._edge = edge

    def is_valid(self, min_obstacle_height: float):
        # stricter filtering for diagonal obstacles
        if ((self.starts_at(TOP) and self.ends_at(BOTTOM)) or
                (self.starts_at(BOTTOM) and self.ends_at(TOP)) or
                (self.starts_at(LEFT) and self.ends_at(RIGHT)) or
                (self.starts_at(RIGHT) and self.ends_at(LEFT))
        ):
            return True
        # stricter filtering for diagonal obstacles:
        # obstacle must be significantly higher than *highest* exchange height of the obstacle-side edges
        # and significantly higher than the *lowest* exchange height on the opposite side edges
        elif self.height > max(
                self.parent.edge(self.from_side).threedi_exchange_level,
                self.parent.edge(self.to_side).threedi_exchange_level
            ) + min_obstacle_height and \
            self.height > min(
                self.parent.edge(OPPOSITE[self.from_side]).threedi_exchange_level,
                self.parent.edge(OPPOSITE[self.to_side]).threedi_exchange_level
            ) + min_obstacle_height:
            return True
        else:
            return False

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
                result.append(self.parent.edge(side))
        return result

    def end_edges(self):
        result = []
        for side in [TOP, RIGHT, BOTTOM, LEFT]:
            if self.ends_at(side):
                result.append(self.parent.edge(side))
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
        result.edge = self.edge
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
    """Group of one or more ObstacleSegments that cross a cell / two neighb. cells from bottom to top or left to right"""

    def __init__(self, segments: List[ObstacleSegment], edge: Edge):
        self.segments = segments
        self.edge = edge

    def start_edges(self) -> [Edge]:
        """
        Returns the edge or edges at which this obstacle starts
        """
        return self.segments[0].start_edges()

    def end_edges(self) -> [Edge]:
        """
        Returns the edge or edges at which this obstacle ends
        """
        return self.segments[0].end_edges()

    @property
    def height(self):
        min_height = 9999
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
        self.pixels = read_as_array(raster=parent.dem, bbox=coords)
        self.obstacle_segments = list()
        self.maxima = None
        self.edges = dict()

    def __str__(self):
        return str(self.__dict__)

    def pixels_from_dem(self, dem):
        self.pixels = read_as_array(raster=dem, bbox=self.coords)

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

    def edge(self, side: str) -> Edge:
        """Return the cell border as a linestring

        :param cell_coords: [xmin, ymin, xmax, ymax]
        :param side: TOP | BOTTOM | LEFT | RIGHT
        """
        xmin, ymin, xmax, ymax = self.coords
        side_dict = {
            TOP: ((xmin, ymax), (xmax, ymax)),
            BOTTOM: ((xmin, ymin), (xmax, ymin)),
            LEFT: ((xmin, ymin), (xmin, ymax)),
            RIGHT: ((xmax, ymin), (xmax, ymax)),
        }

        if side in [TOP, BOTTOM, LEFT, RIGHT]:
            try:
                return self.edges[side]
            except KeyError:
                self.edges[side] = self.parent.edges[side_dict[side]]
                return self.edges[side]
        else:
            raise ValueError(f"'side' must be one of {TOP} | {BOTTOM} | {LEFT} | {RIGHT}")

    def side_of_edge(self, edge):
        for side in [TOP, BOTTOM, LEFT, RIGHT]:
            cell_edge = self.edge(side)
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
            if self.edge(fro).exchange_levels is None or self.edge(to).exchange_levels is None:
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
        obstacles = list()
        if search_forward:
            search_start_side = obstacle_segment_to_side
            search_start_pos = obstacle_segment.to_pos
            obstacle_segment_begin_side = obstacle_segment_from_side
        else:
            search_start_side = obstacle_segment_from_side
            search_start_pos = obstacle_segment.from_pos
            obstacle_segment_begin_side = obstacle_segment_to_side
        edge = self.edge(search_start_side)
        neigh_cells = self.parent.neigh_cells(self.id, search_start_side)
        if len(neigh_cells) > 0:
            neigh_cell = neigh_cells[0]  # TODO add support for grid refinement
            cell_pair = CellPair(reference_cell=self, neigh_cell=neigh_cell)
            additional_obstacle_segments = cell_pair.connect_in_cell_pair(
                search_start_pos_in_reference_cell=search_start_pos,
                target_side=OPPOSITE[obstacle_segment_begin_side],
                search_forward=search_forward,
                search_precision=search_precision
            )
            if len(additional_obstacle_segments) > 0:  # i.e. other side has been reached
                if search_forward:
                    obstacle_segments = [obstacle_segment] + additional_obstacle_segments
                else:
                    obstacle_segments = additional_obstacle_segments + [obstacle_segment]
                obstacles.append(Obstacle(segments=obstacle_segments, edge=edge))
        return obstacles


    def connect_to_opposite_side_OLD(
            self,
            obstacle_segment: ObstacleSegment,
            direct_connection_preference: float,
            obstacle_segment_from_side: str,
            obstacle_segment_to_side: str,
            search_forward: bool, search_precision: float,
            min_obstacle_height: float
    ) -> List[Obstacle]:
        # TODO: uit elkaar trekken in verschillende functies
        obstacles = list()
        if search_forward:
            search_start_side = obstacle_segment_to_side
            search_start_pos = obstacle_segment.to_pos
            obstacle_segment_begin_side = obstacle_segment_from_side
        else:
            search_start_side = obstacle_segment_from_side
            search_start_pos = obstacle_segment.from_pos
            obstacle_segment_begin_side = obstacle_segment_to_side
        edge = self.edge(search_start_side)
        neigh_cells = self.parent.neigh_cells(self.id, search_start_side)
        if len(neigh_cells) > 0:
            neigh_cell = neigh_cells[0]  # TODO add support for grid refinement
            if search_start_side == TOP:
                merged_pixels = np.vstack([neigh_cell.pixels, self.pixels])
                this_cell_shift = (neigh_cell.pixels.shape[0], 0)  # {pos in this cell} + this_cell_shift = {pos in merged pixels}
                neigh_cell_shift = (0, 0)  # {pos in neigh. cell} + neigh_cell_shift = {pos in merged pixels}
            elif search_start_side == RIGHT:
                merged_pixels = np.hstack([self.pixels, neigh_cell.pixels])
                this_cell_shift = (0, 0)
                neigh_cell_shift = (0, self.pixels.shape[1])
            elif search_start_side == BOTTOM:
                merged_pixels = np.vstack([self.pixels, neigh_cell.pixels])
                this_cell_shift = (0, 0)
                neigh_cell_shift = (self.pixels.shape[0], 0)
            elif search_start_side == LEFT:
                merged_pixels = np.hstack([neigh_cell.pixels, self.pixels])
                this_cell_shift = (0, neigh_cell.pixels.shape[1])
                neigh_cell_shift = (0, 0)

            search_start_pos_in_merged_pixels = (
                search_start_pos[0] + this_cell_shift[0],
                search_start_pos[1] + this_cell_shift[1]
            )

            #################################################
            # CONNECT TO EXISTING OBSTACLE SEGMENT
            # First we try to connect to the start position of any obstacle segment that reaches
            # the opposite side in the neighbouring cell.
            # The code below takes into account the drawing direction of the obstacles
            # as defined in self.connect_maxima()
            ##################################################
            opposite_side_reached = False
            for neigh_obstacle_segment in neigh_cell.obstacle_segments:
                if search_forward:
                    neigh_obstacle_segment_is_relevant = neigh_obstacle_segment.ends_at(
                        OPPOSITE[obstacle_segment_begin_side])
                    search_end_pos = neigh_obstacle_segment.from_pos
                else:
                    neigh_obstacle_segment_is_relevant = neigh_obstacle_segment.starts_at(
                        OPPOSITE[obstacle_segment_begin_side])
                    search_end_pos = neigh_obstacle_segment.to_pos
                if neigh_obstacle_segment_is_relevant:
                    search_end_pos_in_merged_pixels = \
                        (search_end_pos[0] + neigh_cell_shift[0],
                         search_end_pos[1] + neigh_cell_shift[1]
                         )
                    new_obstacle_segment = ObstacleSegment.from_pixels(
                        pixels=merged_pixels,
                        from_side=None,
                        from_pos=search_start_pos_in_merged_pixels,
                        to_side=None,
                        to_positions=search_end_pos_in_merged_pixels,
                        search_precision=search_precision
                    )
                    if new_obstacle_segment is not None:
                        new_obstacle_segment_to_pos = (
                            min(max(
                                search_end_pos_in_merged_pixels[0] - this_cell_shift[0],
                                0), self.pixels.shape[0] - 1),
                            min(max(
                                search_end_pos_in_merged_pixels[1] - this_cell_shift[1],
                                0), self.pixels.shape[1] - 1)
                        )
                        #  min and max are used to keep the new obstacle segment within the boundaries of the cell
                        #  the obstacle segment geometry coordinates will be snapped to the cell boundary later on
                        #  so for that it does not matter if the end point is in the pixel at one or the other side of the cell boundary
                        if search_forward:
                            # search_end_side = neigh_obstacle_segment.from_side
                            search_end_side = OPPOSITE[obstacle_segment_to_side]
                        else:
                            search_end_side = OPPOSITE[obstacle_segment_from_side]
                        new_obstacle_segment.parent = self
                        new_obstacle_segment.from_side = search_start_side
                        new_obstacle_segment.to_side = search_end_side
                        new_obstacle_segment.from_pos = search_start_pos
                        new_obstacle_segment.to_pos = new_obstacle_segment_to_pos
                        new_obstacle_segment.calculate_coords()
                        if search_forward:
                            obstacle_segments = [obstacle_segment, new_obstacle_segment, neigh_obstacle_segment]
                        else:
                            new_obstacle_segment.reverse()
                            obstacle_segments = [neigh_obstacle_segment, new_obstacle_segment, obstacle_segment]
                        obstacle = Obstacle(obstacle_segments, edge)
                        obstacles.append(obstacle)
                        opposite_side_reached = True

            #################################################
            # CONNECT TO OPPOSITE SIDE
            # Now we try to reach the opposite side of the neighbouring cell regardless of any pre-identified
            # obstacle_segments in that cell
            #################################################
            if not opposite_side_reached:
                new_obstacle_segment_to_side = OPPOSITE[obstacle_segment_begin_side]
                to_positions = SIDE_INDEX[new_obstacle_segment_to_side]
                new_obstacle_segment = ObstacleSegment.from_pixels(
                    pixels=merged_pixels,
                    from_side=None,
                    from_pos=search_start_pos_in_merged_pixels,
                    to_side=new_obstacle_segment_to_side,
                    to_positions=to_positions,
                    search_precision=search_precision
                )
                if new_obstacle_segment is not None:
                    # check if new obstacle ends in neighbouring cell or in this cell
                    to_pos_is_in_neigh_cell = (
                            (search_start_side == TOP
                             and new_obstacle_segment.to_pos[0] < neigh_cell.pixels.shape[0]
                             ) or
                            (search_start_side == RIGHT
                             and new_obstacle_segment.to_pos[1] >= self.pixels.shape[1]
                             ) or
                            (search_start_side == BOTTOM
                             and new_obstacle_segment.to_pos[0] >= self.pixels.shape[0]
                             ) or
                            (search_start_side == LEFT
                             and new_obstacle_segment.to_pos[1] < neigh_cell.pixels.shape[1]
                             )
                    )
                    if to_pos_is_in_neigh_cell:
                        new_obstacle_segment.parent = neigh_cell
                        new_obstacle_segment.from_side = OPPOSITE[search_start_side]
                        # translate the pixel positions from the merged pixels to the parent cell pixels
                        if search_start_side == TOP:
                            from_pos_additional_shift = (1, 0)
                        elif search_start_side == RIGHT:
                            from_pos_additional_shift = (0, -1)
                        elif search_start_side == BOTTOM:
                            from_pos_additional_shift = (-1, 0)
                        elif search_start_side == LEFT:
                            from_pos_additional_shift = (0, 1)
                        from_pos_shift = np.add(neigh_cell_shift, from_pos_additional_shift)
                        new_obstacle_segment.from_pos = tuple(
                            np.subtract(new_obstacle_segment.from_pos, from_pos_shift))
                        new_obstacle_segment.to_pos = tuple(np.subtract(new_obstacle_segment.to_pos, neigh_cell_shift))
                    else:  # to_pos is in this cell
                        new_obstacle_segment.parent = self
                        new_obstacle_segment.from_pos = search_start_pos
                        new_obstacle_segment.from_side = search_start_side

                        # translate the pixel positions from the merged pixels to the parent cell pixels
                        new_obstacle_segment.to_pos = tuple(np.subtract(new_obstacle_segment.to_pos, this_cell_shift))

                        # do not make obstacle for this obstacle_segment if the resulting obstacle
                        # connects left -> right or top -> bottom
                        # while there already is an obstacle_segment in this cell that makes this connection at
                        # (almost) the same height
                        existing_obstacles = self.filtered_obstacle_segments(
                            from_side=new_obstacle_segment.from_side,
                            to_side=OPPOSITE[obstacle_segment_begin_side]
                        )
                        existing_obstacles += self.filtered_obstacle_segments(
                            from_side=OPPOSITE[obstacle_segment_begin_side],
                            to_side=new_obstacle_segment.from_side
                        )
                        highest_obstacle_segment = highest(existing_obstacles)
                        if highest_obstacle_segment is not None:
                            if obstacle_segment.height - direct_connection_preference - search_precision < \
                                    highest_obstacle_segment.height:
                                return obstacles  # empty list
                            # create mock obstacle segment to determine the edge to which the Obstacle should be linked
                            else:
                                if search_forward:
                                    mock_obstacle_from_pos = obstacle_segment.from_pos
                                    mock_obstacle_to_pos = new_obstacle_segment.to_pos
                                else:
                                    mock_obstacle_from_pos = new_obstacle_segment.to_pos
                                    mock_obstacle_to_pos = obstacle_segment.to_pos
                                mock_obstacle_segment = ObstacleSegment(
                                    parent=obstacle_segment.parent,
                                    creation_method=CREATION_METHOD_MOCK,
                                    from_side=None,
                                    from_pos=mock_obstacle_from_pos,
                                    to_side=None,
                                    to_pos=mock_obstacle_to_pos,
                                    height=np.min([obstacle_segment.height, new_obstacle_segment.height]),
                                    search_precision=search_precision
                                )
                                edge = mock_obstacle_segment.edge

                        # if no such direct connection exists, create obstacle from the current obstacle segment
                        # and the new obstacle segment
                        if search_start_side == TOP:
                            new_obstacle_segment.to_pos = (
                                new_obstacle_segment.to_pos[0] - neigh_cell.pixels.shape[0],
                                new_obstacle_segment.to_pos[1])
                        elif search_start_side == LEFT:
                            new_obstacle_segment.to_pos = (new_obstacle_segment.to_pos[0],
                                                           new_obstacle_segment.to_pos[1] -
                                                           neigh_cell.pixels.shape[1])

                    new_obstacle_segment.calculate_coords()
                    if search_forward:
                        obstacle_segments = [obstacle_segment, new_obstacle_segment]
                    else:
                        new_obstacle_segment.reverse()
                        obstacle_segments = [new_obstacle_segment, obstacle_segment]
                    obstacle = Obstacle(obstacle_segments, edge)
                    # keep Obstacles based on 'free search' connection to other side only if
                    # both neighbouring exchange levels are significantly higher then the obstacle crest level
                    if to_pos_is_in_neigh_cell:
                        opposite_edge_in_this_cell = self.edge(OPPOSITE[self.side_of_edge(edge)])
                        opposite_edge_in_neigh_cell = neigh_cell.edge(OPPOSITE[neigh_cell.side_of_edge(edge)])
                        if obstacle.height < opposite_edge_in_this_cell.threedi_exchange_level + min_obstacle_height - search_precision \
                                or obstacle.height < opposite_edge_in_neigh_cell.threedi_exchange_level + min_obstacle_height - search_precision:
                            return []

                    obstacles.append(obstacle)
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
                        if obstacle_segment.from_side == obstacle_segment_from_side and \
                                obstacle_segment.to_side == OPPOSITE[obstacle_segment_from_side]:
                            edge = obstacle_segment.edge
                        else:
                            # find correct edge
                            mock_obstacle_segment = obstacle_segment.clone()
                            mock_obstacle_segment.from_side = obstacle_segment_from_side
                            mock_obstacle_segment.to_side = OPPOSITE[obstacle_segment_from_side]
                            mock_obstacle_segment.edge = None
                            edge = mock_obstacle_segment.edge  # will be calculated because it is None
                        obstacle = Obstacle([obstacle_segment], edge)
                        if obstacle.height > edge.threedi_exchange_level + min_obstacle_height:
                            direct_connection_obstacles.append(obstacle)
                    else:
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
                                    if obstacle.height > obstacle.edge.threedi_exchange_level + min_obstacle_height:
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
            obstacle.edge.obstacles.append(obstacle)

        self.parent.obstacles += final_obstacles


class CellPair:
    def __init__(self, reference_cell: Cell, neigh_cell: Cell):
        self.reference_cell = reference_cell
        self.neigh_cell = neigh_cell
        topo = reference_cell.parent
        if neigh_cell in topo.neigh_cells(reference_cell.id, TOP):
            self.pixels = np.vstack([neigh_cell.pixels, reference_cell.pixels])
            self.reference_cell_shift = (neigh_cell.pixels.shape[0], 0)  # {pos in this cell} + this_cell_shift = {pos in merged pixels}
            self.neigh_cell_shift = (0, 0)  # {pos in neigh. cell} + neigh_cell_shift = {pos in merged pixels}
        elif neigh_cell in topo.neigh_cells(reference_cell.id, RIGHT):
            self.pixels = np.hstack([reference_cell.pixels, neigh_cell.pixels])
            self.reference_cell_shift = (0, 0)
            self.neigh_cell_shift = (0, reference_cell.pixels.shape[1])
        elif neigh_cell in topo.neigh_cells(reference_cell.id, BOTTOM):
            self.pixels = np.vstack([reference_cell.pixels, neigh_cell.pixels])
            self.reference_cell_shift = (0, 0)
            self.neigh_cell_shift = (reference_cell.pixels.shape[0], 0)
        elif neigh_cell in topo.neigh_cells(reference_cell.id, LEFT):
            self.pixels = np.hstack([neigh_cell.pixels, reference_cell.pixels])
            self.reference_cell_shift = (0, neigh_cell.pixels.shape[1])
            self.neigh_cell_shift = (0, 0)

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

    def connect_in_cell_pair(
            self,
            search_start_pos_in_reference_cell: tuple,
            target_side: str,
            search_forward: bool,
            search_precision: float
    ) -> List[ObstacleSegment]:
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
        highest_so_far = -9999
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
            to_positions = SIDE_INDEX[target_side]
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


def highest(obstacles: List[Union[ObstacleSegment, Obstacle]]):
    """Return the highest obstacle or obstacle segment from a list of obstacles / obstacle segments.

    For Obstacle lists, obstacles with fewer segments will be preferred over
    obstacles of equal height with more segments
    """
    max_obstacle_height = -9999
    highest_obstacle = None
    for obstacle in obstacles:
        if obstacle.height >= max_obstacle_height:
            if isinstance(obstacle, Obstacle):
                if obstacle.height == max_obstacle_height and len(obstacle.segments) > len(highest_obstacle.segments):
                    continue
            max_obstacle_height = obstacle.height
            highest_obstacle = obstacle
    return highest_obstacle


def lowest(obstacles: List[Union[ObstacleSegment, Obstacle]]):
    """Return the lowest obstacle or obstacle segment from a list of obstacles / obstacle segments.

    For Obstacle lists, obstacles with fewer segments will be preferred over
    obstacles of equal height with more segments
    """
    min_obstacle_height = 9999
    lowest_obstacle = None
    for obstacle in obstacles:
        if obstacle.height <= min_obstacle_height:
            if isinstance(obstacle, Obstacle):
                if obstacle.height == min_obstacle_height and len(obstacle.segments) > len(lowest_obstacle.segments):
                    continue
            min_obstacle_height = obstacle.height
            lowest_obstacle = obstacle
    return lowest_obstacle


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
    field_defn_3di = ogr.FieldDefn('exchange_level_3di', ogr.OFTReal)
    field_defn_crest_level = ogr.FieldDefn('crest_level', ogr.OFTReal)

    lyr.CreateField(field_defn_id)
    lyr.CreateField(field_defn_3di)
    lyr.CreateField(field_defn_crest_level)

    lyr.StartTransaction()
    id_counter = 1
    for cell in topo.cells.values():
        for segment in cell.obstacle_segments:
            feat = ogr.Feature(lyr.GetLayerDefn())
            feat['id'] = id_counter
            feat['crest_level'] = segment.height
            if hasattr(segment, 'edge'):
                if hasattr(segment.edge, 'threedi_exchange_level'):
                    feat['exchange_level_3di'] = segment.edge.threedi_exchange_level
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
    field_defn_3di = ogr.FieldDefn('exchange_level_3di', ogr.OFTReal)
    field_defn_crest_level = ogr.FieldDefn('crest_level', ogr.OFTReal)

    lyr.CreateField(field_defn_id)
    lyr.CreateField(field_defn_3di)
    lyr.CreateField(field_defn_crest_level)

    lyr.StartTransaction()
    id_counter = 1
    for segment in topo.final_obstacle_segments.values():
        feat = ogr.Feature(lyr.GetLayerDefn())
        feat['id'] = id_counter
        feat['crest_level'] = segment.height
        feat['exchange_level_3di'] = segment.edge.threedi_exchange_level
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
