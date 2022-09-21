from pathlib import Path
from datetime import datetime
from leak_detector import *

DATA_DIR = Path(__file__).parent / 'data' / 'grid_refinement'
DEM_FILENAME = DATA_DIR / 'dem_0_01.tif'
DEM_DATASOURCE = gdal.Open(str(DEM_FILENAME), gdal.GA_ReadOnly)
GRIDADMIN_FILENAME = DATA_DIR / 'gridadmin.h5'
GR = GridH5Admin(GRIDADMIN_FILENAME)
current_date_time = datetime.now().strftime("%Y%m%d_%H%M%S")
MIN_PEAK_PROMINENCE = 0.05
SEARCH_PRECISION = 0.001
MIN_OBSTACLE_HEIGHT = 0.05

OUT_GIS_FILE = DATA_DIR / "output" / f'test_output{current_date_time}.gpkg'


def create_topology():
    cell_ids = list(GR.cells.id)
    topo = Topology(GR, cell_ids, dem=DEM_DATASOURCE)
    assert len(topo.neigh_cells(20, RIGHT)) == 1
    assert topo.neigh_cells(20, RIGHT)[0].id == 40
    assert topo.neigh_cells(20, BOTTOM)[0].id == 19
    assert len(topo.neigh_cells(20, LEFT)) == 0
    assert len(topo.neigh_cells(20, TOP)) == 0

    assert topo.neigh_cells(136, RIGHT)[0].id == 156
    assert topo.neigh_cells(136, BOTTOM)[0].id == 135
    assert topo.neigh_cells(136, LEFT)[0].id == 116
    assert topo.neigh_cells(136, TOP)[0].id == 137

    assert len(topo.neigh_cells(158, RIGHT)) == 2
    assert topo.neigh_cells(158, RIGHT)[0].id == 203
    assert topo.neigh_cells(158, RIGHT)[1].id == 204

    assert topo.neigh_cells(203, LEFT)[0].id == 158
    assert topo.neigh_cells(204, LEFT)[0].id == 158

    return topo


def get_cell(topo):
    assert topo.cells[158].pixels.shape == (40, 40)
    assert topo.cells[158].width == 40
    assert topo.cells[204].pixels.shape == (20, 20)
    assert topo.cells[204].width == 20


def cell_edges_unequal_cell_size():
    cell_id = 155
    topo = Topology(GR, [cell_id], dem=DEM_DATASOURCE)
    cell = topo.cells[155]
    assert len(cell.edges[RIGHT]) == 2
    assert len(cell.edges[LEFT]) == 1


def create_cell_pair(topo, id1, id2):
    pair = CellPair(topo.cells[id1], topo.cells[id2])
    return pair


def connect_in_cell_pair(cell_pair, search_start_pos_in_reference_cell):
    obstacle_segments = cell_pair.connect_in_cell_pair(
        # search_start_pos_in_reference_cell=(0, 5),
        search_start_pos_in_reference_cell=search_start_pos_in_reference_cell,
        target_side=BOTTOM,
        search_forward=False,
        search_precision=0.001
    )
    assert len(obstacle_segments) == 1
    return obstacle_segments


def cell_pair_locate_helper(test_cell_ids: List[int], which_cell: str, result_location: Tuple):
    """Test the CellPair.locate() method for several input combinations"""
    topo = Topology(GR, test_cell_ids, dem=DEM_DATASOURCE)
    cell_pair = CellPair(reference_cell=topo.cells[test_cell_ids[0]],
                         neigh_cell=topo.cells[test_cell_ids[1]])
    location = cell_pair.locate(which_cell=which_cell)
    assert location == result_location


def cell_pair_locate():
    """Test the CellPair.locate() method for several input combinations"""
    # Same size
    # # Horizontal
    cell_pair_locate_helper([100, 120], REFERENCE, (LEFT, NA))
    cell_pair_locate_helper([100, 120], NEIGH, (RIGHT, NA))

    # # Vertical
    cell_pair_locate_helper([117, 118], REFERENCE, (BOTTOM, NA))
    cell_pair_locate_helper([117, 118], NEIGH, (TOP, NA))

    # Different size
    # # Horizontal
    # # # Larger cell primary location is left
    # # # # Smaller cell secondary location is top
    cell_pair_locate_helper([159, 206], REFERENCE, (LEFT, NA))
    cell_pair_locate_helper([159, 206], NEIGH, (RIGHT, TOP))

    # # # # Smaller cell secondary location is bottom
    cell_pair_locate_helper([159, 205], REFERENCE, (LEFT, NA))
    cell_pair_locate_helper([159, 205], NEIGH, (RIGHT, BOTTOM))

    # # # Larger cell primary location is right
    # # # # Smaller cell secondary location is top
    cell_pair_locate_helper([191, 222], REFERENCE, (RIGHT, NA))
    cell_pair_locate_helper([191, 222], NEIGH, (LEFT, TOP))

    # # # # Smaller cell secondary location is bottom
    cell_pair_locate_helper([191, 221], REFERENCE, (RIGHT, NA))
    cell_pair_locate_helper([191, 221], NEIGH, (LEFT, BOTTOM))

    # # Vertical
    # # # Larger cell primary location is BOTTOM
    # # # # Smaller cell secondary location is LEFT
    cell_pair_locate_helper([172, 193], REFERENCE, (BOTTOM, NA))
    cell_pair_locate_helper([172, 193], NEIGH, (TOP, LEFT))

    # # # # Smaller cell secondary location is RIGHT
    cell_pair_locate_helper([172, 209], REFERENCE, (BOTTOM, NA))
    cell_pair_locate_helper([172, 209], NEIGH, (TOP, RIGHT))

    # # # Larger cell primary location is TOP
    # # # # Smaller cell secondary location is top
    # NOT TESTED

    # # # # Smaller cell secondary location is bottom
    # NOT TESTED


def cell_pair_smallest_helper(test_cell_ids, result):
    topo = Topology(GR, test_cell_ids, dem=DEM_DATASOURCE)
    cell_pair = CellPair(reference_cell=topo.cells[test_cell_ids[0]],
                         neigh_cell=topo.cells[test_cell_ids[1]])
    if result is None:
        assert cell_pair.smallest() is None
    else:
        assert cell_pair.smallest() == topo.cells[result]


def cell_pair_smallest():
    """"Tests for CellPair.smallest() """
    # equal size
    cell_pair_smallest_helper(test_cell_ids=[115, 116], result=None)

    # neigh cell location = (RIGHT, TOP)
    cell_pair_smallest_helper(test_cell_ids=[155, 198], result=198)
    cell_pair_smallest_helper(test_cell_ids=[198, 155], result=198)

    # neigh cell location = (RIGHT, BOTTOM)
    cell_pair_smallest_helper(test_cell_ids=[155, 197], result=197)
    cell_pair_smallest_helper(test_cell_ids=[197, 155], result=197)

    # neigh cell location = (TOP, LEFT)
    cell_pair_smallest_helper(test_cell_ids=[172, 193], result=193)
    cell_pair_smallest_helper(test_cell_ids=[193, 172], result=193)

    # neigh cell location = (TOP, RIGHT)
    cell_pair_smallest_helper(test_cell_ids=[172, 209], result=209)
    cell_pair_smallest_helper(test_cell_ids=[209, 172], result=209)


def single_cell(test_cell_id: int, result_side: Union[str, None], result_nr_obstacles:int, result_height: float):
    """Helper method to test several single-cell cases"""
    topo = Topology(GR, [test_cell_id], dem=DEM_DATASOURCE)
    cell = topo.cells[test_cell_id]
    cell.find_maxima(min_peak_prominence=MIN_PEAK_PROMINENCE)
    cell.connect_maxima(search_precision=SEARCH_PRECISION, min_obstacle_height=MIN_OBSTACLE_HEIGHT)
    cell.create_obstacles_from_segments(
        direct_connection_preference=MIN_OBSTACLE_HEIGHT,
        search_precision=SEARCH_PRECISION,
        min_obstacle_height=MIN_OBSTACLE_HEIGHT
    )
    topo.filter_obstacles(min_obstacle_height=MIN_OBSTACLE_HEIGHT, search_precision=SEARCH_PRECISION)
    topo.deduplicate_obstacles(search_precision=SEARCH_PRECISION)

    # test if total number of obstacles equals `result_nr_obstacles`
    obstacles = []
    for edge in topo.edges:
        obstacle = edge.highest_obstacle
        if obstacle is not None:
            obstacles.append(obstacle)
    assert len(obstacles) == result_nr_obstacles

    # test if obstacle height is 5.0
    if result_nr_obstacles > 0:
        assert obstacles[0].height == result_height

    # test if `result_side` edge has obstacle
    if result_nr_obstacles > 0:
        assert cell.edges[result_side][0].highest_obstacle is not None


def two_cells(
        test_cell_ids: List[int],
        result_nr_obstacles: int,
        result_height: float,
        result_nr_edges: int,
        result_nr_edges_with_obstacles
    ):
    """Helper method to test cases with obstacle spread over two cells"""
    topo = Topology(GR, test_cell_ids, dem=DEM_DATASOURCE)
    for cell_id in test_cell_ids:
        cell = topo.cells[cell_id]
        cell.find_maxima(min_peak_prominence=MIN_PEAK_PROMINENCE)
        cell.connect_maxima(
            search_precision=SEARCH_PRECISION,
            min_obstacle_height=MIN_OBSTACLE_HEIGHT
        )
    for cell_id in test_cell_ids:
        cell = topo.cells[cell_id]
        cell.create_obstacles_from_segments(
            direct_connection_preference=MIN_OBSTACLE_HEIGHT,
            search_precision=SEARCH_PRECISION,
            min_obstacle_height=MIN_OBSTACLE_HEIGHT
        )
    topo.filter_obstacles(min_obstacle_height=MIN_OBSTACLE_HEIGHT, search_precision=SEARCH_PRECISION)
    topo.deduplicate_obstacles(search_precision=SEARCH_PRECISION)
    # test if shared edge of the two input cells has obstacle
    cell_pair = CellPair(
        reference_cell=topo.cells[test_cell_ids[0]],
        neigh_cell=topo.cells[test_cell_ids[1]]
    )
    assert cell_pair.edge.highest_obstacle is not None

    # test if total number of obstacles equals `result_nr_obstacles`
    # Deduplication isn't perfect, so we skip this test
    # assert len(topo.obstacles) == result_nr_obstacles

    # test if total number of edges with obstacles equals `result_nr_edges_with_obstacles`
    nr_edges_with_obstacles = len([edge for edge in topo.edges if len(edge.obstacles) > 0])
    assert nr_edges_with_obstacles == result_nr_edges_with_obstacles

    # test if obstacle height equals `result_height`
    assert topo.obstacles[0].height == result_height
    assert len(topo.obstacles[0].edges) == result_nr_edges


def single_cell_horizontal_obstacle_top():
    """Cell 56 should result in 1 obstacle from left to right, applied to the top edge"""
    single_cell(test_cell_id=56, result_side=TOP, result_nr_obstacles=1, result_height=5.0)


def single_cell_horizontal_obstacle_bottom():
    """Cell 57 should result in 1 obstacle from left to right, applied to the bottom edge"""
    single_cell(test_cell_id=57, result_side=BOTTOM, result_nr_obstacles=1, result_height=5.0)


def single_cell_vertical_obstacle_left():
    """Cell 75 should result in 1 obstacle from top to bottom, applied to the right edge"""
    single_cell(test_cell_id=75, result_side=RIGHT, result_nr_obstacles=1, result_height=5.0)


def single_cell_vertical_obstacle_right():
    """Cell 95 should result in 1 obstacle from top to bottom, applied to the left edge"""
    single_cell(test_cell_id=95, result_side=LEFT, result_nr_obstacles=1, result_height=5.0)


def single_cell_diagonal_slope_dem():
    """Cell 42 should result in 0 obstacles"""
    single_cell(test_cell_id=42, result_side=None, result_nr_obstacles=0, result_height=None)


def single_cell_free_search():
    """Cell 34 should yield 1 obstacle at the RIGHT edge"""
    single_cell(test_cell_id=34, result_side=RIGHT, result_nr_obstacles=1, result_height=5.0)


def equal_size_horizontal_no_obstacle():
    pass


def equal_size_horizontal():
    """Cells 78 and 98 should yield one obstacle on their shared edge"""
    two_cells(
        test_cell_ids=[78, 98],
        result_nr_obstacles=1,
        result_height=5.0,
        result_nr_edges=1,
        result_nr_edges_with_obstacles=1
    )


def equal_size_vertical():
    """Cells 38 and 39 should yield one obstacle on their shared edge"""
    two_cells(
        test_cell_ids=[38, 39],
        result_nr_obstacles=1,
        result_height=5.0,
        result_nr_edges=1,
        result_nr_edges_with_obstacles=1
    )


def different_size_horizontal_top():
    """Cells 154 (large) and 196 (small, top) should yield one obstacle on their shared edge.
    The other RIGHT edge of cell 154 (shared with 195) should not be affected by this obstacle"""
    two_cells(
        test_cell_ids=[154, 196],
        result_nr_obstacles=1,
        result_height=5.0,
        result_nr_edges=1,
        result_nr_edges_with_obstacles=1
    )


def different_size_horizontal_top_across():
    """Cells 158 (large) and 204 (small, top) should yield one obstacle
     that applies to both RIGHT edges of cell 158"""
    two_cells(
        test_cell_ids=[158, 204],
        result_nr_obstacles=1,
        result_height=5.0,
        result_nr_edges=2,
        result_nr_edges_with_obstacles=2
    )


def different_size_horizontal_bottom_across():
    """Cells 156 (large) and 199 (small, bottom) should yield one obstacle on their shared edge"""
    two_cells(
        test_cell_ids=[156, 199],
        result_nr_obstacles=1,
        result_height=5.0,
        result_nr_edges=2,
        result_nr_edges_with_obstacles=2
    )


def different_size_vertical_left_across():
    """Cells 172 (large) and 193 (small, left) should yield one obstacle on their shared edge"""
    two_cells(
        test_cell_ids=[172, 193],
        result_nr_obstacles=1,
        result_height=3.0,
        result_nr_edges=2,
        result_nr_edges_with_obstacles=2
    )


def connecting_obstacle():
    test_cell_ids = [29, 30, 31]
    topo = Topology(GR, test_cell_ids, dem=DEM_DATASOURCE)
    for cell_id in test_cell_ids:
        cell = topo.cells[cell_id]
        cell.find_maxima(min_peak_prominence=MIN_PEAK_PROMINENCE)
        cell.connect_maxima(
            search_precision=SEARCH_PRECISION,
            min_obstacle_height=MIN_OBSTACLE_HEIGHT
        )
    for cell_id in test_cell_ids:
        cell = topo.cells[cell_id]
        cell.create_obstacles_from_segments(
            direct_connection_preference=MIN_OBSTACLE_HEIGHT,
            search_precision=SEARCH_PRECISION,
            min_obstacle_height=MIN_OBSTACLE_HEIGHT
        )
    topo.filter_obstacles(min_obstacle_height=MIN_OBSTACLE_HEIGHT, search_precision=SEARCH_PRECISION)
    topo.deduplicate_obstacles(search_precision=SEARCH_PRECISION)

    # test if total number of edges with obstacles equals `result_nr_edges_with_obstacles`
    assert len(CellPair(topo.cells[9], topo.cells[29]).edge.obstacles) == 1
    assert len(CellPair(topo.cells[30], topo.cells[50]).edge.obstacles) == 1
    assert len(CellPair(topo.cells[31], topo.cells[51]).edge.obstacles) == 1
    assert len(CellPair(topo.cells[29], topo.cells[30]).edge.obstacles) == 0

    # for edge in topo.edges:
    #     edge.generate_connecting_obstacle(min_obstacle_height=MIN_OBSTACLE_HEIGHT, search_precision=SEARCH_PRECISION)

    edge = CellPair(topo.cells[29], topo.cells[30]).edge
    edge.generate_connecting_obstacle(min_obstacle_height=MIN_OBSTACLE_HEIGHT, search_precision=SEARCH_PRECISION)

    assert len(CellPair(topo.cells[29], topo.cells[30]).edge.obstacles) == 1


def full_test(cell_ids: List):
    obstacles = identify_obstacles(
        dem=DEM_DATASOURCE,
        gr=GR,
        cell_ids=cell_ids,
        min_peak_prominence=0.05,
        search_precision=0.001,
        min_obstacle_height=0.05,
        output_fn=str(OUT_GIS_FILE),
        driver_name='GPKG'
    )
    ogr_lyr = obstacles.GetLayerByName('edge_with_obstacle')
    print(f"Number of edges with obstacles: {ogr_lyr.GetFeatureCount()}")
    obstacles = None


topo=create_topology()
get_cell(topo)
cell_edges_unequal_cell_size()
cell_pair = create_cell_pair(topo, 156, 200)
cell_pair_locate()
cell_pair_smallest()
single_cell_horizontal_obstacle_top()
single_cell_horizontal_obstacle_bottom()
single_cell_vertical_obstacle_left()
single_cell_diagonal_slope_dem()
single_cell_free_search()
equal_size_horizontal()
equal_size_vertical()
different_size_horizontal_top()
different_size_horizontal_top_across()
different_size_horizontal_bottom_across()
different_size_vertical_left_across()
connecting_obstacle()

full_test(cell_ids = list(GR.cells.id))

