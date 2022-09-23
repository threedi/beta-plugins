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
        self.edges = list()
        self._edge_dict = dict()

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
        cell_properties_dict = dict(zip(cell_properties['id'], np.round(cell_properties['cell_coords'].T, COORD_DECIMALS)))

        self._cell_dict = dict()
        for cell_id, cell_coords in cell_properties_dict.items():
            self._cell_dict[cell_id] = Cell(leak_detector=self, id=cell_id, coords=cell_coords)

        for cell in self.cells:
            cell.set_neighbours()

    @property
    def cells(self) -> List:
        return list(self._cell_dict.values())

    def find_edge(self, reference_cell, neigh_cell):
        """
        Find the edge between reference_cell (left/bottom) and neigh_cell (top/right)
        """
        return self._edge_dict[(reference_cell.id, neigh_cell.id)]

    def cell(self, cell_id):
        """
        Return the cell indicated by `cell_id`
        """
        return self._cell_dict[cell_id]


class Edge:
    """
    Edge between two cells
    """
    def __init__(self):
        pass


class Cell:
    """
    Cell in a computational grid, including an array of DEM pixel values
    """

    def __init__(
            self,
            leak_detector: LeakDetector,
            id: int,
            coords: np.ndarray
    ):
        """
        :param id: cell id
        :param leak_detector:
        :param coords: corner coordinates the crs of the dem: [min_x, min_y, max_x, max_y]
        """
        self.leak_detector = leak_detector
        self.id = id
        self.coords = coords
        self.pixels = read_as_array(raster=leak_detector.dem, bbox=coords, pad=True)
        band = leak_detector.dem.GetRasterBand(1)
        ndv = band.GetNoDataValue()
        maxval = np.nanmax(self.pixels)
        self.pixels[self.pixels == ndv] = maxval + \
                                          leak_detector.min_obstacle_height + \
                                          leak_detector.search_precision
        self.width = self.pixels.shape[1]
        self.height = self.pixels.shape[0]
        self.neigh_cells = None

    def set_neighbours(self):
        """Identify cells to the top and right of this cell"""
        self.neigh_cells = {RIGHT: [], TOP: []}
        cell_x_coords = self.coords[[0, 2]]
        self_xmax = np.max(cell_x_coords)
        next_cell_ids = self.leak_detector.line_nodes[np.where(self.leak_detector.line_nodes[:, 0] == self.id), 1].flatten()
        for next_cell_id in next_cell_ids:
            neigh_xmin = np.min(self.leak_detector.cell(next_cell_id).coords[[0, 2]])
            if self_xmax == neigh_xmin:  # aligned horizontally if True
                self.neigh_cells[RIGHT].append(self.leak_detector.cell(next_cell_id))
            else:
                self.neigh_cells[TOP].append(self.leak_detector.cell(next_cell_id))

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

        maxima_1d, _ = find_peaks(self.edge_pixels(side), prominence=self.leak_detector.min_peak_prominence)
        if side == TOP:
            row_indices = np.zeros(maxima_1d.shape)
            result = np.vstack([row_indices, maxima_1d]).T

        elif side == BOTTOM:
            row_indices = np.ones(maxima_1d.shape) * (self.height - 1)
            result = np.vstack([row_indices, maxima_1d]).T

        elif side == LEFT:
            col_indices = np.zeros(maxima_1d.shape)
            result = np.vstack([maxima_1d, col_indices]).T

        elif side == RIGHT:
            col_indices = np.ones(maxima_1d.shape) * (self.width - 1)
            result = np.vstack([maxima_1d, col_indices]).T

        return result


class CellPair:
    """
    A pair of neighbouring cells
    The reference cell is always the left / bottom of the pair
    """

    def __init__(self, leak_detector: LeakDetector, reference_cell: Cell, neigh_cell: Cell):
        self.leak_detector = leak_detector
        self.reference_cell = reference_cell
        self.neigh_cell = neigh_cell
        # self.edge = leak_detector.find_edge(reference_cell, neigh_cell)
        self.neigh_primary_location, self.neigh_secondary_location = self.locate(NEIGH)
        self.reference_primary_location, self.reference_secondary_location = self.locate(REFERENCE)
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

    def locate(self, which_cell: str) -> Tuple[str, str]:
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

    def maxima(self) -> Dict[str, np.ndarray]:
        """
        Return a dict of right-hand-side and left-hand-side indices of maximum locations (cell pair coordinates)
         {rhs: [maxima], lhs: [maxima]}
        """
        if self.neigh_primary_location == RIGHT:
            # right-hand-side edges are BOTTOM
            if self.bottom_aligned:
                # Calculate maxima in the continuous string of values at this side of the cell pair
                rhs_pixels = np.hstack([
                    self.reference_cell.edge_pixels(BOTTOM),
                    self.neigh_cell.edge_pixels(BOTTOM)
                ])
                rhs_maxima_1d, _ = find_peaks(rhs_pixels, prominence=self.leak_detector.min_peak_prominence)
                row_indices = np.ones(rhs_maxima_1d.shape)*(self.height-1)
                rhs_maxima = np.vstack([row_indices, rhs_maxima_1d]).T

            else:
                # Calculate maxima in each cell separately and stack them
                ref_maxima = self.reference_cell.maxima(BOTTOM)
                ref_maxima_transformed = np.array([self.transform(i, REFERENCE, MERGED) for i in ref_maxima])
                neigh_maxima = self.neigh_cell.maxima(BOTTOM)
                neigh_maxima_transformed = np.array([self.transform(i, NEIGH, MERGED) for i in neigh_maxima])
                print(f"ref_maxima_transformed: {ref_maxima_transformed}")
                print(f"neigh_maxima_transformed: {neigh_maxima_transformed}")
                rhs_maxima = np.array(ref_maxima_transformed.tolist() + neigh_maxima_transformed.tolist())

            # left-hand-side edges are TOP
            if self.top_aligned:
                # Calculate maxima in the continuous string of values at this side of the cell pair
                lhs_pixels = np.hstack([
                    self.reference_cell.edge_pixels(TOP),
                    self.neigh_cell.edge_pixels(TOP)
                ])
                lhs_maxima_1d, _ = find_peaks(lhs_pixels, prominence=self.leak_detector.min_peak_prominence)
                row_indices = np.zeros(lhs_maxima_1d.shape)
                lhs_maxima = np.vstack([row_indices, lhs_maxima_1d]).T

            else:
                # Calculate maxima in each cell separately and stack them
                ref_maxima = self.reference_cell.maxima(TOP)
                ref_maxima_transformed = np.array([self.transform(i, REFERENCE, MERGED) for i in ref_maxima])
                neigh_maxima = self.neigh_cell.maxima(TOP)
                neigh_maxima_transformed = np.array([self.transform(i, NEIGH, MERGED) for i in neigh_maxima])
                lhs_maxima = np.vstack([ref_maxima_transformed, neigh_maxima_transformed])

        elif self.neigh_primary_location == TOP:
            # right-hand-side edges are RIGHT
            if self.right_aligned:
                # Calculate maxima in the continuous string of values at this side of the cell pair
                rhs_pixels = np.hstack([
                    self.reference_cell.edge_pixels(RIGHT),
                    self.neigh_cell.edge_pixels(RIGHT)
                ])
                rhs_maxima_1d, _ = find_peaks(rhs_pixels, prominence=self.leak_detector.min_peak_prominence)
                col_indices = np.ones(rhs_maxima_1d.shape)*(self.width-1)
                rhs_maxima = np.vstack([rhs_maxima_1d, col_indices]).T

            else:
                # Calculate maxima in each cell separately and stack them
                ref_maxima = self.reference_cell.maxima(RIGHT)
                ref_maxima_transformed = np.array([self.transform(i, REFERENCE, MERGED) for i in ref_maxima])
                neigh_maxima = self.neigh_cell.maxima(RIGHT)
                neigh_maxima_transformed = np.array([self.transform(i, NEIGH, MERGED) for i in neigh_maxima])
                rhs_maxima = np.vstack([ref_maxima_transformed, neigh_maxima_transformed])

            # left-hand-side edges are LEFT
            if self.left_aligned:
                # Calculate maxima in the continuous string of values at this side of the cell pair
                lhs_pixels = np.hstack([
                    self.reference_cell.edge_pixels(LEFT),
                    self.neigh_cell.edge_pixels(LEFT)
                ])
                lhs_maxima_1d, _ = find_peaks(lhs_pixels, prominence=self.leak_detector.min_peak_prominence)
                col_indices = np.zeros(lhs_maxima_1d.shape)
                lhs_maxima = np.vstack([lhs_maxima_1d, col_indices]).T

            else:
                # Calculate maxima in each cell separately and stack them
                ref_maxima = self.reference_cell.maxima(LEFT)
                ref_maxima_transformed = np.array([self.transform(i, REFERENCE, MERGED) for i in ref_maxima])
                neigh_maxima = self.neigh_cell.maxima(LEFT)
                neigh_maxima_transformed = np.array([self.transform(i, NEIGH, MERGED) for i in neigh_maxima])
                lhs_maxima = np.vstack([ref_maxima_transformed, neigh_maxima_transformed])
        else:
            raise ValueError(f"self.neigh_primary_location = {self.neigh_primary_location}")

        return {"rhs": rhs_maxima, "lhs": lhs_maxima}