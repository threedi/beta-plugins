from leak_detector import *


dem_fn = 'C:\\3Di\\heugem_limmel_geul_midden\\rasters\\dem_geul_midden.tif'
dem = gdal.Open(dem_fn, gdal.GA_ReadOnly)

ga = 'C:\\Users\\leendert.vanwolfswin\\Documents\\heugem-limmel\\resultaat\\heugem_limmel_geul_midden\\rev3\\T25 4u ' \
     'droog\\gridadmin.h5 '
res = 'C:\\Users\\leendert.vanwolfswin\\Documents\\heugem-limmel\\resultaat\\heugem_limmel_geul_midden\\rev3\\T25 4u ' \
      'droog\\results_3di.nc '
gr = GridH5ResultAdmin(ga, res)

out_gis_file = 'C:\\Users\\leendert.vanwolfswin\\Documents\\LeakDetector\\test.gpkg'

# test line id = 63159, goede antwoord is ongeveer 76.17
# line_ids = list(gr.lines.subset('2D_OPEN_WATER').id)
line_ids = [63159]
ds = obstacle_info_to_ogr(dem=dem, gr=gr, line_ids=line_ids, search_precision=0.01, datasource_name='')
ogr_lyr = ds.GetLayerByName('obstacle_info')
print(ogr_lyr.GetFeatureCount())
ds = None
