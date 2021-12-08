# ------------- TEST AMSTELSTATION
from leak_detector import *

dem_fn = 'C:/3Di/w0127-rotterdam-3d-obstacle-detection/rasters/dem_01x01_new.tif'
dem = gdal.Open(dem_fn, gdal.GA_ReadOnly)
ga = 'C:/Users/leendert.vanwolfswin/Documents/rotterdam/obstacle_detection/revisie_2/gridadmin.h5'
gr = GridH5Admin(ga)
out_gis_file = 'C:/Users/leendert.vanwolfswin/Documents/rotterdam/obstacle_detection/test_rotterdam_08_5cm.gpkg'
test_cell_ids = [8377, 8376, 8375, 8654, 8655, 8931]
test_cell_id = 45

topo = Topology(gr, [test_cell_id], dem=dem)
xmin_i, ymin_i, xmax_i, ymax_i = topo.cell_coords[test_cell_id]
my_cell = Cell(parent=topo, id=test_cell_id, coords=topo.cell_coords[test_cell_id])
for side in ['top', 'left', 'bottom', 'right']:
    edge = my_cell.edge(side)
    if edge:
        print(f'exchange_levels {side}: ', my_cell.edge(side).exchange_levels)
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
                               # cell_ids=test_cell_ids,
                               min_peak_prominence=0.05,
                               search_precision=0.001,
                               min_obstacle_height=0.05,
                               output_fn=out_gis_file,
                               driver_name='GPKG'
                               )

ogr_lyr = obstacles.GetLayerByName('final_obstacle_segments')
print(ogr_lyr.GetFeatureCount())
obstacles = None
