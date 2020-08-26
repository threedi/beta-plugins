# TODO: 'Flowline with direction' styling ook width laten variëren afhankelijk van de klasse
# TODO: Legenda in layer tree ook updaten na triggerRepaint

import os
import numpy as np
from typing import List

from qgis.core import QgsMarkerSymbol, QgsExpression, QgsExpressionContext, QgsExpressionContextUtils

STYLE_DIR = os.path.join(os.path.dirname(__file__), 'style')


class Style:
    def __init__(self, name: str, output_type: str, params: dict, qml: str, styling_method):
        self.name = name
        assert output_type in ('flowline', 'node', 'cell', 'raster')
        self.output_type = output_type
        self.params = params
        if os.path.isabs(qml):
            self.qml = qml
        else:
            self.qml = os.path.join(STYLE_DIR, qml)
        if not os.path.isfile(self.qml):
            raise FileNotFoundError('QML file not found')
        self.styling_method = styling_method

    def apply(self, qgis_layer, style_kwargs):
        self.styling_method(qgis_layer, self.qml, **style_kwargs)


def style_on_single_column(layer, qml: str, column: str):
    layer.loadNamedStyle(qml)
    layer.renderer().setClassAttribute(column)
    layer.renderer().updateClasses(vlayer=layer,
                                   mode=layer.renderer().mode(),
                                   nclasses=len(layer.renderer().ranges()))
    layer.triggerRepaint()


def style_balance(layer, qml: str,
                  positive_col1: str,
                  positive_col2: str,
                  positive_col3: str,
                  negative_col1: str,
                  negative_col2: str,
                  negative_col3: str
                  ):
    layer.loadNamedStyle(qml)

    positive_columns = []
    negative_columns = []
    for col in [positive_col1, positive_col2, positive_col3]:
        if col != '':
            positive_columns.append(col)
    for col in [negative_col1, negative_col2, negative_col3]:
        if col != '':
            negative_columns.append(col)
    class_attribute_string = '({pos})-({neg})'.format(pos=' + '.join(positive_columns),
                                                      neg=' + '.join(negative_columns))
    layer.renderer().setClassAttribute(class_attribute_string)
    layer.renderer().deleteAllClasses()
    min_expression = QgsExpression('minimum({})'.format(class_attribute_string))
    max_expression = QgsExpression('maximum({})'.format(class_attribute_string))
    context = QgsExpressionContext()
    context.appendScopes(QgsExpressionContextUtils.globalProjectLayerScopes(layer))
    min_val = min_expression.evaluate(context)
    max_val = max_expression.evaluate(context)
    abs_max = max(abs(min_val), abs(max_val))
    class_bounds = list(np.arange(abs_max * -1, abs_max, ((abs_max - abs_max * -1) / 10.0)))
    class_bounds.append(abs_max)
    for i in range(len(class_bounds) - 1):
        layer.renderer().addClassLowerUpper(lower=class_bounds[i], upper=class_bounds[i + 1])
    color_ramp = layer.renderer().sourceColorRamp()
    layer.renderer().updateColorRamp(color_ramp)
    layer.triggerRepaint()


def style_as_vector(layer, qml: str, x: str, y: str):
    layer.loadNamedStyle(qml)

    # set data defined rotation
    rotation_expression = 'degrees(azimuth( make_point( 0,0), make_point( "{x}",  "{y}" )))'.format(x=x, y=y)
    data_defined_angle = QgsMarkerSymbol().dataDefinedAngle().fromExpression(rotation_expression)
    layer.renderer().sourceSymbol().setDataDefinedAngle(data_defined_angle)

    # update coloring
    class_attribute_string = 'sqrt("{x}" * "{x}" + "{y}" * "{y}")'.format(x=x, y=y)
    layer.renderer().setClassAttribute(class_attribute_string)
    layer.renderer().updateClasses(vlayer=layer,
                                   mode=layer.renderer().mode(),
                                   nclasses=len(layer.renderer().ranges()))

    layer.triggerRepaint()


def style_flow_direction(layer, qml: str, column: str):
    layer.loadNamedStyle(qml)

    # set data defined rotation
    rotation_expression = ' CASE WHEN "{}" < 0 \
                            THEN degrees(azimuth(start_point($geometry ), end_point($geometry))) + 90 \
                            ELSE degrees(azimuth(start_point(  $geometry ), end_point(  $geometry  ))) - 90 \
                            END'.format(column)
    data_defined_angle = QgsMarkerSymbol().dataDefinedAngle().fromExpression(rotation_expression)
    layer.renderer().sourceSymbol()[1].subSymbol().setDataDefinedAngle(data_defined_angle)

    # update coloring
    class_attribute_string = 'abs("{}")'.format(column)
    layer.renderer().setClassAttribute(class_attribute_string)
    layer.renderer().updateClasses(vlayer=layer,
                                   mode=layer.renderer().mode(),
                                   nclasses=len(layer.renderer().ranges()))

    layer.triggerRepaint()


def style_ts_reduction_analysis(layer, qml: str, col1: str, col2: str, col3: str):
    layer.loadNamedStyle(qml)
    filter_expression = '{col1} >10 or {col2} > 50 or {col3} > 80'.format(col1=col1, col2=col2, col3=col3)
    layer.renderer().rootRule().children()[0].setFilterExpression(filterExp=filter_expression)
    layer.triggerRepaint()


STYLE_FLOW_DIRECTION = Style(name='Flow direction',
                             output_type='flowline',
                             params={'column': 'column'},
                             qml='flow_direction.qml',
                             styling_method=style_flow_direction
                             )

STYLE_SINGLE_COLUMN_GRADUATED_FLOWLINE = Style(name='Single column graduated',
                                               output_type='flowline',
                                               params={'column': 'column'},
                                               qml='flowline.qml',
                                               styling_method=style_on_single_column)

STYLE_TIMESTEP_REDUCTION_ANALYSIS = Style(name='Timestep reduction analysis',
                                          output_type='flowline',
                                          params={'col1': 'column', 'col2': 'column', 'col3': 'column'},
                                          qml='ts_reduction_analysis.qml',
                                          styling_method=style_ts_reduction_analysis)

STYLE_SINGLE_COLUMN_GRADUATED_NODE = Style(name='Single column graduated',
                                           output_type='node',
                                           params={'column': 'column'},
                                           qml='node.qml',
                                           styling_method=style_on_single_column)

STYLE_VECTOR = Style(name='Vector',
                     output_type='node',
                     params={'x': 'column', 'y': 'column'},
                     qml='vector.qml',
                     styling_method=style_as_vector)

STYLE_SINGLE_COLUMN_GRADUATED_CELL = Style(name='Single column graduated',
                                           output_type='cell',
                                           params={'column': 'column'},
                                           qml='cell.qml',
                                           styling_method=style_on_single_column)

STYLE_BALANCE = Style(name='Balance',
                      output_type='cell',
                      params={'positive_col1': 'column',
                              'positive_col2': 'column',
                              'positive_col3': 'column',
                              'negative_col1': 'column',
                              'negative_col2': 'column',
                              'negative_col3': 'column',
                              },
                      qml='balance.qml',
                      styling_method=style_balance)

STYLES = [
    STYLE_FLOW_DIRECTION,
    STYLE_SINGLE_COLUMN_GRADUATED_FLOWLINE,
    STYLE_TIMESTEP_REDUCTION_ANALYSIS,
    STYLE_SINGLE_COLUMN_GRADUATED_NODE,
    STYLE_VECTOR,
    STYLE_SINGLE_COLUMN_GRADUATED_CELL,
    STYLE_BALANCE
]
