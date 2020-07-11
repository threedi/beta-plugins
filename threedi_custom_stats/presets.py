from typing import List

try:
    from .aggregation_classes import *
    from .constants import *
except ImportError:
    from aggregation_classes import *
    from constants import *


class Preset:
    def __init__(self,
                 name: str,
                 aggregations: List[Aggregation] = [],
                 resample_point_layer: bool = False,
                 flowlines_styling_type: str = '',
                 cells_styling_type: str = '',
                 nodes_styling_type: str = ''
                 ):
        self.name = name
        self.__aggregations = aggregations
        self.resample_point_layer = resample_point_layer
        self.flowlines_styling_type = flowlines_styling_type
        self.cells_styling_type = cells_styling_type
        self.nodes_styling_type = nodes_styling_type

    def add_aggregation(self, aggregation: Aggregation):
        self.__aggregations.append(aggregation)

    def aggregations(self):
        return self.__aggregations

# No preset selected
NO_PRESET = Preset(name='(no preset selected)',
                   aggregations=[]
                   )

# Timestep reduction analysis
ts_reduction_analysis_aggregations = []
ts_reduction_analysis_aggregations.append(Aggregation(variable=AGGREGATION_VARIABLES.get_by_short_name('ts_max'),
                                                      method=AGGREGATION_METHODS.get_by_short_name('below_thres'),
                                                      threshold=1.0
                                                      )
                                          )
ts_reduction_analysis_aggregations.append(Aggregation(variable=AGGREGATION_VARIABLES.get_by_short_name('ts_max'),
                                                      method=AGGREGATION_METHODS.get_by_short_name('below_thres'),
                                                      threshold=3.0
                                                      )
                                          )
ts_reduction_analysis_aggregations.append(Aggregation(variable=AGGREGATION_VARIABLES.get_by_short_name('ts_max'),
                                                      method=AGGREGATION_METHODS.get_by_short_name('below_thres'),
                                                      threshold=5.0
                                                      )
                                          )
TS_REDUCTION_ANALYSIS_PRESETS = Preset(name='Timestep reduction analysis',
                                       aggregations=ts_reduction_analysis_aggregations,
                                       flowlines_styling_type='Timestep reduction analysis')


# Flow pattern
flow_pattern_aggregations = []
flow_pattern_aggregations.append(Aggregation(variable=AGGREGATION_VARIABLES.get_by_short_name('q_out_x'),
                                             method=AGGREGATION_METHODS.get_by_short_name('sum'),
                                             )
                                 )
flow_pattern_aggregations.append(Aggregation(variable=AGGREGATION_VARIABLES.get_by_short_name('q_out_y'),
                                             method=AGGREGATION_METHODS.get_by_short_name('sum'),
                                             )
                                 )
FLOW_PATTERN_PRESETS = Preset(name='Flow pattern',
                              aggregations=flow_pattern_aggregations,
                              resample_point_layer=True,
                              nodes_styling_type='Vector')

# Water balance per node (m3)
# Water balance per 2D cell (mm)
# Maximum water level

PRESETS = [NO_PRESET, FLOW_PATTERN_PRESETS, TS_REDUCTION_ANALYSIS_PRESETS]