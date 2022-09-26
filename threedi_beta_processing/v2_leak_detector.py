from typing import Dict, Union, List, Tuple

import numpy as np
from osgeo import gdal
from scipy.ndimage import label, generate_binary_structure, maximum_position
from scipy.signal import find_peaks
from threedigrid.admin.gridadmin import GridH5Admin
from threedigrid.admin.lines.models import Lines

SEARCH_STRUCTURE = generate_binary_structure(2, 2)
TOP = 'top'
RIGHT = 'right'
BOTTOM = 'bottom'
LEFT = 'left'
LEFTHANDSIDE = "left-hand side"
RIGHTHANDSIDE = "right-hand side"
NA = 'N/A'
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
COORD_DECIMALS = 5
PSEUDO_INFINITE = 9999

gdal.UseExceptions()


def read_as_array(
        raster: gdal.Dataset,
        bbox: Union[List[float], Tuple[float], np.ndarray],
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
    :param decimals: `coords` are rounded to `decimals`

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


class LeakDetector:
    """
    Interface between the gridadmin and the classes in this module
    Maintains an administration of cells, edges and obstacles
    """

    def __init__(
            self,
            gridadmin: GridH5Admin,
            dem: gdal.Dataset,
            cell_ids: List[int],
            min_obstacle_height: float,
            search_precision: float,
            min_peak_prominence: float,
            feedback=None
    ):
        """
        :param gridadmin:
        :param dem:
        :param cell_ids: list of cell ids to limit the obstacle detection to. Neighbours of cells indicated by cell_ids
        will also be included in the analysis
        :param min_obstacle_height:
        :param search_precision:
        :param min_peak_prominence:
        :param feedback: Object that has .pushWarning() method, like QgsProcessingFeedback
        """
        self.dem = dem
        self.min_obstacle_height = min_obstacle_height
        self.search_precision = search_precision
        self.min_peak_prominence = min_peak_prominence

        # Get all flowlines that are connected to any of the cell_ids
        flowlines = filter_lines_by_node_ids(gridadmin.lines.subset('2D_OPEN_WATER'), node_ids=cell_ids)
        if np.all(np.isnan(flowlines.dpumax)):
            if feedback:
                feedback.pushWarning(
                    "Gridadmin file does not contain elevation data. Exchange levels will be derived from the DEM. "
                    "Obstacles will be ignored. Please use a gridadmin file that was generated on the server instead."
                )
        self.line_nodes = flowlines.line_nodes

        # Create cells
        threedigrid_cells = gridadmin.cells.filter(id__in=self.line_nodes.flatten())
        cell_properties = threedigrid_cells.only('id', 'cell_coords').data
        cell_properties_dict = dict(
            zip(cell_properties['id'], np.round(cell_properties['cell_coords'].T, COORD_DECIMALS)))

        self._cell_dict = dict()
        for cell_id, cell_coords in cell_properties_dict.items():
            self._cell_dict[cell_id] = Cell(ld=self, id=cell_id, coords=cell_coords)

        for cell in self.cells:
            cell.set_neighbours()

        # Create edges
        self._edge_dict = dict()  # {line_nodes: Edge}
        flowlines_list = flowlines.to_list()
        for flowline in flowlines_list:
            cell_ids: Tuple = flowline["line"]
            edge = Edge(ld=self, cell_ids=cell_ids, exchange_level=flowline["dpumax"])
            self._edge_dict[tuple(cell_ids)] = edge

    @property
    def cells(self) -> List:
        return list(self._cell_dict.values())

    def cell(self, cell_id):
        """
        Return the cell indicated by `cell_id`
        """
        return self._cell_dict[cell_id]

    @property
    def edges(self):
        """
        Find the edge between reference_cell (left/bottom) and neigh_cell (top/right)
        """
        return list(self._edge_dict.values())

    def edge(self, reference_cell, neigh_cell):
        """
        Find the edge between reference_cell (left/bottom) and neigh_cell (top/right)
        """
        return self._edge_dict[(reference_cell.id, neigh_cell.id)]


class Obstacle:
    """
    Obstacle between two sides of a CellPair
    """

    def __init__(
            self,
            crest_level,
            from_edges,
            to_edges,
            from_cell,
            to_cell,
            from_pos: Tuple[int, int],
            to_pos: Tuple[int, int],
            edges=None,
    ):
        self.crest_level = crest_level
        self.from_edges = from_edges
        self.to_edges = to_edges
        self.from_cell = from_cell
        self.to_cell = to_cell
        self.from_pos = from_pos
        self.to_pos = to_pos
        self.edges = edges if edges else []


class Edge:
    """
    Edge between two cells
    Drawing direction is always left -> right or bottom -> top.
    """

    def __init__(self, ld: LeakDetector, cell_ids: Tuple[int], exchange_level: float = None):
        self.ld = ld
        self.cell_ids = cell_ids
        self.obstacles: List[Obstacle] = list()

        # set start and end coordinates
        cell_1, cell_2 = [ld.cell(i) for i in cell_ids]
        side_coords1 = cell_1.side_coords()
        side_coords2 = cell_2.side_coords()
        for side_1 in [TOP, BOTTOM, LEFT, RIGHT]:
            for side_2 in [TOP, BOTTOM, LEFT, RIGHT]:
                intersection_coords = intersection(side_coords1[side_1], side_coords2[side_2])
                if intersection_coords:
                    self.start_coord, self.end_coord = intersection_coords

        # set exchange_level
        if np.isnan(exchange_level):
            exchange_level = None
        if exchange_level:
            self.exchange_level = exchange_level
        else:
            # calculate exchange level from DEM: 1D array of max of pixel pairs along the edge
            pxsize = self.ld.dem.GetGeoTransform()[1]
            if self.is_bottom_up():
                bbox = [self.start_coord[0] - pxsize, self.start_coord[1], self.end_coord[0] + pxsize,
                        self.end_coord[1]]
            else:
                bbox = [self.start_coord[0], self.start_coord[1] - pxsize, self.end_coord[0],
                        self.end_coord[1] + pxsize]
            arr = read_as_array(raster=self.ld.dem, bbox=bbox, pad=True)
            exchange_levels = np.nanmax(arr, axis=int(self.is_bottom_up()))
            self.exchange_level = np.nanmin(exchange_levels)

    def is_bottom_up(self):
        return self.start_coord[0] == self.end_coord[0]


class Cell:
    """
    Cell in a computational grid, including an array of DEM pixel values
    """

    def __init__(
            self,
            ld: LeakDetector,
            id: int,
            coords: np.ndarray
    ):
        """
        :param id: cell id
        :param ld:
        :param coords: corner coordinates the crs of the dem: [min_x, min_y, max_x, max_y]
        """
        self.ld = ld
        self.id = id
        self.coords = coords
        self.pixels = read_as_array(raster=ld.dem, bbox=coords, pad=True)
        band = ld.dem.GetRasterBand(1)
        ndv = band.GetNoDataValue()
        maxval = np.nanmax(self.pixels)
        self.pixels[self.pixels == ndv] = maxval + \
                                          ld.min_obstacle_height + \
                                          ld.search_precision
        self.width = self.pixels.shape[1]
        self.height = self.pixels.shape[0]
        self.neigh_cells = None

    def set_neighbours(self):
        """Identify cells to the top and right of this cell"""
        self.neigh_cells = {TOP: [], RIGHT: [], BOTTOM: [], LEFT: []}
        cell_x_coords = self.coords[[0, 2]]
        self_xmax = np.max(cell_x_coords)
        self_xmin = np.min(cell_x_coords)

        # next_cells: cells up / to the right
        next_cell_ids = self. \
            ld. \
            line_nodes[np.where(self.ld.line_nodes[:, 0] == self.id), 1]. \
            flatten()
        for next_cell_id in next_cell_ids:
            neigh_xmin = np.min(self.ld.cell(next_cell_id).coords[[0, 2]])
            if self_xmax == neigh_xmin:  # aligned horizontally if True
                self.neigh_cells[RIGHT].append(self.ld.cell(next_cell_id))
            else:
                self.neigh_cells[TOP].append(self.ld.cell(next_cell_id))

        # previous_cells: cells down / to the left
        previous_cell_ids = self. \
            ld. \
            line_nodes[np.where(self.ld.line_nodes[:, 1] == self.id), 0]. \
            flatten()
        for previous_cell_id in previous_cell_ids:
            neigh_xmax = np.max(self.ld.cell(previous_cell_id).coords[[0, 2]])
            if self_xmin == neigh_xmax:  # aligned horizontally if True
                self.neigh_cells[LEFT].append(self.ld.cell(previous_cell_id))
            else:
                self.neigh_cells[BOTTOM].append(self.ld.cell(previous_cell_id))

    @property
    def edges(self):
        return {
            TOP: [self.ld.edge(self, i) for i in self.neigh_cells[TOP]],
            BOTTOM: [self.ld.edge(i, self) for i in self.neigh_cells[BOTTOM]],
            LEFT: [self.ld.edge(i, self) for i in self.neigh_cells[LEFT]],
            RIGHT: [self.ld.edge(self, i) for i in self.neigh_cells[RIGHT]]
        }

    def side_coords(self):
        """Return dict with the coordinates of all sides of the cell"""
        xmin, ymin, xmax, ymax = self.coords
        return {
            TOP: ((xmin, ymax), (xmax, ymax)),
            BOTTOM: ((xmin, ymin), (xmax, ymin)),
            LEFT: ((xmin, ymin), (xmin, ymax)),
            RIGHT: ((xmax, ymin), (xmax, ymax)),
        }

    def edge_pixels(self, side: str) -> np.array:
        """
        Return the pixels on the inside of given `edge`
        Pixel values are sorted from TOP to BOTTOM or from LEFT to RIGHT
        """
        return self.pixels[SIDE_INDEX[side]]

    def maxima(self, side):
        """
        Return the pixel indices of the local maxima (peaks) along the edge at given `side`
        """

        maxima_1d, _ = find_peaks(self.edge_pixels(side), prominence=self.ld.min_peak_prominence)
        if side == TOP:
            row_indices = np.zeros(maxima_1d.shape)
            result = np.vstack([row_indices, maxima_1d]).T.astype(int)

        elif side == BOTTOM:
            row_indices = np.ones(maxima_1d.shape) * (self.height - 1)
            result = np.vstack([row_indices, maxima_1d]).T.astype(int)

        elif side == LEFT:
            col_indices = np.zeros(maxima_1d.shape)
            result = np.vstack([maxima_1d, col_indices]).T.astype(int)

        elif side == RIGHT:
            col_indices = np.ones(maxima_1d.shape) * (self.width - 1)
            result = np.vstack([maxima_1d, col_indices]).T.astype(int)

        return result


class CellPair:
    """
    A pair of neighbouring cells
    The reference cell is always the left / bottom of the pair
    """

    def __init__(self, ld: LeakDetector, reference_cell: Cell, neigh_cell: Cell):
        self.ld = ld
        self.reference_cell = reference_cell
        self.neigh_cell = neigh_cell
        self.neigh_primary_location, self.neigh_secondary_location = self.locate_cell(NEIGH)
        if self.neigh_primary_location not in [TOP, RIGHT]:
            raise ValueError(
                f"neigh_cell is located at the {self.neigh_primary_location} of reference_cell. It must be located at "
                f"the top or right of reference_cell"
            )
        self.reference_primary_location, self.reference_secondary_location = self.locate_cell(REFERENCE)
        smallest_cell = self.smallest()
        if smallest_cell:
            fill_array = smallest_cell.pixels * 0 - min(np.nanmin(reference_cell.pixels), np.nanmin(neigh_cell.pixels))
            if reference_cell.id == smallest_cell.id:
                smallest_secondary_location = self.reference_secondary_location
            else:
                smallest_secondary_location = self.neigh_secondary_location

        if self.neigh_primary_location == TOP:
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

        elif self.neigh_primary_location == RIGHT:
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

        elif self.neigh_primary_location == BOTTOM:
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

        elif self.neigh_primary_location == LEFT:
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
        self.width = self.pixels.shape[1]
        self.height = self.pixels.shape[0]

        # Determine shifts, i.e. paramaters to transform coordinates between ref cell, neigh cell and merged
        # {pos in ref cell} + self.reference_cell_shift = {pos in merged pixels}
        # {pos in neigh cell} + self.neigh_cell_shift = {pos in merged pixels}

        # Reference
        # x
        if self.neigh_primary_location == LEFT:
            reference_cell_shift_x = self.neigh_cell.width
        elif self.reference_secondary_location == RIGHT:
            reference_cell_shift_x = self.reference_cell.width
        else:
            reference_cell_shift_x = 0

        # y
        if self.neigh_primary_location == TOP:
            reference_cell_shift_y = self.neigh_cell.height
        elif self.reference_secondary_location == BOTTOM:
            reference_cell_shift_y = self.reference_cell.height
        else:
            reference_cell_shift_y = 0

        # Neigh
        # x
        if self.neigh_primary_location == RIGHT:
            neigh_cell_shift_x = self.reference_cell.width
        elif self.neigh_secondary_location == RIGHT:
            neigh_cell_shift_x = self.neigh_cell.width
        else:
            neigh_cell_shift_x = 0

        # y
        if self.neigh_primary_location == BOTTOM:
            neigh_cell_shift_y = self.reference_cell.height
        elif self.neigh_secondary_location == BOTTOM:
            neigh_cell_shift_y = self.neigh_cell.height
        else:
            neigh_cell_shift_y = 0

        self.reference_cell_shift = (reference_cell_shift_y, reference_cell_shift_x)
        self.neigh_cell_shift = (neigh_cell_shift_y, neigh_cell_shift_x)

        # Set edges
        self.edges = {}
        if self.neigh_primary_location == TOP:
            self.edges[0] = self.reference_cell.edges[BOTTOM]
            self.edges[1] = [self.ld.edge(self.reference_cell, self.neigh_cell)]
            self.edges[2] = self.neigh_cell.edges[TOP]
        if self.neigh_primary_location == RIGHT:
            self.edges[0] = self.reference_cell.edges[LEFT]
            self.edges[1] = [self.ld.edge(self.reference_cell, self.neigh_cell)]
            self.edges[2] = self.neigh_cell.edges[RIGHT]

    @property
    def bottom_aligned(self) -> bool:
        return round(self.reference_cell.coords[1], COORD_DECIMALS) == round(self.neigh_cell.coords[1], COORD_DECIMALS)

    @property
    def top_aligned(self) -> bool:
        return round(self.reference_cell.coords[3], COORD_DECIMALS) == round(self.neigh_cell.coords[3], COORD_DECIMALS)

    @property
    def left_aligned(self) -> bool:
        return round(self.reference_cell.coords[0], COORD_DECIMALS) == round(self.neigh_cell.coords[0], COORD_DECIMALS)

    @property
    def right_aligned(self) -> bool:
        return round(self.reference_cell.coords[2], COORD_DECIMALS) == round(self.neigh_cell.coords[2], COORD_DECIMALS)

    @property
    def lowest_edge(self):
        return lowest(self.edges[0] + self.edges[1] + self.edges[2])

    def locate_pos(self, pos: Tuple[int, int]) -> str:
        """
        Returns the cell ('reference' or 'neigh') in which given pixel position (index) is located
        """
        self.pixels[pos]  # to raise IndexError if out of bounds for this CellPair
        if self.neigh_primary_location == TOP:
            if pos[0] >= self.neigh_cell.height:
                return REFERENCE
            else:
                return NEIGH
        if self.neigh_primary_location == RIGHT:
            if pos[1] >= self.reference_cell.width:
                return NEIGH
            else:
                return REFERENCE

    def locate_cell(self, which_cell: str) -> Tuple[str, str]:
        """
        Return primary and secondary location of `which_cell` relative to the other cell in the pair
        If `which_cell` is the largest of the two or both cells are of the same size, secondary location is NA

        :param which_cell: REFERENCE or NEIGH
        :param decimals: the coordinates of the cell will be rounded to `decimals` when determining their location
        """
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
        for where in [TOP, RIGHT]:
            if self.neigh_cell in self.reference_cell.neigh_cells[where]:
                primary_location = where if which_cell == NEIGH else OPPOSITE[where]
                break
        if not primary_location:
            raise ValueError("Could determine primary location with given arguments")

        # secondary location
        if cell_to_locate.width >= other_cell.width:
            secondary_location = NA
        elif primary_location in [LEFT, RIGHT]:
            if self.bottom_aligned and self.top_aligned:
                secondary_location = NA
            elif self.bottom_aligned:
                secondary_location = BOTTOM
            elif self.top_aligned:
                secondary_location = TOP
            else:
                raise ValueError("Could not locate with given arguments")
        elif primary_location in [TOP, BOTTOM]:
            if self.left_aligned and self.right_aligned:
                secondary_location = NA
            elif self.left_aligned:
                secondary_location = LEFT
            elif self.right_aligned:
                secondary_location = RIGHT
            else:
                raise ValueError("Could not locate with given arguments")
        else:
            raise ValueError("Could not locate with given arguments")
        return primary_location, secondary_location

    def smallest(self) -> Union[Cell, None]:
        """
        Returns the smallest cell of self.`reference_cell` and self.`neigh_cell` or None if cells have the same width
        """
        if self.reference_cell.width < self.neigh_cell.width:
            return self.reference_cell
        elif self.reference_cell.width > self.neigh_cell.width:
            return self.neigh_cell
        else:
            return None

    def transform(self, pos: Tuple[int, int], from_array, to_array) -> Tuple[int, int]:
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

    def maxima(self) -> Dict[str, List[Tuple[int, int]]]:
        """
        Return a dict of right-hand-side and left-hand-side indices of maximum locations (cell pair coordinates)
        {rhs: [maxima], lhs: [maxima]}.
        \n
        Only maxima higher than `min_obstacle_height` - `search_precision` are included.
        """
        if self.neigh_primary_location == RIGHT:
            # right-hand-side edges are BOTTOM
            if self.bottom_aligned:
                # Calculate maxima in the continuous string of values at this side of the cell pair
                rhs_pixels = np.hstack([
                    self.reference_cell.edge_pixels(BOTTOM),
                    self.neigh_cell.edge_pixels(BOTTOM)
                ])
                rhs_maxima_1d, _ = find_peaks(rhs_pixels, prominence=self.ld.min_peak_prominence)
                row_indices = np.ones(rhs_maxima_1d.shape) * (self.height - 1)
                rhs_maxima = np.vstack([row_indices, rhs_maxima_1d]).T.astype(int)

            else:
                # Calculate maxima in each cell separately and stack them
                ref_maxima = self.reference_cell.maxima(BOTTOM)
                ref_maxima_transformed = np.array([self.transform(i, REFERENCE, MERGED) for i in ref_maxima])
                neigh_maxima = self.neigh_cell.maxima(BOTTOM)
                neigh_maxima_transformed = np.array([self.transform(i, NEIGH, MERGED) for i in neigh_maxima])
                rhs_maxima = np.array(ref_maxima_transformed.tolist() + neigh_maxima_transformed.tolist())

            # left-hand-side edges are TOP
            if self.top_aligned:
                # Calculate maxima in the continuous string of values at this side of the cell pair
                lhs_pixels = np.hstack([
                    self.reference_cell.edge_pixels(TOP),
                    self.neigh_cell.edge_pixels(TOP)
                ])
                lhs_maxima_1d, _ = find_peaks(lhs_pixels, prominence=self.ld.min_peak_prominence)
                row_indices = np.zeros(lhs_maxima_1d.shape)
                lhs_maxima = np.vstack([row_indices, lhs_maxima_1d]).T.astype(int)

            else:
                # Calculate maxima in each cell separately and stack them
                ref_maxima = self.reference_cell.maxima(TOP)
                ref_maxima_transformed = np.array([self.transform(i, REFERENCE, MERGED) for i in ref_maxima])
                neigh_maxima = self.neigh_cell.maxima(TOP)
                neigh_maxima_transformed = np.array([self.transform(i, NEIGH, MERGED) for i in neigh_maxima])
                lhs_maxima = np.array(ref_maxima_transformed.tolist() + neigh_maxima_transformed.tolist())

        elif self.neigh_primary_location == TOP:
            # right-hand-side edges are RIGHT
            if self.right_aligned:
                # Calculate maxima in the continuous string of values at this side of the cell pair
                rhs_pixels = np.hstack([
                    self.neigh_cell.edge_pixels(RIGHT),
                    self.reference_cell.edge_pixels(RIGHT)
                ])
                rhs_maxima_1d, _ = find_peaks(rhs_pixels, prominence=self.ld.min_peak_prominence)
                col_indices = np.ones(rhs_maxima_1d.shape) * (self.width - 1)
                rhs_maxima = np.vstack([rhs_maxima_1d, col_indices]).T.astype(int)

            else:
                # Calculate maxima in each cell separately and stack them
                ref_maxima = self.reference_cell.maxima(RIGHT)
                ref_maxima_transformed = np.array([self.transform(i, REFERENCE, MERGED) for i in ref_maxima])
                neigh_maxima = self.neigh_cell.maxima(RIGHT)
                neigh_maxima_transformed = np.array([self.transform(i, NEIGH, MERGED) for i in neigh_maxima])
                rhs_maxima = np.array(neigh_maxima_transformed.tolist() + ref_maxima_transformed.tolist())

            # left-hand-side edges are LEFT
            if self.left_aligned:
                # Calculate maxima in the continuous string of values at this side of the cell pair
                lhs_pixels = np.hstack([
                    self.neigh_cell.edge_pixels(LEFT),
                    self.reference_cell.edge_pixels(LEFT),
                ])
                lhs_maxima_1d, _ = find_peaks(lhs_pixels, prominence=self.ld.min_peak_prominence)
                col_indices = np.zeros(lhs_maxima_1d.shape)
                lhs_maxima = np.vstack([lhs_maxima_1d, col_indices]).T.astype(int)

            else:
                # Calculate maxima in each cell separately and stack them
                ref_maxima = self.reference_cell.maxima(LEFT)
                ref_maxima_transformed = np.array([self.transform(i, REFERENCE, MERGED) for i in ref_maxima])
                neigh_maxima = self.neigh_cell.maxima(LEFT)
                neigh_maxima_transformed = np.array([self.transform(i, NEIGH, MERGED) for i in neigh_maxima])
                lhs_maxima = np.array(neigh_maxima_transformed.tolist() + ref_maxima_transformed.tolist())

        else:
            raise ValueError(f"self.neigh_primary_location = {self.neigh_primary_location}")

        # Filter out maxima with too low pixel values
        filtered_rhs_maxima = []
        for pos in rhs_maxima:
            pos = tuple(pos)
            pixel_value = self.pixels[pos]
            if pixel_value > self.lowest_edge.exchange_level + \
                    self.ld.min_obstacle_height - \
                    self.ld.search_precision:
                filtered_rhs_maxima.append(pos)

        filtered_lhs_maxima = []
        for pos in lhs_maxima:
            pos = tuple(pos)
            pixel_value = self.pixels[pos]
            if pixel_value > self.lowest_edge.exchange_level + \
                    self.ld.min_obstacle_height - \
                    self.ld.search_precision:
                filtered_lhs_maxima.append(pos)

        return {RIGHTHANDSIDE: filtered_rhs_maxima, LEFTHANDSIDE: filtered_lhs_maxima}

    def crest_level_from_pixels(
            self,
            from_pos: Tuple[int, int],
            to_pos: Tuple[int, int]
    ) -> Union[float, None]:
        """
        Fin obstacle in self.pixels and return its crest level

        Returns None if no obstacle is found
        """
        from_val = self.pixels[from_pos]
        to_val = self.pixels[to_pos]

        # case: flat(ish) cellpair (from_val or max_to_val is not significantly higher than lowest pixel)
        if np.nanmin([from_val, to_val]) - np.nanmin(self.pixels) < self.ld.search_precision:
            return None

        # now find the obstacle crest level iteratively
        hmin = np.nanmin(self.pixels)
        hmax = np.nanmax([from_val, to_val])

        # case: from and to positions already connect at hmax
        labelled_pixels, labelled_pixels_nr_features = label(self.pixels >= hmax, structure=SEARCH_STRUCTURE)
        from_pixel_label = int(labelled_pixels[from_pos])
        to_pixel_label = labelled_pixels[to_pos]
        if from_pixel_label != 0 and np.any(to_pixel_label == from_pixel_label):
            obstacle_crest_level = hmax

        # all other cases
        else:
            while (hmax - hmin) > self.ld.search_precision:
                hcurrent = np.nanmean([hmin, hmax])
                labelled_pixels, _ = label(self.pixels > hcurrent, structure=SEARCH_STRUCTURE)
                from_pixel_label = int(labelled_pixels[from_pos])
                to_pixel_label = labelled_pixels[to_pos]
                if from_pixel_label != 0 and np.any(to_pixel_label == from_pixel_label):
                    # the two sides are connected at this threshold
                    hmin = hcurrent
                else:
                    # the two sides are NOT connected at this threshold
                    hmax = hcurrent

            obstacle_crest_level = float(np.mean([hmin, hmax]))

        return obstacle_crest_level

    def find_obstacles(self):
        """
        Obstacles are identified and assigned to the appropriate Edge
        """
        maxima = self.maxima()
        cells = {REFERENCE: self.reference_cell, NEIGH: self.neigh_cell}
        for from_pos in maxima[LEFTHANDSIDE]:
            for to_pos in maxima[RIGHTHANDSIDE]:
                crest_level = self.crest_level_from_pixels(from_pos=from_pos, to_pos=to_pos)
                if crest_level is None:
                    break

                # determine other obstacle properties
                from_pos_cell = self.locate_pos(from_pos)
                from_pos_transformed = self.transform(pos=from_pos, from_array=MERGED, to_array=from_pos_cell)
                to_pos_cell = self.locate_pos(to_pos)
                to_pos_transformed = self.transform(pos=to_pos, from_array=MERGED, to_array=to_pos_cell)

                # # from_edges, to_edges, from_cell, to_cell, from_pos, to_pos
                if self.neigh_primary_location == TOP:
                    from_side = LEFT
                    to_side = RIGHT
                else:
                    from_side = TOP
                    to_side = BOTTOM
                from_edges = cells[from_pos_cell].edges[from_side]
                to_edges = cells[to_pos_cell].edges[to_side]
                from_cell = cells[from_pos_cell]
                to_cell = cells[to_pos_cell]

                obstacle = Obstacle(
                    crest_level=crest_level,
                    from_edges=from_edges,
                    to_edges=to_edges,
                    from_cell=from_cell,
                    to_cell=to_cell,
                    from_pos=from_pos_transformed,
                    to_pos=to_pos_transformed
                )

                # # edge
                if from_pos_cell != to_pos_cell:
                    edges = self.edges[1]
                elif from_pos_cell == to_pos_cell:
                    edges = determine_edges(
                        ld=self.ld,
                        crest_level=crest_level,
                        cell=cells[from_pos_cell],
                        from_pos=from_pos_transformed,
                        is_left_to_right=self.neigh_primary_location == TOP
                    )

                # assign obstacle to crossing edges (and v.v.) if they are high enough
                if crest_level > lowest(edges).exchange_level + \
                        self.ld.min_obstacle_height - \
                        self.ld.search_precision:
                    for edge in edges:
                        edge.obstacles.append(obstacle)
                        obstacle.edges.append(edge)

    def find_connecting_obstacles(self):
        """
        Assumes that 'normal' obstacles have already been found

        If a high line element in the DEM is slightly skewed relative to the grid, the obstacles it produces may
        contain a gap at the location where it switches sides. This method generates an obstacle that connects the
        two sides, e.g.:

            |                   |
            |         --->      |
            |         --->      |___
                |     --->          |
                |                   |
                |                   |
        """
        for lhs_obstacle in self.obstacles[LEFTHANDSIDE]:
            for rhs_obstacle in self.obstacles[RIGHTHANDSIDE]:
                pass



def highest(elements: List[Union[Obstacle, Edge]]):
    """
    Return the highest element from a list of obstacles or edges.
    """
    max_element_height = -PSEUDO_INFINITE
    highest_element = None
    for element in elements:
        attr_name = 'exchange_level' if isinstance(element, Edge) else 'crest_level'
        if getattr(element, attr_name) >= max_element_height:
            max_element_height = getattr(element, attr_name)
            highest_element = element
    return highest_element


def lowest(elements: List[Union[Obstacle, Edge]]):
    """
    Return the lowest element from a list of obstaclesor edges.
    """
    min_element_height = PSEUDO_INFINITE
    lowest_element = None
    for element in elements:
        attr_name = 'exchange_level' if isinstance(element, Edge) else 'crest_level'
        if getattr(element, attr_name) <= min_element_height:
            min_element_height = getattr(element, attr_name)
            lowest_element = element
    return lowest_element


def determine_edges(
        ld: LeakDetector,
        crest_level: float,
        cell: Cell,
        from_pos: Tuple[int, int],
        is_left_to_right: bool
) -> List[Edge]:
    """
    For given `obstacle`, determine to which edges of `cell` it should be assigned
    Obstacle from_pos and to_pos should be within `cell`

    :param is_left_to_right: True if `obstacle` connects the left side of the cell to the right, False if top to bottom
    :returns: list of edges
    """
    labelled_pixels, labelled_pixels_nr_features = label(
        cell.pixels >= crest_level - ld.search_precision,
        structure=SEARCH_STRUCTURE
    )
    obstacle_pixels = labelled_pixels == labelled_pixels[from_pos]
    nr_obstacle_pixels_left = np.nansum(obstacle_pixels[:, 0:int(cell.width / 2)] == 1)
    nr_obstacle_pixels_right = np.nansum(obstacle_pixels[:, int(cell.width / 2):] == 1)
    nr_obstacle_pixels_top = np.nansum(obstacle_pixels[0:int(cell.height / 2), :] == 1)
    nr_obstacle_pixels_bottom = np.nansum(obstacle_pixels[int(cell.height / 2):, :] == 1)

    if is_left_to_right:
        if nr_obstacle_pixels_top > nr_obstacle_pixels_bottom:
            preferred_side = TOP
        else:
            preferred_side = BOTTOM
    else:
        if nr_obstacle_pixels_left > nr_obstacle_pixels_right:
            preferred_side = LEFT
        else:
            preferred_side = RIGHT
    return cell.edges[preferred_side]
