from pathlib import Path
from datetime import datetime

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


def locate():
    cell_ids = [158, 204]
    leak_detector = LeakDetector(
        gridadmin=GR,
        dem=DEM_DATASOURCE,
        cell_ids=cell_ids,
        min_obstacle_height=MIN_OBSTACLE_HEIGHT,
        search_precision=SEARCH_PRECISION,
        min_peak_prominence=MIN_PEAK_PROMINENCE
    )
    ref = leak_detector.cell(158)
    neigh = leak_detector.cell(204)
    cell_pair = CellPair(leak_detector, ref, neigh)
    assert cell_pair.locate(NEIGH) == (RIGHT, TOP)


def maxima():
    cell_ids = [158, 204]
    leak_detector = LeakDetector(
        gridadmin=GR,
        dem=DEM_DATASOURCE,
        cell_ids=cell_ids,
        min_obstacle_height=MIN_OBSTACLE_HEIGHT,
        search_precision=SEARCH_PRECISION,
        min_peak_prominence=MIN_PEAK_PROMINENCE
    )

    ref = leak_detector.cell(158)
    neigh = leak_detector.cell(204)
    cell_pair = CellPair(leak_detector, ref, neigh)


    all_maxima = cell_pair.maxima()
    print(all_maxima)


locate()
maxima()
