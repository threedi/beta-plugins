from typing import Optional, List

# Pre resample methods
PRM_NONE = 0  # no processing before resampling (e.g. for water levels, velocities); divide by 1
PRM_SPLIT = 1  # split the original value over the new pixels; divide by (res_old/res_new)*2
PRM_1D = 2  # for flows (q) in x or y sign: scale with pixel resolution; divide by (res_old/res_new)

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


class AggregationVariableList(list):
    def __init__(self):
        super().__init__()

    def as_dict(self, key, var_type=None):
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


class AggregationSign:
    def __init__(self, short_name, long_name):
        self.short_name = short_name
        self.long_name = long_name


class AggregationMethod:
    def __init__(self, short_name, long_name, has_threshold: bool = False,
                 integrates_over_time: bool = False, is_percentage: bool = False):
        self.short_name = short_name
        self.long_name = long_name
        self.has_threshold = has_threshold
        self.integrates_over_time = integrates_over_time
        self.is_percentage = is_percentage
        self.var_type = None


NA_TEXT = '[Not applicable]'
AGGREGATION_SIGN_NA = AggregationSign(short_name='', long_name=NA_TEXT)


class Aggregation:
    def __init__(self, variable: AggregationVariable, method: AggregationMethod,
                 sign: Optional[AggregationSign] = AGGREGATION_SIGN_NA,
                 threshold: Optional[float] = None, multiplier: float = 1):
        assert isinstance(method, AggregationMethod)
        self.variable = variable
        self.sign = sign
        self.method = method
        self.threshold = threshold
        self.multiplier = multiplier

    def as_column_name(self):
        column_name_list = []
        try:
            column_name_list.append(self.variable.short_name)
            if self.variable.signed:
                column_name_list.append(self.sign.short_name)
            column_name_list.append(self.method.short_name)
            if self.method.short_name in ['above_thres', 'below_thres']:
                thres_parsed = str(self.threshold).replace('.', '_')
                column_name_list.append(thres_parsed)
            return '_'.join(column_name_list).lower()
        except AttributeError:
            return None


def filter_demanded_aggregations(das: List[Aggregation], variable_types):
    result = []
    for da in das:
        if da.variable.var_type in variable_types:
            result.append(da)
    return result

