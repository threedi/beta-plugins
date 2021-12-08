from leak_detector import *

dem_fn = 'C:/Users/leendert.vanwolfswin/Documents/LeakDetector/model/rasters/dem.tif'
dem = gdal.Open(dem_fn, gdal.GA_ReadOnly)
ga = 'C:/Users/leendert.vanwolfswin/Documents/LeakDetector/test_result/gridadmin.h5'
# res = 'C:/Users/leendert.vanwolfswin/Documents/LeakDetector/test_result/results_3di.nc '
gr = GridH5Admin(ga)

test_cell_id = 12045
topo = Topology(gr, [test_cell_id], dem=dem)
xmin_i, ymin_i, xmax_i, ymax_i = topo.cell_coords[test_cell_id]
my_cell = Cell(parent=topo, id=test_cell_id, coords=topo.cell_coords[test_cell_id])
for side in ['top', 'left', 'bottom', 'right']:
    edge = my_cell.edge(side)
    if edge:
        print(f'exchange_levels {side}: ', my_cell.edge(side).exchange_levels)
my_cell.find_maxima(min_peak_prominence=0.1)
# print('minima: ', my_cell.minima)
print('maxima: ', my_cell.maxima)

cell_right = topo.neigh_cells(test_cell_id, 'right')[0]
cell_right.find_maxima(min_peak_prominence=0.1)

cell_down = topo.neigh_cells(test_cell_id, 'bottom')[0]
cell_down.find_maxima(min_peak_prominence=0.1)

my_cell.connect_maxima(search_precision=0.01, min_obstacle_height=0.3)

print('cell properties:')
print(my_cell)

print('obstacle properties test cell:')
for i in my_cell.obstacle_segments:
    print(i)

print('obstacle properties cell below test cell:')
for i in cell_down.obstacle_segments:
    print(i)
print('kleine testjes klaar')

####
out_gis_file = 'C:\\Users\\leendert.vanwolfswin\\Documents\\LeakDetector\\test100.gpkg'
obstacles = identify_obstacles(     dem=dem,
                                    gr=gr,
                                    cell_ids=list(gr.cells.id),
                                    # cell_ids=[test_cell_id],
                                    min_peak_prominence=0.1,
                                    search_precision=0.01,
                                    min_obstacle_height=0.3,
                                    output_fn=out_gis_file,
                                    driver_name='GPKG'
                               )

ogr_lyr = obstacles.GetLayerByName('final_obstacle_segments')
print(ogr_lyr.GetFeatureCount())
obstacles = None

