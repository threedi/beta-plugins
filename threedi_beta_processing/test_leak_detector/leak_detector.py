from pathlib import Path

import numpy as np
from osgeo import gdal
from threedigrid.admin.gridadmin import GridH5Admin

from v2_leak_detector import CellPair, LeakDetector, NEIGH, RIGHT, TOP

DATA_DIR = Path(__file__).parent / 'data' / 'grid_refinement'
DEM_FILENAME = DATA_DIR / 'dem_0_01.tif'
DEM_DATASOURCE = gdal.Open(str(DEM_FILENAME), gdal.GA_ReadOnly)
GRIDADMIN_FILENAME = DATA_DIR / 'gridadmin.h5'
GR = GridH5Admin(GRIDADMIN_FILENAME)
MIN_PEAK_PROMINENCE = 0.05
SEARCH_PRECISION = 0.001
MIN_OBSTACLE_HEIGHT = 0.05

