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


DATA_DIR = Path(r"C:\Temp\dam locator\Dam Locator")
RESULTS_DIR = DATA_DIR / "Geul Oost T100 Gebiedsbreed Rev 4"
DEM_FILENAME = DATA_DIR / "schematisation" / "rasters" / "dem.tif"
DEM_DATASOURCE = gdal.Open(str(DEM_FILENAME), gdal.GA_ReadOnly)
GRIDADMIN_FILENAME = RESULTS_DIR / 'gridadmin.h5'
# RESULTS_FILENAME = RESULTS_DIR / 'results_3di.nc'
GRIDADMIN = GridH5Admin(GRIDADMIN_FILENAME)
# GRIDRESULTADMIN = GridH5ResultAdmin(str(GRIDADMIN_FILENAME), str(RESULTS_FILENAME))
MIN_PEAK_PROMINENCE = 0.05
SEARCH_PRECISION = 0.001
MIN_OBSTACLE_HEIGHT = 0.05

leak_detector = LeakDetector(
        gridadmin=GRIDADMIN,
        dem=DEM_DATASOURCE,
        flowline_ids=list(GRIDADMIN.lines.id),
        min_obstacle_height=MIN_OBSTACLE_HEIGHT,
        search_precision=SEARCH_PRECISION,
        min_peak_prominence=MIN_PEAK_PROMINENCE
   )
csv_lines = []
with open(DATA_DIR / "exchange_levels.csv", "w") as file:
    file.write("id,exchange_level\n")
    for edge in leak_detector.edges:
        file.write(f"{edge.flowline_id},{edge.exchange_level}")
        file.write("\n")
