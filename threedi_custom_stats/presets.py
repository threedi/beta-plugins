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
                 description: str = '',
                 aggregations: List[Aggregation] = [],
                 resample_point_layer: bool = False,
                 flowlines_styling_type: str = '',
                 cells_styling_type: str = '',
                 nodes_styling_type: str = ''
                 ):
        self.name = name
        self.description = description
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

# Maximum water level
max_wl_aggregations = [Aggregation(variable=AGGREGATION_VARIABLES.get_by_short_name('s1'),
                                   method=AGGREGATION_METHODS.get_by_short_name('max'),
                                   )
                       ]

MAX_WL_PRESETS = Preset(name='Maximum water level',
                        description='Calculates the maximum water level for nodes and cells within the chosen '
                                    'time filter.',
                        aggregations=max_wl_aggregations,
                        nodes_styling_type='Single column graduated')

# Flow pattern
flow_pattern_aggregations = [Aggregation(variable=AGGREGATION_VARIABLES.get_by_short_name('q_out_x'),
                                         method=AGGREGATION_METHODS.get_by_short_name('sum'),
                                         ),
                             Aggregation(variable=AGGREGATION_VARIABLES.get_by_short_name('q_out_y'),
                                         method=AGGREGATION_METHODS.get_by_short_name('sum'),
                                         )]
FLOW_PATTERN_PRESETS = Preset(name='Flow pattern',
                              description='Generates a flow pattern map. The aggregation calculates total outflow per '
                                          'node in x and y directions, resampled to grid_space. In the styling that is '
                                          'applied, the shade of blue and the rotation of the arrows are based on the '
                                          'resultant of these two.\n\n'
                                          'To save the output to disk, save to GeoPackage (Export > Save features as),'
                                          'copy the styling to the new layer (Styles > Copy Style / Paste Style). Then '
                                          'save the styling as default in the GeoPackage (Properties > Style > Save as '
                                          'Default > Save default style to Datasource Database). ',
                              aggregations=flow_pattern_aggregations,
                              resample_point_layer=True,
                              nodes_styling_type='Vector')

# Timestep reduction analysis
ts_reduction_analysis_aggregations = [Aggregation(variable=AGGREGATION_VARIABLES.get_by_short_name('ts_max'),
                                                  method=AGGREGATION_METHODS.get_by_short_name('below_thres'),
                                                  threshold=1.0
                                                  ),
                                      Aggregation(variable=AGGREGATION_VARIABLES.get_by_short_name('ts_max'),
                                                  method=AGGREGATION_METHODS.get_by_short_name('below_thres'),
                                                  threshold=3.0
                                                  ),
                                      Aggregation(variable=AGGREGATION_VARIABLES.get_by_short_name('ts_max'),
                                                  method=AGGREGATION_METHODS.get_by_short_name('below_thres'),
                                                  threshold=5.0
                                                  )]
TS_REDUCTION_ANALYSIS_PRESETS = Preset(name='Timestep reduction analysis',
                                       description='Timestep reduction analysis calculates the % of time that the flow '
                                                   'through each flowline limits the calculation timestep to below 1, 3, '
                                                   'or 5 seconds. \n\n'
                                                   'The styling highlights the flowlines that have a timestep of \n'
                                                   '    < 1 s for 10% of the time and/or\n'
                                                   '    < 3 s for 50% of the time and/or\n'
                                                   '    < 5 s for 80% of the time;'
                                                   '\n\n'
                                                   'Replacing these flowlines with orifices may speed up the simulation '
                                                   'without large impact on the results. Import the highlighted lines '
                                                   'from the aggregation result into your 3Di spatialite as '
                                                   '\'ts_reducers\' and use this query to replace line elements (example '
                                                   'for v2_pipe):\n\n'
                                                   '-- Add orifice:\n'
                                                   'INSERT INTO v2_orifice(display_name, code, crest_level, sewerage, '
                                                   'cross_section_definition_id, friction_value, friction_type, '
                                                   'discharge_coefficient_positive, discharge_coefficient_negative, '
                                                   'zoom_category, crest_type, connection_node_start_id, '
                                                   'connection_node_end_id)\n'
                                                    'SELECT display_name, code, max(invert_level_start_point, '
                                                   'invert_level_end_point) AS crest_level, TRUE AS sewerage, '
                                                   'cross_section_definition_id, friction_value, friction_type, '
                                                   '1 AS discharge_coefficient_positive, '
                                                   '1 AS discharge_coefficient_negative, zoom_category, 4 AS crest_type, '
                                                   'connection_node_start_id, connection_node_end_id\n'
                                                   'FROM v2_pipe\n'
                                                   'WHERE id IN (SELECT spatialite_id FROM ts_reducers WHERE '
                                                   'content_type=\'v2_pipe\');\n\n'
                                                   '-- Remove pipe\n'
                                                   'DELETE FROM v2_pipe WHERE id IN (SELECT spatialite_id FROM '
                                                   'ts_reducers WHERE content_type=''v2_pipe'');',
                                       aggregations=ts_reduction_analysis_aggregations,
                                       flowlines_styling_type='Timestep reduction analysis')

# Water balance per node (m3)
# Water balance per 2D cell (mm)


PRESETS = [NO_PRESET, MAX_WL_PRESETS, FLOW_PATTERN_PRESETS, TS_REDUCTION_ANALYSIS_PRESETS]
