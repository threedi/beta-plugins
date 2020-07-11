from threedi_result_aggregation import *
# from threedigrid.admin.gridresultadmin import GridH5ResultAdmin

# ga='C:\\Users\\leendert.vanwolfswin\\Documents\\sloterplas\\Sloterplas_vulkaanuitbarsting\\gridadmin.h5'
# res='C:\\Users\\leendert.vanwolfswin\\Documents\\sloterplas\\Sloterplas_vulkaanuitbarsting\\results_3di.nc'
# ga='C:\\Users\\leendert.vanwolfswin\\Documents\\bergeijk\\rev26\\Bui08\\gridadmin.h5'
# res='C:\\Users\\leendert.vanwolfswin\\Documents\\bergeijk\\rev26\\Bui08\\results_3di.nc'
ga= "C:/Users/leendert.vanwolfswin/Documents/heugem-limmel/resultaat/heugem_limmel_geul_midden/rev3/T25 4u droog/gridadmin.h5"
res= "C:/Users/leendert.vanwolfswin/Documents/heugem-limmel/resultaat/heugem_limmel_geul_midden/rev3/T25 4u droog/results_3di.nc"
gr = GridH5ResultAdmin(ga, res)
#
# from threedigrid.admin.nodes.exporters import NodesOgrExporter
# a = NodesOgrExporter(gr.nodes)
# a.set_driver(driver_name='MEMORY', extension='')
# a.save('', node_data=gr.nodes.data, target_epsg_code=28992)

das = []

# da4 = dict()
# da4['variable'] = 'q_pos'
# da4['method']='median'
# da4['threshold'] = 0.0
# das.append(da4)
#
# da4 = dict()
# da4['variable'] = 'q_in_x'
# da4['method']='sum'
# da4['threshold'] = None
# da4['sign'] = None
# da4['multiplier'] = 1
# das.append(da4)
# #
da = dict()
da['variable'] = 'q_out_x'
da['method']='sum'
da['threshold'] = 0.0
da['sign'] = 'pos'
da['multiplier'] = 1
das.append(da)

da2 = dict()
da2['variable'] = 'q_out_y'
da2['method']='sum'
da2['threshold'] = 0.0
da2['sign'] = ''
da2['multiplier'] = 1
das.append(da2)

print(das)

#print(type(gr.lines))
#print(gr.lines.filter(id__in=[23]).data['line_geometries'])

bbox = [185746.2278, 320514.5504, 186318.2898, 320733.7015]
# bbox= None
# ca = custom_aggregation(gr=gr, variable='q_abs', method='sum', threshold=None,
#                       bbox=None, start_time=None, end_time=None, subsets=None)

ca, rast = aggregate_threedi_results(gridadmin=ga,
                                     results_3di=res,
                                     demanded_aggregations=das,
                                     bbox=bbox,
                                     start_time=0,
                                     end_time=3600,
                                     interpolation_method='linear')
ogr_fllyr = ca.GetLayerByName('flowline')
if ogr_fllyr is not None:
    print('flowline layer has {} features'.format(ogr_fllyr.GetFeatureCount()))
ogr_nlyr = ca.GetLayerByName('node')
if ogr_nlyr is not None:
    print('node layer has {} features'.format(ogr_nlyr.GetFeatureCount()))
ogr_clyr = ca.GetLayerByName('cell')
if ogr_clyr is not None:
    print('cell layer has {} features'.format(ogr_clyr.GetFeatureCount()))
ogr_rsamplyr = ca.GetLayerByName('point_resampled')
if ogr_rsamplyr is not None:
    print('resampled point layer has {} features'.format(ogr_rsamplyr.GetFeatureCount()))


# test resample_cell_layer
# src_ds = resample_cell_layer(ogr_clyr, 's1_max', [2,4,8,16,32], prm=PRM_NONE, pk='id')
# driver = gdal.GetDriverByName('GTiff')
# dst_ds = driver.CreateCopy('C:/Users/leendert.vanwolfswin/Documents/test_resample.tif', src_ds, strict=0)
# dst_ds = None
# src_ds = None

# print(len(ca['values']))
# print(gr.lines.count)

