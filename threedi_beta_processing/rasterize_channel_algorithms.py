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

from qgis.PyQt.QtCore import (QCoreApplication, QVariant)
from qgis.core import (
    QgsMeshLayer,
    QgsVectorLayer,
    QgsPoint,
    QgsGeometry,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingContext,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFeatureSource,
    QgsCoordinateTransform,
    QgsCoordinateReferenceSystem,
    QgsFeature,
    QgsFeatureSink,
    QgsField,
    QgsFields,
    QgsProject,
    QgsWkbTypes
)
import processing

from .raster_tools.dem_sampler import AttributeProcessor
from .test_rasterize_channel.test_oo import run_tests
from .rasterize_channel_oo import Channel, CrossSectionLocation


class MesherizeChannelsAlgorithm(QgsProcessingAlgorithm):
    """
    Rasterize channels using its cross sections
    """
    OUTPUT = 'OUTPUT'
    INPUT_CHANNELS = 'INPUT_CHANNELS'
    INPUT_CROSS_SECTION_LOCATIONS = 'INPUT_CROSS_SECTION_LOCATIONS'

    def initAlgorithm(self, config):

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_CHANNELS,
                self.tr('Channels'),
                [QgsProcessing.TypeVectorLine]
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_CROSS_SECTION_LOCATIONS,
                self.tr('Cross section locations'),
                [QgsProcessing.TypeVectorPoint]
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Channel elevation points'),
                type=QgsProcessing.TypeVectorPolygon
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        channel_features = self.parameterAsSource(parameters, self.INPUT_CHANNELS, context)
        cross_section_location_features = self.parameterAsSource(parameters, self.INPUT_CROSS_SECTION_LOCATIONS, context)
        sink_fields = QgsFields()
        sink_fields.append(QgsField(name='id', type=QVariant.Int))
        sink_fields.append(QgsField(name='channel_id', type=QVariant.Int))

        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            fields=sink_fields,
            geometryType=QgsWkbTypes.PolygonZ,
            crs=channel_features.sourceCrs()
        )

        all_points = dict()
        for channel_feature in channel_features.getFeatures():
            channel = Channel.from_qgs_feature(channel_feature)
            channel_id = channel_feature.attribute('id')
            for cross_section_location_feature in cross_section_location_features.getFeatures():
                if channel_id == cross_section_location_feature.attribute('channel_id'):
                    cross_section_location = CrossSectionLocation.from_qgs_feature(cross_section_location_feature)
                    channel.add_cross_section_location(cross_section_location)
            channel.generate_parallel_offsets()

            # points = [QgsPoint(*point.coords[0]) for point in channel.points]
            # for point in points:
            #     sink_feature = QgsFeature(sink_fields)
            #     sink_feature.setGeometry(point)
            #     sink.addFeature(sink_feature, QgsFeatureSink.FastInsert)
            triangles = [QgsGeometry.fromWkt(triangle.wkt) for triangle in channel.triangles]
            for triangle in triangles:
                sink_feature = QgsFeature(sink_fields)
                sink_feature.setGeometry(triangle)
                sink.addFeature(sink_feature, QgsFeatureSink.FastInsert)

        # output_layer_name = "Channel points"
        # points = run_tests()
        # qgs_points = [QgsPoint(*point.coords[0]) for point in points]
        # uri = "pointz?crs=epsg:28992&field=id:integer"
        # layer = QgsVectorLayer(uri, output_layer_name, "memory")
        # fields = QgsFields()
        # id_field = QgsField(name='id', type=QVariant.Int)
        # fields.append(id_field)
        # features = dict()
        # for channel_id, points in all_points.items():

        # layer.dataProvider().addFeatures(features.values())
        # context.temporaryLayerStore().addMapLayer(layer)
        # layer_details = QgsProcessingContext.LayerDetails(output_layer_name, context.project(), self.OUTPUT)
        # context.addLayerToLoadOnCompletion(layer.id(), layer_details)
        return {self.OUTPUT: dest_id}

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'mesherize_channels'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Channels as mesh layers')

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
        return 'Conversion 1D-2D'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return MesherizeChannelsAlgorithm()
