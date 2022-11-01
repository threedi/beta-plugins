from typing import List, Tuple
from pathlib import Path

import numpy as np
from osgeo import gdal
from threedigrid.admin.gridadmin import GridH5Admin

from leak_detector import CellPair, LeakDetector, REFERENCE, NEIGH, MERGED, RIGHT, TOP, LEFTHANDSIDE, RIGHTHANDSIDE

DATA_DIR = Path(__file__).parent / 'data'
DEM_FILENAME = DATA_DIR / 'dem_0_01.tif'
DEM_DATASOURCE = gdal.Open(str(DEM_FILENAME), gdal.GA_ReadOnly)
GRIDADMIN_FILENAME = DATA_DIR / 'gridadmin.h5'
GR = GridH5Admin(GRIDADMIN_FILENAME)
MIN_PEAK_PROMINENCE = 0.05
SEARCH_PRECISION = 0.001
MIN_OBSTACLE_HEIGHT = 0.05

SIDE_BOTTOM = 0
SIDE_LEFT = 0
SIDE_MIDDLE = 1
SIDE_TOP = 2
SIDE_RIGHT = 2


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


def locate_cell():
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
    assert cell_pair.locate_cell(NEIGH) == (RIGHT, TOP)


def locate_pos():
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
    assert cell_pair.locate_pos((0, 25)) == REFERENCE
    assert cell_pair.locate_pos((0, 39)) == REFERENCE
    assert cell_pair.locate_pos((0, 40)) == NEIGH
    assert cell_pair.locate_pos((0, 45)) == NEIGH


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
    assert np.all(all_maxima[RIGHTHANDSIDE] == np.array([[39, 7]]))
    assert np.all(all_maxima[LEFTHANDSIDE] == np.array([[0, 54]]))

    # Neigh is smaller, location is (RIGHT, TOP)
    # There are no right-hand-side nor left-hand-side maxima
    ref = leak_detector.cell(159)
    neigh = leak_detector.cell(206)
    cell_pair = CellPair(leak_detector, ref, neigh)
    all_maxima = cell_pair.maxima()
    assert len(all_maxima[RIGHTHANDSIDE]) == 0
    assert len(all_maxima[LEFTHANDSIDE]) == 0

    # Neigh is same size, location is (TOP, N/A)
    ref = leak_detector.cell(205)
    neigh = leak_detector.cell(206)
    cell_pair = CellPair(leak_detector, ref, neigh)
    all_maxima = cell_pair.maxima()
    assert np.all(all_maxima[RIGHTHANDSIDE] == np.array([[16, 19]]))
    assert np.all(all_maxima[LEFTHANDSIDE] == np.array([[11, 0]]))

    # Neigh is smaller, location is (RIGHT, BOTTOM)
    ref = leak_detector.cell(156)
    neigh = leak_detector.cell(199)
    cell_pair = CellPair(leak_detector, ref, neigh)
    all_maxima = cell_pair.maxima()
    assert np.all(all_maxima[RIGHTHANDSIDE] == np.array([[39, 51]]))
    assert np.all(all_maxima[LEFTHANDSIDE] == np.array([[0, 4]]))

    # Neigh is bigger, location is (RIGHT, N/A)
    # Ref location is (LEFT, TOP)
    ref = leak_detector.cell(220)
    neigh = leak_detector.cell(190)
    cell_pair = CellPair(leak_detector, ref, neigh)
    all_maxima = cell_pair.maxima()
    assert np.all(all_maxima[RIGHTHANDSIDE] == np.array([[39, 52]]))
    assert np.all(all_maxima[LEFTHANDSIDE] == np.array([[0, 38]]))


def find_obstacles_helper(
        cell_ids: List[int],
        result_obstacle_side: int,
        result_nr_obstacles: int,
        result_crest_levels: List[float],
        extra_edges_with_obstacles: List[Tuple[int, int]] = None
):
    leak_detector = LeakDetector(
        gridadmin=GR,
        dem=DEM_DATASOURCE,
        cell_ids=cell_ids,
        min_obstacle_height=MIN_OBSTACLE_HEIGHT,
        search_precision=SEARCH_PRECISION,
        min_peak_prominence=MIN_PEAK_PROMINENCE
    )

    ref = leak_detector.cell(cell_ids[0])
    neigh = leak_detector.cell(cell_ids[1])
    cell_pair = CellPair(leak_detector, ref, neigh)
    cell_pair.find_obstacles()
    edge = cell_pair.edges[result_obstacle_side][0]
    try:
        assert len(edge.obstacles) == result_nr_obstacles
    except AssertionError:
        print(f"len(edge.obstacles): {len(edge.obstacles)}")
        raise
    crest_levels = [obstacle.crest_level for obstacle in edge.obstacles]
    crest_levels.sort()
    result_crest_levels.sort()
    assert crest_levels == result_crest_levels

    if extra_edges_with_obstacles:
        for e in extra_edges_with_obstacles:
            edge = leak_detector.edge(*e)
            assert len(edge.obstacles) > 0


def find_obstacles():
    find_obstacles_helper(
        cell_ids=[55, 56],
        result_obstacle_side=SIDE_TOP,
        result_nr_obstacles=1,
        result_crest_levels=[5.0]
    )

    find_obstacles_helper(
        cell_ids=[56, 57],
        result_obstacle_side=SIDE_MIDDLE,
        result_nr_obstacles=2,
        result_crest_levels=[5.0, 5.0]
    )

    find_obstacles_helper(
        cell_ids=[38, 39],
        result_obstacle_side=SIDE_MIDDLE,
        result_nr_obstacles=1,
        result_crest_levels=[5.0]
    )

    find_obstacles_helper(
        cell_ids=[34, 54],
        result_obstacle_side=SIDE_MIDDLE,
        result_nr_obstacles=1,
        result_crest_levels=[5.0]
    )

    for side in [SIDE_LEFT, SIDE_MIDDLE, SIDE_TOP]:
        find_obstacles_helper(
            cell_ids=[35, 55],
            result_obstacle_side=side,
            result_nr_obstacles=0,
            result_crest_levels=[]
        )

    find_obstacles_helper(
        cell_ids=[159, 206],
        result_obstacle_side=SIDE_MIDDLE,
        result_nr_obstacles=0,
        result_crest_levels=[]
    )

    find_obstacles_helper(
        cell_ids=[158, 204],
        result_obstacle_side=SIDE_MIDDLE,
        result_nr_obstacles=1,
        result_crest_levels=[5.0],
        extra_edges_with_obstacles=[(158, 203)]
    )

    find_obstacles_helper(
        cell_ids=[156, 199],
        result_obstacle_side=SIDE_MIDDLE,
        result_nr_obstacles=1,
        result_crest_levels=[5.0],
        extra_edges_with_obstacles=[(156, 200)]
    )

    find_obstacles_helper(
        cell_ids=[172, 193],
        result_obstacle_side=SIDE_MIDDLE,
        result_nr_obstacles=1,
        result_crest_levels=[3.0]
    )

    find_obstacles_helper(
        cell_ids=[212, 186],
        result_obstacle_side=SIDE_MIDDLE,
        result_nr_obstacles=1,
        result_crest_levels=[5.0]
    )


def find_connecting_obstacles():
    cell_ids = [29, 30, 49, 50]
    leak_detector = LeakDetector(
        gridadmin=GR,
        dem=DEM_DATASOURCE,
        cell_ids=cell_ids,
        min_obstacle_height=MIN_OBSTACLE_HEIGHT,
        search_precision=SEARCH_PRECISION,
        min_peak_prominence=MIN_PEAK_PROMINENCE
    )

    for ref_id, neigh_id in [(29, 30), (29, 49), (30, 50)]:
        ref = leak_detector.cell(ref_id)
        neigh = leak_detector.cell(neigh_id)
        cell_pair = CellPair(leak_detector, ref, neigh)
        cell_pair.find_obstacles()

    assert len(leak_detector.edge(29, 30).obstacles) == 0

    ref = leak_detector.cell(29)
    neigh = leak_detector.cell(30)
    cell_pair = CellPair(leak_detector, ref, neigh)
    cell_pair.find_connecting_obstacles()

    print(leak_detector.edge(29, 30).obstacles)
    assert len(leak_detector.edge(29, 30).obstacles) == 1


def transform():
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

    # shape of cell 158: 40 x 40
    # shape of cell 204: 20 x 20
    # location of cell 204 is (RIGHT, TOP)
    pos = (13, 17)
    transformed = cell_pair.transform(
            pos=pos,
            from_array=REFERENCE,
            to_array=MERGED
    )
    assert transformed == (13, 17)


def squash_indices():
    # TODO: add tests here
    pass


def side_indices():
    # TODO: add tests here
    pass


def is_obstacle_relevant():
    # TODO: add tests here
    pass


# width_and_height()
# locate_cell()
# locate_pos()
# maxima()
# find_obstacles()
# find_connecting_obstacles()
transform()
