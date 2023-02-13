import numpy as np

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
        print(f"old_total_discharge: {old_total_discharge}")
        discharge_reduction_factors = self.discharge_reduction_factors(water_levels)
        print(f"discharge_reduction_factors: {discharge_reduction_factors}")
        new_total_discharge = np.sum(discharges * discharge_reduction_factors * tintervals)
        print(f"new_total_discharge: {new_total_discharge}")
        return new_total_discharge - old_total_discharge

### TEST ###

from threedigrid.admin.gridresultadmin import GridH5ResultAdmin
from pathlib import Path

from osgeo import gdal
from threedigrid.admin.gridadmin import GridH5Admin

from leak_detector import LeakDetector
from threedi_result_aggregation.base import water_levels_at_cross_section, prepare_timeseries
from threedi_result_aggregation.aggregation_classes import (
    Aggregation,
    AggregationSign,
)
from threedi_result_aggregation.constants import (
    AGGREGATION_VARIABLES,
    AGGREGATION_METHODS,
)
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

flowline_id = 5972  # exchange level is ~ 133 m, water level varies from 134 to 134.6
leak_detector = LeakDetector(
        gridadmin=GRIDADMIN,
        dem=DEM_DATASOURCE,
        flowline_ids=[flowline_id],
        min_obstacle_height=MIN_OBSTACLE_HEIGHT,
        search_precision=SEARCH_PRECISION,
        min_peak_prominence=MIN_PEAK_PROMINENCE
    )
flowlines = GRIDRESULTADMIN.lines.filter(id__in=[5972])
edge = leak_detector.edge(*flowlines.line_nodes[0])
print(f"edge.exchange_level: {edge.exchange_level}")
print(f"edge.exchange_levels: {edge.exchange_levels}")
discharge_reduction_flowline = DischargeReductionFlowline(
    id=5972,
    pixel_size=leak_detector.dem.RasterXSize,
    exchange_levels=edge.exchange_levels,
    new_obstacle_crest_level=134.3
)
drf = discharge_reduction_flowline.discharge_reduction_factor(water_level=134.57425)
print(f"drf: {drf}")
aggregation_sign = AggregationSign(short_name="net", long_name="Net")
water_levels, tintervals = water_levels_at_cross_section(
            gr=GRIDRESULTADMIN,
            flowline_ids=flowlines.id,
            aggregation_sign=aggregation_sign,
        )
water_levels = water_levels.flatten()
tintervals = tintervals.flatten()
print(f"water_levels: {water_levels}")
drf_v = discharge_reduction_flowline.discharge_reduction_factors(
    water_levels=np.array([134.32193, 134.37238, 134.41074,
 134.44113, 134.46786, 134.49088, 134.5123,  134.52995, 134.54704, 134.56166,
 134.57425, 134.5852,  134.59477]))
print(f"drf_v: {drf_v}")

Q_NET_SUM = Aggregation(
    variable=AGGREGATION_VARIABLES.get_by_short_name("q"),
    method=AGGREGATION_METHODS.get_by_short_name("sum"),
    sign=AggregationSign("net", "Net"),
)

discharges, _ = prepare_timeseries(
    nodes_or_lines=flowlines,
    start_time=None,
    end_time=None,
    aggregation=Q_NET_SUM
)
discharges = discharges.flatten()
dr = discharge_reduction_flowline.discharge_reduction(water_levels, discharges, tintervals)
print(f"dr: {dr}")
