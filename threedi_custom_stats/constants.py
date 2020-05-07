import ogr
import numpy as np
# Python to Ogr data type conversions
NP_OGR_DTYPES = {np.dtype('float32'): ogr.OFTReal,
                 np.dtype('float64'): ogr.OFTReal,
                 np.dtype('int32'): ogr.OFTInteger,
                 np.dtype('int64'): ogr.OFTInteger64
                 }

# Pre resample methods
PRM_NONE = 0  # no processing before resampling (e.g. for water levels, velocities); divide by 1
PRM_SPLIT = 1  # split the original value over the new pixels; divide by (res_old/res_new)*2
PRM_1D = 2  # for flows (q) in x or y direction: scale with pixel resolution; divide by (res_old/res_new)


class AggregationList(list):
    def __init__(self):
        super().__init__()

    def as_dict(self, key, var_type = None):
        result = dict()
        for var in self:
            if var.var_type == var_type or var_type is None:
                if key == 'short':
                    result[var.short_name] = var.long_name
                elif key == 'long':
                    result[var.long_name] = var.short_name
        return result

    def short_names(self, var_types=None):
        result = list()
        for var in self:
            if var.var_type is None:
                result.append(var.short_name)
            elif var.var_type in var_types:
                result.append(var.short_name)
        return result

    def long_names(self, var_types=None):
        result = list()
        for var in self:
            if var.var_type is None:
                result.append(var.long_name)
            elif var.var_type in var_types:
                result.append(var.long_name)
        return result

    def get_by_short_name(self, short_name):
        for var in self:
            if var.short_name == short_name:
                return var

    def get_by_long_name(self, long_name):
        for var in self:
            if var.long_name == long_name:
                return var


class AggregationVariable:
    def __init__(self, short_name, long_name, signed: bool, applicable_methods: list, var_type: int, units: dict,
                 can_resample: bool, pre_resample_method: int = PRM_NONE):
        self.short_name = short_name
        self.long_name = long_name
        self.signed = signed
        self.var_type = var_type
        self.units = units
        self.applicable_methods = applicable_methods
        self.can_resample = can_resample
        self.pre_resample_method = pre_resample_method


class AggregationMethod:
    def __init__(self, short_name, long_name, has_threshold: bool = False,
                 integrates_over_time: bool = False, is_percentage: bool = False):
        self.short_name = short_name
        self.long_name = long_name
        self.has_threshold = has_threshold
        self.integrates_over_time = integrates_over_time
        self.is_percentage = is_percentage
        self.var_type = None


# Variable types
VT_FLOW = 0
VT_NODE = 1
VT_PUMP = 3
VT_FLOW_HYBRID = 10
VT_NODE_HYBRID = 20

VT_NAMES = {
    VT_FLOW: 'Flowline',
    VT_NODE: 'Node',
    VT_PUMP: 'Pump',
    VT_FLOW_HYBRID: 'Flowline',
    VT_NODE_HYBRID: 'Node'
}

# Aggregation methods
AGGREGATION_METHODS = AggregationList()

agg_method_list = [
    {'short_name': 'sum', 'long_name': 'Sum', 'integrates_over_time': True},
    {'short_name': 'max', 'long_name': 'Max'},
    {'short_name': 'min', 'long_name': 'Min'},
    {'short_name': 'mean', 'long_name': 'Mean'},
    {'short_name': 'median', 'long_name': 'Median'},
    {'short_name': 'first', 'long_name': 'First'},
    {'short_name': 'last', 'long_name': 'Last'},
    {'short_name': 'above_thres', 'long_name': '% of time above threshold', 'has_threshold': True, 'is_percentage': True},
    {'short_name': 'below_thres', 'long_name': '% of time below threshold', 'has_threshold': True, 'is_percentage': True}
]

for var in agg_method_list:
    AGGREGATION_METHODS.append(AggregationMethod(**var))

ALL_AGG_METHODS = list(AGGREGATION_METHODS.short_names())
ALL_AGG_METHODS_NO_SUM = list(AGGREGATION_METHODS.short_names())
ALL_AGG_METHODS_NO_SUM.remove('sum')

# Aggregation variables
agg_var_list = [
    {'short_name': 'q', 'long_name': 'Discharge', 'signed': True,
     'applicable_methods': ALL_AGG_METHODS, 'var_type': VT_FLOW, 'units': {('m3', 's'): (1, 1)},
     'can_resample':False, 'pre_resample_method':PRM_NONE},
    {'short_name': 'u', 'long_name':'Velocity', 'signed':True,
     'applicable_methods':ALL_AGG_METHODS_NO_SUM, 'var_type': VT_FLOW, 'units': {('m', 's'): (1, 1)},
     'can_resample':False, 'pre_resample_method':PRM_NONE},
    {'short_name': 'au', 'long_name': 'Wet crosssectional area', 'signed': False,
     'applicable_methods': ALL_AGG_METHODS_NO_SUM, 'var_type': VT_FLOW, 'units': {('m2',): (1,)},
     'can_resample': False, 'pre_resample_method': PRM_NONE},
    # NOT YET IMPLEMENTED (MY CODE) {'short_name': 'qp', 'long_name': 'Discharge in interflow layer', 'signed': True, 'applicable_methods': ALL_AGG_METHODS,'var_type': VT_FLOW, 'units':{('m3','s'):(1,1)}, 'can_resample': False, 'pre_resample_method': PRM_NONE},
    # NOT YET IMPLEMENTED (MY CODE) {'short_name': 'up1', 'long_name': 'Velocity in interflow layer', 'signed': True,'applicable_methods': ALL_AGG_METHODS_NO_SUM,'var_type': VT_FLOW, 'units':{('m','s'):(1,1)}, 'can_resample': False, 'pre_resample_method': PRM_NONE},
    {'short_name': 'ts_max', 'long_name': 'Max. possible timestep', 'signed': False,'applicable_methods': ALL_AGG_METHODS_NO_SUM,'var_type': VT_FLOW, 'units':{('s'):(1,)}, 'can_resample': False, 'pre_resample_method': PRM_NONE},
    # NOT YET IMPLEMENTED (MY CODE) {'short_name': 'q_pump', 'long_name': 'Pump discharge', 'signed': False, 'applicable_methods': ALL_AGG_METHODS, 'var_type': VT_PUMP,'units':{('m3','s'):(1, 1), ('m3', 'h'):(1, 3600), ('L','s'):(1000,1)}, 'can_resample': False, 'pre_resample_method': PRM_NONE},
    {'short_name': 's1', 'long_name': 'Water level', 'signed': False, 'applicable_methods': ALL_AGG_METHODS_NO_SUM, 'var_type': VT_NODE, 'units':{('m.a.s.l.',): (1,)}, 'can_resample': True, 'pre_resample_method': PRM_NONE},
    {'short_name': 'vol', 'long_name': 'Volume', 'signed': False, 'applicable_methods': ALL_AGG_METHODS_NO_SUM, 'var_type': VT_NODE, 'units':{('m3',): (1,)}, 'can_resample': True, 'pre_resample_method': PRM_SPLIT},
    {'short_name': 'rain', 'long_name': 'Rain intensity', 'signed': False, 'applicable_methods': ALL_AGG_METHODS, 'var_type': VT_NODE, 'units':{('m3', 's'):(1, 1), ('m3', 'h'):(1, 3600)}, 'can_resample': True, 'pre_resample_method': PRM_SPLIT},
    {'short_name': 'rain_depth', 'long_name': 'Rain depth', 'signed': False, 'applicable_methods': ALL_AGG_METHODS, 'var_type': VT_NODE, 'units':{('mm', 's'): (1000, 1), ('mm', 'h'): (1000, 3600)}, 'can_resample': True, 'pre_resample_method': PRM_NONE},
    # DOESNT WORK (THREEDIGRID) {'short_name': 'infiltration_rate', 'long_name': 'Infiltration rate', 'signed': False, 'applicable_methods': ALL_AGG_METHODS, 'var_type': VT_NODE, 'units':{('m3','s'):(1,1), ('m3','h'):(1,3600)}, 'can_resample': True, 'pre_resample_method': PRM_NONE},
    # DOESNT WORK (THREEDIGRID) {'short_name': 'infiltration_rate_mm', 'long_name': 'Infiltration rate per m2', 'signed': False, 'applicable_methods': ALL_AGG_METHODS, 'var_type': VT_NODE, 'units': {('mm', 's'): (1, 1), ('mm', 'h'): (1, 3600)}, 'can_resample': True, 'pre_resample_method': PRM_NONE},
    {'short_name': 'su', 'long_name': 'Wet surface area', 'signed': False, 'applicable_methods': ALL_AGG_METHODS_NO_SUM, 'var_type': VT_NODE, 'units': {('m2',): (1,)}, 'can_resample': False, 'pre_resample_method': PRM_NONE},
    # DOESNT WORK (THREEDIGRID) {'short_name': 'uc', 'long_name': 'Flow velocity at cell center', 'signed': False, 'applicable_methods': ALL_AGG_METHODS_NO_SUM, 'var_type': VT_NODE, 'units': {('m', 's'): (1, 1)}, 'can_resample': True, 'pre_resample_method': PRM_NONE},
    # DOESNT WORK (THREEDIGRID) {'short_name': 'ucx', 'long_name': 'Flow velocity in x direction at cell center', 'signed': True, 'applicable_methods': ALL_AGG_METHODS_NO_SUM, 'var_type': VT_NODE, 'units': {('m', 's'): (1, 1)}, 'can_resample': True, 'pre_resample_method': PRM_NONE},
    # DOESNT WORK (THREEDIGRID) {'short_name': 'ucy', 'long_name': 'Flow velocity in y direction at cell center', 'signed': True, 'applicable_methods': ALL_AGG_METHODS_NO_SUM, 'var_type': VT_NODE, 'units': {('m', 's'): (1, 1)}, 'can_resample': True, 'pre_resample_method': PRM_NONE},
    # NOT YET IMPLEMENTED (MY CODE) 'Flow direction in cell center': 'u_dir_cell', # moeilijk
    # 'Leakage' ???
    {'short_name': 'q_lat', 'long_name': 'Lateral discharge', 'signed': True,
     'applicable_methods': ALL_AGG_METHODS, 'var_type': VT_NODE, 'units': {('m3','s'): (1, 1)},
     'can_resample': True, 'pre_resample_method': PRM_SPLIT},
    {'short_name': 'q_lat_mm', 'long_name': 'Lateral discharge per m2', 'signed': True,
     'applicable_methods': ALL_AGG_METHODS, 'var_type': VT_NODE, 'units': {('mm', 's'): (1, 1), ('mm', 'h'): (1, 3600)},
     'can_resample': True, 'pre_resample_method': PRM_NONE},
    {'short_name': 'intercepted_volume', 'long_name': 'Intercepted volume', 'signed': False,
     'applicable_methods': ALL_AGG_METHODS, 'var_type': VT_NODE, 'units': {('m3',): (1,)},
     'can_resample': True, 'pre_resample_method': PRM_SPLIT},
    {'short_name': 'intercepted_volume_mm', 'long_name': 'Intercepted volume per m2', 'signed': False,
     'applicable_methods': ALL_AGG_METHODS, 'var_type': VT_NODE, 'units': {('mm',): (1,)},
     'can_resample': True, 'pre_resample_method': PRM_NONE},
    {'short_name': 'q_sss', 'long_name': 'Surface sources and sinks discharge', 'signed': True,
     'applicable_methods': ALL_AGG_METHODS, 'var_type': VT_NODE, 'units': {('m3', 's'): (1, 1)},
     'can_resample': True, 'pre_resample_method': PRM_SPLIT},
    {'short_name': 'q_sss_mm', 'long_name': 'Surface sources and sinks discharge per m2', 'signed': True,
     'applicable_methods': ALL_AGG_METHODS, 'var_type': VT_NODE, 'units': {('mm', 's'): (1, 1), ('mm', 'h'): (1, 3600)},
     'can_resample': True, 'pre_resample_method': PRM_NONE},
    {'short_name': 'q_in_x', 'long_name': 'Node inflow in x direction', 'signed': False,
     'applicable_methods': ALL_AGG_METHODS, 'var_type': VT_NODE_HYBRID, 'units': {('m3', 's'): (1, 1)},
     'can_resample': True, 'pre_resample_method': PRM_1D},
    {'short_name': 'q_in_y', 'long_name': 'Node inflow in y direction', 'signed': False,
     'applicable_methods': ALL_AGG_METHODS, 'var_type': VT_NODE_HYBRID, 'units': {('m3', 's'): (1, 1)},
     'can_resample': True, 'pre_resample_method': PRM_1D},
    {'short_name': 'q_out_x', 'long_name': 'Node outflow in x direction', 'signed': False,
     'applicable_methods': ALL_AGG_METHODS, 'var_type': VT_NODE_HYBRID, 'units': {('m3', 's'): (1, 1)},
     'can_resample': True, 'pre_resample_method': PRM_1D},
    {'short_name': 'q_out_y', 'long_name': 'Node outflow in y direction', 'signed': False,
     'applicable_methods': ALL_AGG_METHODS, 'var_type': VT_NODE_HYBRID, 'units': {('m3', 's'): (1, 1)},
     'can_resample': True, 'pre_resample_method': PRM_1D}
]

AGGREGATION_VARIABLES = AggregationList()

for var in agg_var_list:
    AGGREGATION_VARIABLES.append(AggregationVariable(**var))

# HYBRID_NODE_VARIABLES = {'Inflow': 'q_in',
#                          'Outflow': 'q_out',
#                          'Net flow': 'q_net'
#                          }
#
# HYBRID_FLOWLINE_VARIABLES = {'Gradient': 'dhdx'}
NA_TEXT = '[Not applicable]'
DIRECTION_SIGNS = {'Positive': 'pos', 'Negative': 'neg','Absolute': 'abs', 'Net': 'net', NA_TEXT: ''}

NON_TS_REDUCING_KCU = [3, 4, 51, 52, 53, 54, 55, 56, 57, 58, 150, 200, 300, 400, 500]
