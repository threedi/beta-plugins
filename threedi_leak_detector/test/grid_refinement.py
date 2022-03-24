# ------------- TEST ROTTERDAM

from pathlib import Path
from datetime import datetime
from leak_detector import *

DATA_DIR = Path(__file__).parent / 'data' / 'grid_refinement'
DEM_FILENAME = DATA_DIR / 'dem_0_01.tif'
DEM_DATASOURCE = gdal.Open(str(DEM_FILENAME), gdal.GA_ReadOnly)
GRIDADMIN_FILENAME = DATA_DIR / 'gridadmin.h5'
GR = GridH5Admin(GRIDADMIN_FILENAME)
current_date_time = datetime.now().strftime("%Y%m%d_%H%M%S")
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
    for obs in obstacle_segments:
        print(obs.__dict__)
    return obstacle_segments


def get_edge(obstacle_segment):
    edge = obstacle_segment.get_edges
    print(edge)
    return edge


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
    print(ogr_lyr.GetFeatureCount())
    obstacles = None

topo = create_topology()
get_cell(topo)
cell_pair = create_cell_pair(topo, 156, 200)
# np.set_printoptions(threshold=100000000)
# print(cell_pair.indices(BOTTOM).astype(int))
# obstacle_segments = connect_in_cell_pair(cell_pair, (0, 5))
# edge = get_edge(obstacle_segments[0])
# full_test(cell_ids = list(GR.cells.id))
full_test(cell_ids=[156, 200])

