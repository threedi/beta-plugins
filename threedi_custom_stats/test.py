from threedi_result_aggregation import *
from threedigrid.admin.gridresultadmin import GridH5ResultAdmin
from threedigrid.admin.gridresultadmin import GridH5AggregateResultAdmin

ga = "C:\\Users\\leendert.vanwolfswin\\Documents\\purmerend\\overhwere_opp\\70mm\\gridadmin.h5"
res = "C:\\Users\\leendert.vanwolfswin\\Documents\\purmerend\\overhwere_opp\\70mm\\results_3di.nc"
agg_res = "C:\\Users\\leendert.vanwolfswin\\Documents\\purmerend\\overhwere_opp\\70mm\\aggregate_results_3di.nc"

gr = GridH5ResultAdmin(ga, res)
gr_agg = GridH5ResultAdmin(ga, agg_res)
gr_agg.nodes._field_names
gr_agg.nodes.Meta.composite_fields.keys()
gr_agg.nodes.Meta.subset_fields.keys()
# nodes = list(gr.nodes.id)
# flow_per_node(gr=gr, node_ids=nodes, start_time=0, end_time=3600, out=True, aggregation_method=AGGREGATION_METHODS.get_by_short_name('sum'))
#
# # from threedigrid.admin.nodes.exporters import NodesOgrExporter
# # a = NodesOgrExporter(gr.nodes)
# # a.set_driver(driver_name='MEMORY', extension='')
# # a.save('', node_data=gr.nodes.data, target_epsg_code=28992)
#
# das = []
#
# # da4 = dict()
# # da4['variable'] = 'q_pos'
# # da4['method']='median'
# # da4['threshold'] = 0.0
# # das.append(da4)
# #
# # da4 = dict()
# # da4['variable'] = 'q_in_x'
# # da4['method']='sum'
# # da4['threshold'] = None
# # da4['sign'] = None
# # da4['multiplier'] = 1
# # das.append(da4)
# # #
# da = dict()
# da['variable'] = 'q_out_x'
# da['method']='sum'
# da['threshold'] = 0.0
# da['sign'] = 'pos'
# da['multiplier'] = 1
# das.append(da)
#
# da2 = dict()
# da2['variable'] = 'q_out_y'
# da2['method']='sum'
# da2['threshold'] = 0.0
# da2['sign'] = ''
# da2['multiplier'] = 1
# das.append(da2)
#
# print(das)
#
# #print(type(gr.lines))
# #print(gr.lines.filter(id__in=[23]).data['line_geometries'])
#
# bbox = [185746.2278, 320514.5504, 186318.2898, 320733.7015]
# # bbox= None
# # ca = custom_aggregation(gr=gr, variable='q_abs', method='sum', threshold=None,
# #                       bbox=None, start_time=None, end_time=None, subsets=None)


from threedi_result_aggregation import *

ga = "C:/Users/leendert.vanwolfswin/Documents/mead/rev6 45 mm 40mm per uur/gridadmin.h5"
res = "C:/Users/leendert.vanwolfswin/Documents/mead/rev6 45 mm 40mm per uur/results_3di.nc"

das = []

# das.append(Aggregation(variable=AGGREGATION_VARIABLES.get_by_short_name('q'),
#                        method=AGGREGATION_METHODS.get_by_short_name('sum'),
#                        sign=AggregationSign('net', 'Net')
#                        )
#            )

das.append(
    Aggregation(
        variable=AGGREGATION_VARIABLES.get_by_short_name("s1"),
        method=AGGREGATION_METHODS.get_by_short_name("first_non_empty"),
    )
)

ca, rast = aggregate_threedi_results(
    gridadmin=ga,
    results_3di=res,
    demanded_aggregations=das,
    interpolation_method="linear",
    resample_point_layer=False,
    output_flowlines=False,
    output_cells=False,
    output_rasters=False,
    output_nodes=True,
)

ogr_rsamplyr = ca.GetLayerByName("flowline")
if ogr_rsamplyr is not None:
    print(
        "flowline layer has {} features".format(ogr_rsamplyr.GetFeatureCount())
    )

# ogr_fllyr = ca.GetLayerByName('flowline')
# if ogr_fllyr is not None:
#     print('flowline layer has {} features'.format(ogr_fllyr.GetFeatureCount()))
ogr_nlyr = ca.GetLayerByName("node")
if ogr_nlyr is not None:
    print("node layer has {} features".format(ogr_nlyr.GetFeatureCount()))

# ogr_clyr = ca.GetLayerByName('cell')
# if ogr_clyr is not None:
#     print('cell layer has {} features'.format(ogr_clyr.GetFeatureCount()))
# ogr_rsamplyr = ca.GetLayerByName('node_resampled')
# if ogr_rsamplyr is not None:
#     print('resampled point layer has {} features'.format(ogr_rsamplyr.GetFeatureCount()))


# test resample_cell_layer
# src_ds = resample_cell_layer(ogr_clyr, 's1_max', [2,4,8,16,32], prm=PRM_NONE, pk='id')
# driver = gdal.GetDriverByName('GTiff')
# dst_ds = driver.CreateCopy('C:/Users/leendert.vanwolfswin/Documents/test_resample.tif', src_ds, strict=0)
# dst_ds = None
# src_ds = None

# print(len(ca['values']))
# print(gr.lines.count)
