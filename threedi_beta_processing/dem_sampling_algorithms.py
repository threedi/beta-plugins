# -*- coding: utf-8 -*-

"""
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

from typing import (Any, Dict, Tuple, Union, List)

from osgeo import ogr
from osgeo import gdal
import numpy as np

from qgis.PyQt.QtCore import (QCoreApplication, QVariant)
from qgis.core import (
    NULL,
    QgsCoordinateTransform,
    QgsExpression,
    QgsFeature,
    QgsFeatureRequest,
    QgsFeatureSink,
    QgsField,
    QgsFields,
    QgsGeometry,
    QgsLineString,
    QgsMapLayer,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingContext,
    QgsProcessingFeatureSource,
    QgsProcessingMultiStepFeedback,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterNumber,
    QgsProcessingParameterRasterLayer,
    QgsProject,
    QgsRasterLayer,
    QgsVectorLayer
)
import processing

from .raster_tools.dem_sampler import AttributeProcessor

# Calculation types channel (taken from CalculationType in threedi_modelchecker.threedi_model.constants)
EMBEDDED = 100
STANDALONE = 101
CONNECTED = 102
DOUBLE_CONNECTED = 105

# Manhole indicator types
INSPECTION = 0

# cross section shapes (taken from CrossSectionShape in threedi_modelchecker.threedi_model.constants)
CLOSED_RECTANGLE = 0
RECTANGLE = 1
CIRCLE = 2
EGG = 3
TABULATED_RECTANGLE = 5
TABULATED_TRAPEZIUM = 6

ogr.UseExceptions()
gdal.UseExceptions()

def safe_float(val):
    try:
        return float(val)
    except (TypeError, ValueError):
        return np.nan

def cross_section_max_width(shape: int, width: float, table: str):
    if shape in [0, 1, 2, 3]:
        if width is None:
            raise ValueError(f'Invalid cross section: width is required for shape {shape}')
        return width
    elif shape in [5, 6]:
        try:
            max_width = 0
            height_width_pairs = table.split('\n')
            for height_width_pair in height_width_pairs:
                width_str = height_width_pair[1]
                width = float(width_str)
                if width > max_width:
                    max_width = width
            return max_width
        except Exception:
            raise ValueError(f'Invalid cross section table')
    else:
        raise ValueError(f'Unknown cross section shape: {shape}')


def add_float_field_if_not_exists(source: Union[QgsFeature, QgsProcessingFeatureSource], fieldname: str) -> tuple:
    """Return tuple of result_fields, result_field_idx, field_added"""
    result_fields = QgsFields(source.fields())
    if fieldname not in source.fields().names():
        field_added = True  # field does not exists, so value has to be filled for all features
        result_field = QgsField(
            name=fieldname,
            type=QVariant.Double,
            len=16,
            prec=3
        )
        result_fields.append(result_field)
    else:
        field_added = False
    result_field_idx = result_fields.indexFromName(fieldname)
    return result_fields, result_field_idx, field_added


class DemSamplerQgsConnector:
    """"Interface between dem_sampler.py and the QGIS API"""
    def __init__(self, raster: QgsRasterLayer, source: QgsProcessingFeatureSource, target_fieldname: str, width: float,
                 distance: float, overwrite: bool, inverse: bool = False, modify: bool = False, average: int = None):
        self.source = source
        self.target_fieldname = target_fieldname
        self.target_fields, self.target_field_idx, field_added = add_float_field_if_not_exists(
            source=source,
            fieldname=target_fieldname
        )
        self.overwrite = overwrite
        if field_added:
            self.overwrite = False

        self._get_features()

        dem_fn = raster.source()
        dem_ds = gdal.Open(dem_fn)
        self.processor = AttributeProcessor(
            raster=dem_ds,
            width=width,
            distance=distance,
            inverse=inverse,
            modify=modify,
            average=average
        )

        src_crs = source.sourceCrs()
        tgt_crs = raster.crs()
        self.coordinate_transform = QgsCoordinateTransform(src_crs, tgt_crs, QgsProject.instance())

    def _get_features(self):
        if self.overwrite:
            self.features = self.source.getFeatures()
        else:
            request = QgsFeatureRequest(QgsExpression(f'{self.target_fieldname} IS NULL'))
            self.features = self.source.getFeatures(request)

    def results(self, return_features: bool = True, left: bool = True, right: bool = True, search_distance_field: str = None):
        self._get_features()
        for feature in self.features:
            print(f'processing feature {feature.id()}')
            input_qgs_geometry = QgsGeometry(feature.geometry())
            if input_qgs_geometry.isEmpty():
                raise ValueError(f'Feature {feature.id()} has an empty geometry. Please fix or remove this feature and '
                                 f'try again.')
            input_qgs_geometry.transform(self.coordinate_transform)
            input_qgs_geometry_simple = input_qgs_geometry.simplify(0.01)
            input_wkb_geometry = input_qgs_geometry_simple.asWkb()
            input_ogr_geometry = ogr.Geometry(wkb=input_wkb_geometry)
            if search_distance_field:
                search_distance_field_idx = self.source.fields().indexFromName(search_distance_field)
                if search_distance_field_idx == -1:
                    raise ValueError(f'Invalid search_distance_field: source has no field {search_distance_field}')
                distance_override = feature[search_distance_field_idx]
            else:
                distance_override = None
            processed_features = self.processor.process(
                source_geometry=input_ogr_geometry,
                left=left,
                right=right,
                distance_override=distance_override
            )
            for output_ogr_geometry, crest_level in processed_features:
                if not return_features:
                    yield crest_level
                else:
                    result_feature = QgsFeature()
                    result_feature.setFields(self.target_fields)
                    for idx, value in enumerate(feature.attributes()):
                        result_feature.setAttribute(idx, value)
                    if not np.isnan(crest_level):
                        result_feature[self.target_field_idx] = float(crest_level)

                    output_wkb_geometry = output_ogr_geometry.ExportToWkb()
                    output_qgs_geometry = QgsGeometry()
                    output_qgs_geometry.fromWkb(output_wkb_geometry)
                    output_qgs_geometry.transform(self.coordinate_transform, QgsCoordinateTransform.ReverseTransform)
                    result_feature.setGeometry(output_qgs_geometry)

                    yield result_feature


class CrestLevelAlgorithm(QgsProcessingAlgorithm):
    """
    Estimate crest level from sampling the DEM perpendicular to the input lines
    """
    OUTPUT = 'OUTPUT'
    OBSTACLE_LINES = 'OBSTACLE_LINES'
    OVERWRITE_VALUES = 'OVERWRITE_VALUES'
    SEARCH_DISTANCE = 'SEARCH_DISTANCE'
    MIN_CREST_WIDTH = 'MIN_CREST_WIDTH'
    DEM = 'DEM'

    TARGET_FIELDNAME = 'crest_level'

    def initAlgorithm(self, config):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.OBSTACLE_LINES,
                self.tr('Obstacle lines layer'),
                [QgsProcessing.TypeVectorLine]
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.OVERWRITE_VALUES,
                self.tr('Overwrite existing values')
            )
        )

        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.DEM,
                self.tr('Digital Elevation Model')
            )
        )

        param = QgsProcessingParameterNumber(
                self.SEARCH_DISTANCE,
                self.tr('Search distance [m]'),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=10.0,
                minValue=0.0
        )
        param.setMetadata({'widget_wrapper': {'decimals': 2}})
        param.toolTip = 'Search distance for finding crest height in the DEM perpendicular to input line'
        self.addParameter(param)

        param = QgsProcessingParameterNumber(
                self.MIN_CREST_WIDTH,
                self.tr('Minimum crest width [m]'),
                type=QgsProcessingParameterNumber.Double,
                optional=True,
                minValue=0.0
        )
        param.setMetadata({'widget_wrapper': {'decimals': 2}})
        self.addParameter(param)

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Crest level')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(parameters, self.OBSTACLE_LINES, context)
        qgs_raster_layer = self.parameterAsRasterLayer(parameters, self.DEM, context)

        dem_sampler = DemSamplerQgsConnector(raster=qgs_raster_layer, source=source,
                                             target_fieldname=self.TARGET_FIELDNAME,
                                             width=self.parameterAsDouble(parameters, self.MIN_CREST_WIDTH, context),
                                             distance=self.parameterAsDouble(parameters, self.SEARCH_DISTANCE, context),
                                             overwrite=self.parameterAsBoolean(parameters, self.OVERWRITE_VALUES,
                                                                               context))

        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            dem_sampler.target_fields,
            source.wkbType(),
            source.sourceCrs()
        )

        total = 100.0 / source.featureCount() if source.featureCount() else 0

        for current, feature in enumerate(dem_sampler.results()):
            if feedback.isCanceled():
                break
            sink.addFeature(feature, QgsFeatureSink.FastInsert)

            feedback.setProgress(int(current * total))

        return {self.OUTPUT: dest_id}

    def supportInPlaceEdit(self, layer: QgsMapLayer):
        if isinstance(layer, QgsVectorLayer):
            if self.TARGET_FIELDNAME in layer.fields().names():
                return True
        return False

    def flags(self):
        return super().flags() | QgsProcessingAlgorithm.FlagSupportsInPlaceEdits

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'crest_level'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Crest level for linear obstacle')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr(self.groupId())

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'DEM Sampling'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return CrestLevelAlgorithm()


class MaxBreachDepthAlgorithm(QgsProcessingAlgorithm):
    """
    Estimate crest level from sampling the DEM perpendicular to the input lines
    """
    OUTPUT = 'OUTPUT'
    OBSTACLE_LINES = 'OBSTACLE_LINES'
    OVERWRITE_VALUES = 'OVERWRITE_VALUES'
    SEARCH_DISTANCE = 'SEARCH_DISTANCE'
    MIN_DEPRESSION_WIDTH = 'MIN_DEPRESSION_WIDTH'
    DEM = 'DEM'

    TARGET_FIELDNAME = 'max_breach_depth'

    def initAlgorithm(self, config):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.OBSTACLE_LINES,
                self.tr('Levee lines layer'),
                [QgsProcessing.TypeVectorLine]
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.OVERWRITE_VALUES,
                self.tr('Overwrite existing values')
            )
        )

        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.DEM,
                self.tr('Digital Elevation Model')
            )
        )

        param = QgsProcessingParameterNumber(
                self.SEARCH_DISTANCE,
                self.tr('Search distance [m]'),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=10.0,
                minValue=0.0
        )
        param.setMetadata({'widget_wrapper': {'decimals': 2}})
        param.toolTip = 'Search distance for finding minima in the DEM perpendicular to input line'
        self.addParameter(param)

        param = QgsProcessingParameterNumber(
                self.MIN_DEPRESSION_WIDTH,
                self.tr('Minimum depression width [m]'),
                type=QgsProcessingParameterNumber.Double,
                optional=True,
                minValue=0.0
        )
        param.setMetadata({'widget_wrapper': {'decimals': 2}})
        self.addParameter(param)

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Max breach depth')
            )
        )

    def checkParameterValues(self, parameters: Dict[str, Any], context: QgsProcessingContext) -> Tuple[bool, str]:
        success, msg = super().checkParameterValues(parameters, context)
        if success:
            msg_list = list()
            source = self.parameterAsSource(parameters, self.OBSTACLE_LINES, context)
            if 'crest_level' not in source.fields().names():
                msg_list.append('Obstacle lines layer does not contain crest_level field')
            success = len(msg_list) == 0
            msg = '; '.join(msg_list)
        return success, msg

    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(parameters, self.OBSTACLE_LINES, context)
        crest_level_field_idx = source.fields().indexFromName('crest_level')

        qgs_raster_layer = self.parameterAsRasterLayer(parameters, self.DEM, context)

        dem_sampler = DemSamplerQgsConnector(raster=qgs_raster_layer, source=source,
                                             target_fieldname=self.TARGET_FIELDNAME,
                                             width=self.parameterAsDouble(parameters, self.MIN_DEPRESSION_WIDTH,
                                                                          context),
                                             distance=self.parameterAsDouble(parameters, self.SEARCH_DISTANCE, context),
                                             overwrite=self.parameterAsBoolean(parameters, self.OVERWRITE_VALUES,
                                                                               context), inverse=True)

        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            dem_sampler.target_fields,
            source.wkbType(),
            source.sourceCrs()
        )

        total = 100.0 / source.featureCount() if source.featureCount() else 0

        for current, feature in enumerate(dem_sampler.results()):
            if feedback.isCanceled():
                break

            crest_level = feature[crest_level_field_idx]
            depression_level = feature[dem_sampler.target_field_idx]
            feature[dem_sampler.target_field_idx] = crest_level - depression_level

            sink.addFeature(feature, QgsFeatureSink.FastInsert)

            feedback.setProgress(int(current * total))

        return {self.OUTPUT: dest_id}

    def supportInPlaceEdit(self, layer: QgsMapLayer):
        if isinstance(layer, QgsVectorLayer):
            if self.TARGET_FIELDNAME in layer.fields().names():
                return True
        return False

    def flags(self):
        return super().flags() | QgsProcessingAlgorithm.FlagSupportsInPlaceEdits

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'max_breach_depth'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Max breach depth')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr(self.groupId())

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'DEM Sampling'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return MaxBreachDepthAlgorithm()


class BankLevelAlgorithm(QgsProcessingAlgorithm):
    """
    Estimate bank level from sampling the DEM perpendicular to the input lines
    """
    # TODO add option to limit search_distance to max width of cross section
    CROSS_SECTION_LOCATIONS = 'CROSS_SECTION_LOCATIONS'
    OVERWRITE_VALUES = 'OVERWRITE_VALUES'
    CHANNELS = 'CHANNELS'
    CONNECTED_ONLY = 'CONNECTED_ONLY'
    DEM = 'DEM'
    EXTRA_SEARCH_DISTANCE = 'EXTRA_SEARCH_DISTANCE'
    MIN_CREST_WIDTH = 'MIN_CREST_WIDTH'
    MAX_SEGMENT_LENGTH = 'MAX_SEGMENT_LENGTH'
    OUTPUT = 'OUTPUT'

    SEARCH_DISTANCE_FIELDNAME = 'search_distance'
    TARGET_FIELDNAME = 'bank_level'

    def initAlgorithm(self, config):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.CROSS_SECTION_LOCATIONS,
                self.tr('Cross section location layer'),
                [QgsProcessing.TypeVectorPoint]
            )
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.OVERWRITE_VALUES,
                self.tr('Overwrite existing values')
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.CHANNELS,
                self.tr('Channel layer'),
                [QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.CONNECTED_ONLY,
                self.tr("'Connected' calculation type only")
            )
        )
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.DEM,
                self.tr('Digital Elevation Model')
            )
        )
        param = QgsProcessingParameterNumber(
                self.EXTRA_SEARCH_DISTANCE,
                self.tr('Extra search distance [m]'),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=0.0,
                minValue=0.0
        )
        param.setMetadata({'widget_wrapper': {'decimals': 2}})
        param.toolTip = 'Search distance for finding maxima in the DEM perpendicular to channel'
        self.addParameter(param)

        param = QgsProcessingParameterNumber(
                self.MAX_SEGMENT_LENGTH,
                self.tr('Maximum channel segment length [m]'),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=10.0,
                minValue=0.0
        )
        param.setMetadata({'widget_wrapper': {'decimals': 2}})
        self.addParameter(param)

        param = QgsProcessingParameterNumber(
                self.MIN_CREST_WIDTH,
                self.tr('Minimum crest width [m]'),
                type=QgsProcessingParameterNumber.Double,
                optional=True,
                minValue=0.0
        )
        param.setMetadata({'widget_wrapper': {'decimals': 2}})
        self.addParameter(param)

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Bank level')
            )
        )

    def checkParameterValues(self, parameters: Dict[str, Any], context: QgsProcessingContext) -> Tuple[bool, str]:
        success, msg = super().checkParameterValues(parameters, context)
        if success:
            msg_list = list()
            cross_section_locations_source = self.parameterAsSource(parameters, self.CROSS_SECTION_LOCATIONS, context)
            channels_source = self.parameterAsVectorLayer(parameters, self.CHANNELS, context)
            if 'channel_id' not in cross_section_locations_source.fields().names():
                msg_list.append("Cross section location layer does not have 'channel_id' field")
            if 'id' not in channels_source.fields().names():
                msg_list.append("Channel layer does not have 'id' field")
            success = len(msg_list) == 0
            msg = '; '.join(msg_list)
        return success, msg

    def processAlgorithm(self, parameters, context, feedback):
        qgs_project = QgsProject.instance()

        # convert parameters
        cross_section_locations_source = self.parameterAsSource(parameters, self.CROSS_SECTION_LOCATIONS, context)
        cross_section_locations_layer = self.parameterAsVectorLayer(parameters, self.CROSS_SECTION_LOCATIONS, context)
        overwrite = self.parameterAsBoolean(parameters, self.OVERWRITE_VALUES, context)
        channels_layer = self.parameterAsVectorLayer(parameters, self.CHANNELS, context)
        connected_only = self.parameterAsBoolean(parameters, self.CONNECTED_ONLY, context)
        dem_layer = self.parameterAsRasterLayer(parameters, self.DEM, context)
        extra_search_distance = self.parameterAsDouble(parameters, self.EXTRA_SEARCH_DISTANCE, context)
        min_crest_width = self.parameterAsDouble(parameters, self.MIN_CREST_WIDTH, context)
        max_segment_length = self.parameterAsDouble(parameters, self.MAX_SEGMENT_LENGTH, context)

        target_fields, target_field_idx, field_added = add_float_field_if_not_exists(
            source=cross_section_locations_source,
            fieldname=self.TARGET_FIELDNAME
        )
        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            target_fields,
            cross_section_locations_source.wkbType(),
            cross_section_locations_source.sourceCrs()
        )

        cross_section_locations_id_field_idx = cross_section_locations_layer.fields().indexFromName('id')
        cross_section_locations_channel_id_field_idx = cross_section_locations_layer.fields().indexFromName('channel_id')
        cross_section_shape_field_idx = cross_section_locations_layer.fields().indexFromName('shape')
        cross_section_width_field_idx = cross_section_locations_layer.fields().indexFromName('width')
        cross_section_table_field_idx = cross_section_locations_layer.fields().indexFromName('table')
        cross_section_definition_available = (
                cross_section_shape_field_idx != -1 and
                cross_section_width_field_idx != -1 and
                cross_section_table_field_idx != -1
        )
        if not cross_section_definition_available:
            msg = f"Warning: No cross section definition attributes found in cross section location layer. Using " \
                  f"'Extra search distance' ({extra_search_distance}) as search distance"
            feedback.pushWarning(msg)
        cross_section_locations_coordinate_transform = QgsCoordinateTransform(
            cross_section_locations_source.sourceCrs(),
            dem_layer.dataProvider().crs(),
            qgs_project
        )

        channels_id_field_idx = channels_layer.fields().indexFromName('id')
        calculation_type_field_idx = channels_layer.fields().indexFromName('calculation_type')
        channels_coordinate_transform = QgsCoordinateTransform(
            channels_layer.sourceCrs(),
            dem_layer.dataProvider().crs(),
            qgs_project
        )

        cross_section_location_id_field = QgsField(name='cross_section_location_id', type=QVariant.Int)
        search_distance_field = QgsField(name=self.SEARCH_DISTANCE_FIELDNAME, type=QVariant.Double)
        cross_section_location_bank_level_field = QgsField(name=self.TARGET_FIELDNAME, type=QVariant.Double)

        # create (temp) channel segment layer to sample dem
        crs = dem_layer.dataProvider().crs()
        uri = f"linestring?crs={crs.authid()}&field=cross_section_location_id:integer&field={self.SEARCH_DISTANCE_FIELDNAME}:double"
        if not field_added:
            uri += f'&field={self.TARGET_FIELDNAME}:double'
        bank_level_sample_layer = QgsVectorLayer(uri, "Bank level sample layer", "memory")

        # create channel segment features
        bank_level_sample_layer.startEditing()
        bank_level_sample_features = []
        channel_ids = [str(feature[cross_section_locations_channel_id_field_idx])
                       for feature in cross_section_locations_source.getFeatures()]
        channel_ids_str = ','.join(channel_ids)
        request = QgsFeatureRequest(QgsExpression(f'id IN ({channel_ids_str})'))
        if calculation_type_field_idx != -1 and connected_only:
            request.combineFilterExpression(f'calculation_type IN ({CONNECTED}, {DOUBLE_CONNECTED})')
        for channel in channels_layer.getFeatures(request):
            channel_id = channel[channels_id_field_idx]
            channel_geom = channel.geometry()
            channel_geom.transform(channels_coordinate_transform)
            for part in channel_geom.parts():  # get QgsLineString from QgsGeometry
                channel_geom_part = part
            request = QgsFeatureRequest(QgsExpression(f'channel_id = {channel_id}'))
            cross_section_locations = cross_section_locations_source.getFeatures(request)
            positions = []
            for cross_section_location in cross_section_locations:
                cross_section_location_fid = cross_section_location.id()
                if cross_section_locations_id_field_idx != -1:
                    cross_section_location_id = cross_section_location[cross_section_locations_id_field_idx]
                if cross_section_definition_available:
                    shape = cross_section_location[cross_section_shape_field_idx]
                    width = cross_section_location[cross_section_width_field_idx]
                    table = cross_section_location[cross_section_table_field_idx]
                    search_distance = cross_section_max_width(
                        shape=shape,
                        width=width,
                        table=table
                    ) + extra_search_distance
                else:
                    search_distance = extra_search_distance
                cross_section_location_geom = cross_section_location.geometry()
                cross_section_location_geom.transform(cross_section_locations_coordinate_transform)
                if cross_section_location_geom.distance(channel_geom) > 0.1:
                    # cross section location should intersect channel, so this is already a large tolerance
                    if cross_section_locations_id_field_idx == -1:
                        msg = f'Warning: A cross section location with channel_id {channel_id} is not located on that' \
                              f' channel'
                    else:
                        msg = f'Warning: Cross section location with id {cross_section_location_id} referring to ' \
                              f'channel with id {channel_id} is not located on that channel'
                    feedback.pushWarning(msg)
                    continue
                position = channel_geom.lineLocatePoint(cross_section_location_geom)
                position_plus_attr = [position, cross_section_location_fid]
                if not field_added:
                    cross_section_location_bank_level = cross_section_location[target_field_idx]
                    position_plus_attr.append(cross_section_location_bank_level)
                positions.append(position_plus_attr)
            if len(positions) == 0:
                feedback.pushWarning(f'Warning: No referenced cross section locations found on channel with id'
                                     f' {channel_id}')
                continue
            positions.sort()
            positions_array = np.array(positions)
            in_betweens = np.mean([positions_array[0:-1, 0], positions_array[1:, 0]], axis=0)
            cut_positions = np.concatenate([[0], in_betweens, [channel_geom_part.length()]])
            for i in range(len(cut_positions) - 1):
                bank_level_sample_feature_fields = QgsFields()
                if not bank_level_sample_feature_fields.append(cross_section_location_id_field):  # 0
                    raise Exception('Failed to add cross_section_location_id_field to bank_level_sample_feature_fields')
                if not bank_level_sample_feature_fields.append(search_distance_field):  # 1
                    raise Exception('Failed to add search_distance_field to bank_level_sample_feature_fields')
                if not field_added:
                    if not bank_level_sample_feature_fields.append(cross_section_location_bank_level_field):  # 2
                        raise Exception('Failed to add cross_section_location_bank_level_field to '
                                        'bank_level_sample_feature_fields')
                bank_level_sample_feature = QgsFeature()
                bank_level_sample_feature.setFields(bank_level_sample_feature_fields)
                cross_section_location_position, cross_section_location_fid = positions[i][0:2]
                bank_level_sample_feature[0] = cross_section_location_fid
                bank_level_sample_feature[1] = search_distance
                if not field_added:
                    bank_level_sample_feature[2] = positions[i][2]
                cut_position_start = max(cut_positions[i], cross_section_location_position - (max_segment_length/2))
                cut_position_end = min(cut_positions[i+1], cross_section_location_position + (max_segment_length/2))
                bank_level_sample_geom = channel_geom_part.curveSubstring(cut_position_start, cut_position_end)
                bank_level_sample_feature.setGeometry(bank_level_sample_geom)
                bank_level_sample_features.append(bank_level_sample_feature)
        if not bank_level_sample_layer.addFeatures(bank_level_sample_features):
            raise Exception('Failed to add features to bank_level_sample_layer')
        bank_level_sample_layer.commitChanges()

        dem_sampler = DemSamplerQgsConnector(raster=dem_layer, source=bank_level_sample_layer,
                                             target_fieldname=self.TARGET_FIELDNAME, width=min_crest_width,
                                             distance=extra_search_distance, overwrite=overwrite)

        total = 100.0 / cross_section_locations_source.featureCount() if cross_section_locations_source.featureCount() else 0

        crest_levels_left = list()
        # crest level on left side of the sample line
        for i, crest_level in enumerate(dem_sampler.results(
                return_features=False,
                left=True,
                right=False,
                search_distance_field=self.SEARCH_DISTANCE_FIELDNAME
        )):
            if feedback.isCanceled():
                break
            crest_levels_left.append(crest_level)
            feedback.setProgress(int(i/2 * total))

        # crest level on right side of the sample line
        crest_level_fid_dict = dict()
        for i, feature in enumerate(dem_sampler.results(
                return_features=True,
                left=False,
                right=True,
                search_distance_field=self.SEARCH_DISTANCE_FIELDNAME
        )):
            if feedback.isCanceled():
                break
            right_val = feature.attribute(dem_sampler.target_field_idx)
            left_val = crest_levels_left[i]

            crest_level_right = safe_float(right_val)
            crest_level_left = safe_float(left_val)

            crest_level_fid_dict[feature.id()] = float(np.nanmin([crest_level_right, crest_level_left]))

            feedback.setProgress(50 + int(i/2 * total))

        for source_feature in cross_section_locations_layer.getFeatures():
            sink_feature = QgsFeature()
            sink_feature.setFields(target_fields)
            for idx, value in enumerate(source_feature.attributes()):
                sink_feature.setAttribute(idx, value)
            try:
                if not np.isnan(crest_level_fid_dict[source_feature.id()]):
                    sink_feature[target_field_idx] = float(round(crest_level_fid_dict[source_feature.id()], 3))
            except KeyError:
                pass
            sink_geom = QgsGeometry(source_feature.geometry())
            sink_feature.setGeometry(sink_geom)

            sink.addFeature(sink_feature, QgsFeatureSink.FastInsert)

        return {self.OUTPUT: dest_id}

    def supportInPlaceEdit(self, layer: QgsMapLayer):
        if isinstance(layer, QgsVectorLayer):
            if self.TARGET_FIELDNAME in layer.fields().names():
                return True
        return False

    def flags(self):
        return super().flags() | QgsProcessingAlgorithm.FlagSupportsInPlaceEdits

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'bank_level'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Bank level')

    def shortHelpString(self):
        # TODO: implement helpUrl() when documentation is available online and prune this description
        help_string = "Derive the bank level of cross section locations from a Digital Elevation Model. \n\n" \
        "To update your 3Di schematisation directly with this algorithm, use the 'Edit features in-place' option in the " \
        "Processing Toolbox, click on the Cross Section Location layer in the Layer Panel, then start the algorithm. " \
        "\n\n" \
        "On both sides of the channel the maximum height is determined and the bank level is set to the lowest of " \
        "these two maxima. The maxima are determined by searching for maximum values in the DEM along a segment of the " \
        "channel, within 'Search distance' from that segment. The length of the segment is at most the 'Maximum channel" \
        " segment length', but may be shorter if the cross section is located near the start or end of the channel or " \
        "near another cross section." \
        "\n\n" \
        "The minimum crest width can be set to ignore narrow crests (outliers) that the algorithm encounters within " \
        "search distance from the channel." \
        "\n\n" \
        "You may limit processing to cross section locations that are located on channels with calculation type " \
        "'Connected' only, because the bank level is not relevant for channels with other calculation types." \
        "\n\n" \
        "By default, only those features are processed that have an empty bank level field. Check the box 'Overwrite " \
        "existing values' to change this behaviour."

        return self.tr(help_string)

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr(self.groupId())

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'DEM Sampling'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return BankLevelAlgorithm()


class DrainLevelAlgorithm(QgsProcessingAlgorithm):
    """
    Estimate drain level by finding the minimum value in the DEM in a buffer of specified width around the input point
    """
    OUTPUT = 'OUTPUT'
    INPUT_POINTS = 'INPUT_POINTS'
    OVERWRITE_VALUES = 'OVERWRITE_VALUES'
    CONNECTED_ONLY = 'CONNECTED_ONLY'
    INSPECTION_ONLY = 'INSPECTION_ONLY'
    SEARCH_DISTANCE = 'SEARCH_DISTANCE'
    DEM = 'DEM'

    TARGET_FIELDNAME = 'drain_level'

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_POINTS,
                self.tr('Manholes'),
                [QgsProcessing.TypeVectorPoint]
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.OVERWRITE_VALUES,
                self.tr('Overwrite existing values')
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.CONNECTED_ONLY,
                self.tr("'Connected' calculation type only"),
                defaultValue=True
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.INSPECTION_ONLY,
                self.tr("'Inspection' manhole indicator only"),
                defaultValue=True
            )
        )

        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.DEM,
                self.tr('Digital Elevation Model')
            )
        )

        param = QgsProcessingParameterNumber(
                self.SEARCH_DISTANCE,
                self.tr('Search distance [m]'),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=10.0,
                minValue=0.0
        )
        param.setMetadata({'widget_wrapper': {'decimals': 2}})
        param.toolTip = 'Search distance for finding minimum value in DEM around manhole'
        self.addParameter(param)

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Drain level')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        feedback = QgsProcessingMultiStepFeedback(3, feedback)

        source = self.parameterAsSource(parameters, self.INPUT_POINTS, context)
        source_layer = self.parameterAsVectorLayer(parameters, self.INPUT_POINTS, context)
        distance = self.parameterAsDouble(parameters, self.SEARCH_DISTANCE, context)
        overwrite = self.parameterAsBoolean(parameters, self.OVERWRITE_VALUES, context)
        connected_only = self.parameterAsBoolean(parameters, self.CONNECTED_ONLY, context)
        inspection_only = self.parameterAsBoolean(parameters, self.INSPECTION_ONLY, context)

        target_fields, target_field_idx, field_added = add_float_field_if_not_exists(
            source=source,
            fieldname=self.TARGET_FIELDNAME
        )
        calculation_type_field_idx = source.fields().indexFromName('calculation_type')
        manhole_indicator_field_idx = source.fields().indexFromName('manhole_indicator')

        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            target_fields,
            source.wkbType(),
            source.sourceCrs()
        )

        # Buffer
        alg_params = {
            'DISSOLVE': False,
            'DISTANCE': distance,
            'END_CAP_STYLE': 0,
            'INPUT': parameters[self.INPUT_POINTS],
            'JOIN_STYLE': 0,
            'MITER_LIMIT': 2,
            'SEGMENTS': 5,
            'OUTPUT': 'TEMPORARY_OUTPUT'
        }
        buffer_run = processing.run('native:buffer', alg_params, context=context, feedback=feedback,
                                    is_child_algorithm=True)
        buffered = buffer_run['OUTPUT']

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return

        # Zonal statistics (in place)
        alg_params = {
            'COLUMN_PREFIX': 'stats_',
            'INPUT_RASTER': parameters['DEM'],
            'INPUT_VECTOR': buffered,
            'RASTER_BAND': 1,
            'STATISTICS': [5]  # 5 = MIN
        }

        processing.run(
            'native:zonalstatistics',
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True
        )

        zonal_statistics_output_layer = context.getMapLayer(buffered)
        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return

        total = 100.0 / source.featureCount() if source.featureCount() else 0
        for current, feature in enumerate(zonal_statistics_output_layer.getFeatures()):

            if feedback.isCanceled():
                break

            source_feature = source_layer.getFeature(feature.id())
            output_feature = QgsFeature()
            output_feature.setFields(target_fields)

            for idx, value in enumerate(source_feature.attributes()):
                output_feature.setAttribute(idx, value)

            skip = False
            if overwrite and output_feature[target_field_idx] != NULL:
                skip = True
            if calculation_type_field_idx != -1:
                if output_feature[calculation_type_field_idx] not in (CONNECTED, DOUBLE_CONNECTED) and connected_only:
                    skip = True
            if manhole_indicator_field_idx != -1:
                if output_feature[manhole_indicator_field_idx] != INSPECTION and inspection_only:
                    skip = True

            if not skip:
                output_feature[target_field_idx] = feature['stats_min']
            geom = QgsGeometry(source_feature.geometry())
            output_feature.setGeometry(geom)

            sink.addFeature(output_feature, QgsFeatureSink.FastInsert)

            feedback.setProgress(int(current * total))

        return {self.OUTPUT: dest_id}

    def supportInPlaceEdit(self, layer: QgsMapLayer):
        if isinstance(layer, QgsVectorLayer):
            if self.TARGET_FIELDNAME in layer.fields().names():
                return True
        return False

    def flags(self):
        return super().flags() | QgsProcessingAlgorithm.FlagSupportsInPlaceEdits

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'drain_level'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Drain level')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr(self.groupId())

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'DEM Sampling'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return DrainLevelAlgorithm()


class SurfaceLevelAlgorithm(QgsProcessingAlgorithm):
    """
    Estimate drain level by finding the minimum value in the DEM in a buffer of specified width around the input point
    """
    OUTPUT = 'OUTPUT'
    INPUT_POINTS = 'INPUT_POINTS'
    OVERWRITE_VALUES = 'OVERWRITE_VALUES'
    DEM = 'DEM'

    TARGET_FIELDNAME = 'surface_level'

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_POINTS,
                self.tr('Manholes'),
                [QgsProcessing.TypeVectorPoint]
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.OVERWRITE_VALUES,
                self.tr('Overwrite existing values')
            )
        )

        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.DEM,
                self.tr('Digital Elevation Model')
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Surface level')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(parameters, self.INPUT_POINTS, context)
        source_layer = self.parameterAsVectorLayer(parameters, self.INPUT_POINTS, context)
        overwrite = self.parameterAsBoolean(parameters, self.OVERWRITE_VALUES, context)

        target_fields, target_field_idx, field_added = add_float_field_if_not_exists(
            source=source,
            fieldname=self.TARGET_FIELDNAME
        )

        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            target_fields,
            source.wkbType(),
            source.sourceCrs()
        )

        # Sample raster values
        alg_params = {
            'COLUMN_PREFIX': 'value_1234567890',   # make sure input layer doesn't have a field with this name
            'INPUT': parameters[self.INPUT_POINTS],
            'RASTERCOPY': parameters[self.DEM],
            'OUTPUT': 'TEMPORARY_OUTPUT'
        }
        sampled = processing.run('native:rastersampling', alg_params, context=context, feedback=feedback)['OUTPUT']

        for current, feature in enumerate(sampled.getFeatures()):

            if feedback.isCanceled():
                break

            source_feature = source_layer.getFeature(feature.id())
            output_feature = QgsFeature()
            output_feature.setFields(target_fields)

            for idx, value in enumerate(source_feature.attributes()):
                output_feature.setAttribute(idx, value)

            if overwrite or output_feature[target_field_idx] == NULL:
                output_feature[target_field_idx] = feature['value_12345678901']
            geom = QgsGeometry(source_feature.geometry())
            output_feature.setGeometry(geom)

            sink.addFeature(output_feature, QgsFeatureSink.FastInsert)

        return {self.OUTPUT: dest_id}

    def supportInPlaceEdit(self, layer: QgsMapLayer):
        if isinstance(layer, QgsVectorLayer):
            if self.TARGET_FIELDNAME in layer.fields().names():
                return True
        return False

    def flags(self):
        return super().flags() | QgsProcessingAlgorithm.FlagSupportsInPlaceEdits

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'surface_level'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Surface level')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr(self.groupId())

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'DEM Sampling'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return SurfaceLevelAlgorithm()
