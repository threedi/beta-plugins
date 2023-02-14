from pathlib import Path

from leak_detector import LeakDetector, highest
from threedi_result_aggregation.base import water_levels_at_cross_section, prepare_timeseries
from threedi_result_aggregation.aggregation_classes import (
    Aggregation,
    AggregationSign,
)
from threedi_result_aggregation.constants import (
    AGGREGATION_VARIABLES,
    AGGREGATION_METHODS,
)

import numpy as np
from osgeo import gdal
from threedigrid.admin.gridadmin import GridH5Admin
from threedigrid.admin.gridresultadmin import GridH5ResultAdmin

OLD = "OLD"
NEW = "NEW"


class DischargeReductionFlowline:
    def __init__(
        self,
        id: int,
        pixel_size: float,
        exchange_levels: np.ndarray,
        old_obstacle_crest_level: float = None,
        new_obstacle_crest_level: float = None
    ):
        self.id = id
        self.pixel_size = pixel_size
        self.exchange_levels = exchange_levels
        self.old_obstacle_crest_level = old_obstacle_crest_level
        self.new_obstacle_crest_level = new_obstacle_crest_level

    def _get_obstacle_crest_level(self, which_obstacle: str):
        if which_obstacle == OLD:
            obstacle_crest_level = self.old_obstacle_crest_level
        elif which_obstacle == NEW:
            obstacle_crest_level = self.new_obstacle_crest_level
        else:
            raise ValueError(f"Value of argument 'which_obstacle' must be 'OLD' or 'NEW', not {which_obstacle}")
        obstacle_crest_level = np.min(self.exchange_levels) if obstacle_crest_level is None else obstacle_crest_level
        return obstacle_crest_level

    def wet_cross_sectional_area(self, water_level: float, which_obstacle: str):
        """
        Calculate the wet cross-sectional area from a 1D array of exchange levels (bed level values) and a water level.
        obstacle_crest_level may be specified to overrule exchange levels that are lower
        """
        obstacle_crest_level = self._get_obstacle_crest_level(which_obstacle)
        bed_levels = np.maximum(self.exchange_levels, obstacle_crest_level)
        water_depths = np.maximum(water_level - np.minimum(water_level, bed_levels), 0)
        return np.sum(water_depths * self.pixel_size)

    def wetted_perimeter(self, water_level: float, which_obstacle: str):
        """
        Calculate the wetted perimeter of a 2D cross-section; only the horizontal wet surface are taken into account
        """
        obstacle_crest_level = self._get_obstacle_crest_level(which_obstacle)
        return np.sum((np.maximum(self.exchange_levels, obstacle_crest_level) < water_level) * self.pixel_size)

    def discharge_reduction_factor(self, water_level: float):
        """
        reduction = Q_new/Q_old
        Based on:
         A: wet cross-sectional area
         v: flow velocity
         P: wetted perimeter

         Q = A*v (discharge)
         R = A/P (hydraulic radius)
         v = C*sqrt(R*i) (Chezy)
        So:
         Q = A * C * sqrt((A/P)*i)

        Assuming C and i are constant, we can ignore them when dividing Q_new by Q_old:
         reduction = (A_new * sqrt(A_new/P_new)) / (A_old * sqrt(A_old/P_old))
        """
        old_wet_cross_sectional_area = self.wet_cross_sectional_area(water_level=water_level, which_obstacle=OLD)
        new_wet_cross_sectional_area = self.wet_cross_sectional_area(water_level=water_level, which_obstacle=NEW)
        if old_wet_cross_sectional_area == 0 or new_wet_cross_sectional_area == 0:
            return 0
        old_wetted_perimeter = self.wetted_perimeter(water_level=water_level, which_obstacle=OLD)
        new_wetted_perimeter = self.wetted_perimeter(water_level=water_level,which_obstacle=NEW)
        result = np.sqrt(new_wet_cross_sectional_area / new_wetted_perimeter) / \
                 np.sqrt(old_wet_cross_sectional_area / old_wetted_perimeter)
        return result

    def discharge_reduction_factors(self, water_levels: np.array):
        """Vectorized version of `discharge_reduction_factor`"""
        v_discharge_reduction_factors = np.vectorize(self.discharge_reduction_factor, otypes=[float])
        return v_discharge_reduction_factors(water_levels)

    def discharge_reduction(
            self,
            water_levels: np.array,
            discharges: np.array,
            tintervals: np.array
    ):
        """
        Calculate the difference in net cumulative discharge when an obstacle is applied to a flowline's cross-section
        """
        old_total_discharge = np.sum(discharges * tintervals)
        discharge_reduction_factors = self.discharge_reduction_factors(water_levels)
        new_total_discharge = np.sum(discharges * discharge_reduction_factors * tintervals)
        return new_total_discharge - old_total_discharge


def discharge_reduction_for_detected_leaks(
        leak_detector: LeakDetector,
        grid_result_admin: GridH5ResultAdmin
):

    edges = leak_detector.result_edges()
    flowline_ids = [edge["flowline_id"] for edge in edges]
    flowlines = grid_result_admin.lines.filter(id__in=flowline_ids).only("id", "line")

    # get discharge and water_level_at_cross_section timeseries
    water_levels, tintervals = water_levels_at_cross_section(
        gr=grid_result_admin,
        flowline_ids=flowline_ids,
        aggregation_sign=AggregationSign(short_name="net", long_name="Net")
    )

    q_net_sum = Aggregation(
        variable=AGGREGATION_VARIABLES.get_by_short_name("q"),
        method=AGGREGATION_METHODS.get_by_short_name("sum"),
        sign=AggregationSign("net", "Net"),
    )
    discharges, _ = prepare_timeseries(nodes_or_lines=flowlines, aggregation=q_net_sum)

    result = dict()
    for i in range(flowlines.count):
        edge = leak_detector.edge(*flowlines.line_nodes[i])
        discharge_reduction_flowline = DischargeReductionFlowline(
            id=flowlines.id[i],
            pixel_size=leak_detector.dem.RasterXSize,
            exchange_levels=edge.exchange_levels,
            new_obstacle_crest_level=highest(edge.obstacles).crest_level
        )

        result[flowlines.id[i]] = discharge_reduction_flowline.discharge_reduction(
            water_levels[:, i],
            discharges[:, i],
            tintervals
        )
        return result


### TEST ###
DATA_DIR = Path(r"C:\Users\leendert.vanwolfswin\OneDrive - Nelen & Schuurmans\Documents 1\3Di\fuerthen_de - "
                r"fuerthen_fuerthen (1)")
RESULTS_DIR = DATA_DIR / "revision 14" / "results" / "sim_65948_fuerthen_40_mm_in_een_uur"
DEM_FILENAME = DATA_DIR / "work in progress" / "schematisation" / "rasters" / "dem.tif"
DEM_DATASOURCE = gdal.Open(str(DEM_FILENAME), gdal.GA_ReadOnly)
GRIDADMIN_FILENAME = RESULTS_DIR / 'gridadmin.h5'
RESULTS_FILENAME = RESULTS_DIR / 'results_3di.nc'
GRIDADMIN = GridH5Admin(GRIDADMIN_FILENAME)
GRIDRESULTADMIN = GridH5ResultAdmin(str(GRIDADMIN_FILENAME), str(RESULTS_FILENAME))
MIN_PEAK_PROMINENCE = 0.05
SEARCH_PRECISION = 0.001
MIN_OBSTACLE_HEIGHT = 0.05

flowline_ids = [5972, 5973, 5974]  # exchange level is ~ 133 m, water level varies from 134 to 134.6

leak_detector = LeakDetector(
        gridadmin=GRIDADMIN,
        dem=DEM_DATASOURCE,
        flowline_ids=flowline_ids,
        min_obstacle_height=MIN_OBSTACLE_HEIGHT,
        search_precision=SEARCH_PRECISION,
        min_peak_prominence=MIN_PEAK_PROMINENCE
    )


class MockFeedback:
    def setProgress(self, progress):
        pass

    def isCanceled(self):
        return False


leak_detector.run(MockFeedback())

print(discharge_reduction_for_detected_leaks(leak_detector=leak_detector, grid_result_admin=GRIDRESULTADMIN))