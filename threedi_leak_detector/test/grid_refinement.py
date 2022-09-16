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

OUT_GIS_FILE = DATA_DIR / f'test_output{current_date_time}.gpkg'


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
    # for obs in obstacle_segments:
    #     print(obs.__dict__)
    return obstacle_segments


def single_cell(test_cell_id: int, result_side: str, result_nr_obstacles:int, result_height: float):
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
    for edge_list in cell.edges.values():
        for edge in edge_list:
            edge.filter_obstacles(min_obstacle_height=MIN_OBSTACLE_HEIGHT, search_precision=SEARCH_PRECISION)
    topo.select_final_obstacle_segments()

    # test if `result_side` edge has obstacle
    if result_nr_obstacles > 0:
        assert cell.edges[result_side][0].highest_obstacle is not None

    # test if total number of obstacles equals `result_nr_obstacles`
    obstacles = []
    for edge in topo.edges.values():
        obstacle = edge.highest_obstacle
        if obstacle is not None:
            obstacles.append(obstacle)
    assert len(obstacles) == result_nr_obstacles

    # test if obstacle height is 5.0
    if result_nr_obstacles > 0:
        assert obstacles[0].height == result_height


def two_cells(
        test_cell_ids: List[int],
        result_nr_obstacles: int,
        result_height: float,
        result_nr_edges: int
    ):
    """Helper method to test cases with obstacle spread over two cells"""
    """Cells 78 and 98 should yield one obstacle on their shared edge"""
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
    # test if shared edge of the two input cells has obstacle
    cell_pair = CellPair(
        reference_cell=topo.cells[test_cell_ids[0]],
        neigh_cell=topo.cells[test_cell_ids[1]]
    )
    assert cell_pair.edge.highest_obstacle is not None

    # test if total number of obstacles equals `result_nr_obstacles`
    obstacles = []
    for edge in topo.edges.values():
        obstacle = edge.highest_obstacle
        if obstacle is not None:
            obstacles.append(obstacle)
    assert len(obstacles) == result_nr_obstacles

    # test if obstacle height equals `result_height`
    assert obstacles[0].height == result_height
    assert len(obstacles[0].edges) == result_nr_edges


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


def equal_size_horizontal_no_obstacle():
    pass


def equal_size_horizontal():
    """Cells 78 and 98 should yield one obstacle on their shared edge"""
    two_cells(test_cell_ids = [78, 98], result_nr_obstacles=1, result_height=5.0, result_nr_edges=1)


def equal_size_vertical():
    """Cells 38 and 39 should yield one obstacle on their shared edge"""
    two_cells(test_cell_ids = [38, 39], result_nr_obstacles=1, result_height=5.0, result_nr_edges=1)


def different_size_horizontal_top():
    """Cells 154 (large) and 196 (small, top) should yield one obstacle on their shared edge.
    The other RIGHT edge of cell 154 (shared with 195) should not be affected by this obstacle"""
    two_cells(test_cell_ids=[154, 196], result_nr_obstacles=1, result_height=5.0, result_nr_edges=1)


def different_size_horizontal_top_across():
    """Cells 158 (large) and 204 (small, top) should yield one obstacle
     that applies to both RIGHT edges of cell 158"""
    two_cells(test_cell_ids=[158, 204], result_nr_obstacles=1, result_height=5.0, result_nr_edges=2)


def different_size_horizontal_bottom_across():
    """Cells 156 (large) and 199 (small, bottom) should yield one obstacle on their shared edge"""
    two_cells(test_cell_ids=[156, 199], result_nr_obstacles=1, result_height=5.0, result_nr_edges=2)


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
single_cell_horizontal_obstacle_top()
single_cell_horizontal_obstacle_bottom()
single_cell_vertical_obstacle_left()
single_cell_diagonal_slope_dem()
equal_size_horizontal()
equal_size_vertical()
different_size_horizontal_top()
different_size_horizontal_top_across()
different_size_horizontal_bottom_across()

# np.set_printoptions(threshold=100000000)
# print(cell_pair.indices(BOTTOM).astype(int))
# obstacle_segments = connect_in_cell_pair(cell_pair, (0, 5))
# edge = get_edge(obstacle_segments[0])
# full_test(cell_ids=[156, 200])
# full_test(cell_ids = list(GR.cells.id))

