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
from typing import List, Tuple
from uuid import uuid4

from qgis.PyQt.QtCore import (QCoreApplication, QVariant)
from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsGeometry,
    QgsMesh,
    QgsMeshLayer,
    QgsFeature,
    QgsFeatureSink,
    QgsField,
    QgsFields,
    QgsPoint,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingContext,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFeatureSource,
    QgsProcessingUtils,
    QgsProject,
    QgsProviderRegistry,
    QgsVectorLayer,
    QgsWkbTypes
)
import processing

from .rasterize_channel_oo import Channel, CrossSectionLocation


class MesherizeChannelsAlgorithm(QgsProcessingAlgorithm):
    """
    Rasterize channels using its cross sections
    """
    OUTPUT_POLYGONS = 'OUTPUT_POLYGONS'
    OUTPUT_POINTS = 'OUTPUT_POINTS'
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
                self.OUTPUT_POLYGONS,
                self.tr('Triangle'),
                type=QgsProcessing.TypeVectorPolygon
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_POINTS,
                self.tr('Channel elevation point'),
                type=QgsProcessing.TypeVectorPoint
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        channel_features = self.parameterAsSource(parameters, self.INPUT_CHANNELS, context)
        cross_section_location_features = self.parameterAsSource(parameters, self.INPUT_CROSS_SECTION_LOCATIONS, context)

        sink_fields = QgsFields()
        sink_fields.append(QgsField(name='id', type=QVariant.Int))
        sink_fields.append(QgsField(name='channel_id', type=QVariant.Int))

        (sink_polygons, dest_id_polygons) = self.parameterAsSink(
            parameters,
            self.OUTPUT_POLYGONS,
            context,
            fields=sink_fields,
            geometryType=QgsWkbTypes.PolygonZ,
            crs=channel_features.sourceCrs()
        )

        (sink_points, dest_id_points) = self.parameterAsSink(
            parameters,
            self.OUTPUT_POINTS,
            context,
            fields=sink_fields,
            geometryType=QgsWkbTypes.PointZ,
            crs=channel_features.sourceCrs()
        )


        mesh_layers = []

        for channel_feature in channel_features.getFeatures():
            channel = Channel.from_qgs_feature(channel_feature)
            channel_id = channel_feature.attribute('id')
            for cross_section_location_feature in cross_section_location_features.getFeatures():
                if channel_id == cross_section_location_feature.attribute('channel_id'):
                    cross_section_location = CrossSectionLocation.from_qgs_feature(cross_section_location_feature)
                    channel.add_cross_section_location(cross_section_location)
            channel.generate_parallel_offsets()

            points = [QgsPoint(*point.coords[0]) for point in channel.points]

            # create a mesh on disk
            provider_meta = QgsProviderRegistry.instance().providerMetadata('mdal')
            mesh = QgsMesh()
            temp_mesh_filename = f"{uuid4()}.nc"
            temp_mesh_fullpath = QgsProcessingUtils.generateTempFilename(temp_mesh_filename)
            mesh_format = 'Ugrid'
            crs = QgsCoordinateReferenceSystem()
            provider_meta.createMeshData(mesh, temp_mesh_fullpath, mesh_format, crs)
            mesh_layers.append(QgsMeshLayer(temp_mesh_fullpath, 'editable mesh', 'mdal'))

            # add points to mesh
            transform = QgsCoordinateTransform()
            mesh_layers[-1].startFrameEditing(transform)
            points_added = mesh_layers[-1].meshEditor().addPointsAsVertices(points, 0.0000001)
            feedback.pushInfo(f"Added {points_added} points from a total of {len(points)}")

            # add faces to mesh
            faces_added = 0
            total_triangles = 0
            for triangle in channel.triangles:
                total_triangles += 1
                error = mesh_layers[-1].meshEditor().addFace(triangle.vertex_indices)
                if error.errorType == 0:
                    faces_added += 1
            feedback.pushInfo(f"Added {faces_added} faces from a total of {total_triangles  }")

            mesh_layers[-1].commitFrameEditing(transform, continueEditing=False)
            context.temporaryLayerStore().addMapLayer(mesh_layers[-1])
            layer_details = QgsProcessingContext.LayerDetails(temp_mesh_filename, context.project(), self.OUTPUT_POLYGONS)
            context.addLayerToLoadOnCompletion(mesh_layers[-1].id(), layer_details)

            for point in points:
                sink_feature = QgsFeature(sink_fields)
                sink_feature.setGeometry(point)
                sink_points.addFeature(sink_feature, QgsFeatureSink.FastInsert)
            triangles = [QgsGeometry.fromWkt(triangle.geometry.wkt) for triangle in channel.triangles]
            for triangle in triangles:
                sink_feature = QgsFeature(sink_fields)
                sink_feature.setGeometry(triangle)
                sink_polygons.addFeature(sink_feature, QgsFeatureSink.FastInsert)

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

        return {self.OUTPUT_POLYGONS: dest_id_polygons}

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
