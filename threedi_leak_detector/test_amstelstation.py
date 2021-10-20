# ------------- TEST AMSTELSTATION
from leak_detector import *

dem_fn = 'C:/3Di/amstelstation/subgrid/dem_huidig.tif'
dem = gdal.Open(dem_fn, gdal.GA_ReadOnly)
ga = 'C:/Users/leendert.vanwolfswin/Documents/amstelstation/gridadmin.h5'
gr = GridH5Admin(ga)
out_gis_file = 'C:\\Users\\leendert.vanwolfswin\\Documents\\LeakDetector\\test_amstelstation34.gpkg'
test_cell_id = 12706

topo = Topology(gr, [test_cell_id], dem=dem)
xmin_i, ymin_i, xmax_i, ymax_i = topo.cell_coords[test_cell_id]
my_cell = Cell(parent=topo, id=test_cell_id, coords=topo.cell_coords[test_cell_id])
for edge in ['top', 'left', 'bottom', 'right']:
    print(f'exchange_levels {edge}: ', my_cell.edge(edge).exchange_levels)
my_cell.find_maxima(min_peak_prominence=0.3)
# print('minima: ', my_cell.minima)
print('maxima: ', my_cell.maxima)

my_cell.connect_maxima(search_precision=0.01, min_obstacle_height=0.3)

print('cell properties:')
print(my_cell)

print('obstacle properties test cell:')
for i in my_cell.obstacle_segments:
    print(i)

print('kleine testjes klaar')

obstacles = identify_obstacles(dem=dem,
                               gr=gr,
                               cell_ids=list(gr.cells.id),
                               # cell_ids=[test_cell_id],
                               min_peak_prominence=0.3,
                               search_precision=0.01,
                               min_obstacle_height=0.3,
                               output_fn=out_gis_file,
                               driver_name='GPKG'
                               )

ogr_lyr = obstacles.GetLayerByName('final_obstacle_segments')
print(ogr_lyr.GetFeatureCount())
obstacles = None
