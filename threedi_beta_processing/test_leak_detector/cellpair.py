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


def width_and_height():
    cell_ids = [158, 159, 204, 205, 206]
    leak_detector = LeakDetector(
        gridadmin=GR,
        dem=DEM_DATASOURCE,
        cell_ids=cell_ids,
        min_obstacle_height=MIN_OBSTACLE_HEIGHT,
        search_precision=SEARCH_PRECISION,
        min_peak_prominence=MIN_PEAK_PROMINENCE
    )

    ref = leak_detector.cell(205)
    neigh = leak_detector.cell(206)
    cell_pair = CellPair(leak_detector, ref, neigh)
    assert cell_pair.width == 20
    assert cell_pair.height == 40


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
    cell_ids = [156, 157, 158, 159, 190, 199, 200, 203, 204, 205, 206, 219, 220]
    leak_detector = LeakDetector(
        gridadmin=GR,
        dem=DEM_DATASOURCE,
        cell_ids=cell_ids,
        min_obstacle_height=MIN_OBSTACLE_HEIGHT,
        search_precision=SEARCH_PRECISION,
        min_peak_prominence=MIN_PEAK_PROMINENCE
    )

    # Neigh is smaller, location is (RIGHT, TOP)
    ref = leak_detector.cell(158)
    neigh = leak_detector.cell(204)
    cell_pair = CellPair(leak_detector, ref, neigh)
    all_maxima = cell_pair.maxima()
    assert np.all(all_maxima["rhs"] == np.array([[39, 7]]))
    assert np.all(all_maxima["lhs"] == np.array([[0, 54]]))

    # Neigh is smaller, location is (RIGHT, TOP)
    # There are no right-hand-side nor left-hand-side maxima
    ref = leak_detector.cell(159)
    neigh = leak_detector.cell(206)
    cell_pair = CellPair(leak_detector, ref, neigh)
    all_maxima = cell_pair.maxima()
    assert len(all_maxima["rhs"]) == 0
    assert len(all_maxima["lhs"]) == 0

    # Neigh is same size, location is (TOP, N/A)
    ref = leak_detector.cell(205)
    neigh = leak_detector.cell(206)
    cell_pair = CellPair(leak_detector, ref, neigh)
    all_maxima = cell_pair.maxima()
    assert np.all(all_maxima["rhs"] == np.array([[16, 19]]))
    assert np.all(all_maxima["lhs"] == np.array([[11, 0]]))

    # Neigh is smaller, location is (RIGHT, BOTTOM)
    ref = leak_detector.cell(156)
    neigh = leak_detector.cell(199)
    cell_pair = CellPair(leak_detector, ref, neigh)
    all_maxima = cell_pair.maxima()
    assert np.all(all_maxima["rhs"] == np.array([[39, 51]]))
    assert np.all(all_maxima["lhs"] == np.array([[0, 4]]))

    # Neigh is bigger, location is (RIGHT, N/A)
    # Ref location is (LEFT, TOP)
    ref = leak_detector.cell(220)
    neigh = leak_detector.cell(190)
    cell_pair = CellPair(leak_detector, ref, neigh)
    all_maxima = cell_pair.maxima()
    print(all_maxima)
    assert np.all(all_maxima["rhs"] == np.array([[39, 52]]))
    assert np.all(all_maxima["lhs"] == np.array([[0, 38]]))


width_and_height()
locate()
maxima()
