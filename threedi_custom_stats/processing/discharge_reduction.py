import numpy as np
from threedigrid.admin.gridresultadmin import GridH5ResultAdmin


OLD = "OLD"
NEW = "NEW"


class DischargeReductionFlowline:
    def __init__(
        self,
        id: int,
        pixel_size: float,
        exchange_levels: np.ndarray,
        discharge_timeseries: np.ndarray,
        old_obstacle_crest_level: float,
        new_obstacle_crest_level: float
    ):
        self.id = id
        self.pixel_size = pixel_size
        self.exchange_levels = exchange_levels
        self.discharge_timeseries = discharge_timeseries
        self.old_obstacle_crest_level = old_obstacle_crest_level
        self.new_obstacle_crest_level = new_obstacle_crest_level

    def _get_obstacle_crest_level(self, which_obstacle: str):
        if which_obstacle == OLD:
            obstacle_crest_level = self.old_obstacle_crest_level
        elif which_obstacle == NEW:
            obstacle_crest_level = self.old_obstacle_crest_level
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
        old_wet_cross_sectional_area = self.wet_cross_sectional_area(water_level=water_level, which_obstacle=OLD)
        new_wet_cross_sectional_area = self.wet_cross_sectional_area(water_level=water_level, which_obstacle=NEW)
        if old_wet_cross_sectional_area == 0 or new_wet_cross_sectional_area == 0:
            return 0
        old_wetted_perimeter = self.wetted_perimeter(water_level=water_level, which_obstacle=OLD)
        new_wetted_perimeter = self.wetted_perimeter(water_level=water_level,which_obstacle=NEW)
        result = np.sqrt(new_wet_cross_sectional_area / new_wetted_perimeter) / \
                 np.sqrt(old_wet_cross_sectional_area / old_wetted_perimeter)
        return result

    def discharge_reduction(
            self,
            grid_result_admin: GridH5ResultAdmin,
            start_time: float = None,
            end_time: float = None
    ):
        """
        Calculate the discharge reduction in m3 when an obstacle is applied to a flowline's cross-section
        """
        pass
