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
# TODO Only add faces that are within the channel's outline

from typing import List, Tuple
from uuid import uuid4

import numpy as np
from qgis.PyQt.QtCore import (QCoreApplication, QVariant)
from qgis.core import (
    QgsApplication,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsGeometry,
    QgsMesh,
    QgsMeshLayer,
    QgsProcessingMultiStepFeedback,
    QgsFeature,
    QgsFeatureSink,
    QgsField,
    QgsFields,
    QgsPoint,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterRasterDestination,
    QgsProcessingUtils,
    QgsProject,
    QgsProviderRegistry,
    QgsRasterLayer,
    QgsRectangle,
    QgsVectorLayer,
    QgsWkbTypes
)
import processing

from .rasterize_channel_oo import Channel, CrossSectionLocation, EmptyOffsetError, fill_wedges


class MesherizeChannelsAlgorithm(QgsProcessingAlgorithm):
    """
    Rasterize channels using its cross sections
    """
    INPUT_CHANNELS = 'INPUT_CHANNELS'
    INPUT_CROSS_SECTION_LOCATIONS = 'INPUT_CROSS_SECTION_LOCATIONS'

    OUTPUT_TRIANGLES = 'OUTPUT_TRIANGLES'
    OUTPUT_OUTLINES = 'OUTPUT_OUTLINES'
    OUTPUT_POINTS = 'OUTPUT_POINTS'
    OUTPUT_LINES = 'OUTPUT_LINES'
    OUTPUT_RASTER = 'OUTPUT_RASTER'
    ADD_MESH_LAYERS_TO_PROJECT = 'ADD_MESH_LAYERS_TO_PROJECT'

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
                self.OUTPUT_TRIANGLES,
                self.tr('Triangle'),
                type=QgsProcessing.TypeVectorPolygon,
                createByDefault=False
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_OUTLINES,
                self.tr('Outline'),
                type=QgsProcessing.TypeVectorPolygon,
                createByDefault=False
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_POINTS,
                self.tr('Channel elevation point'),
                type=QgsProcessing.TypeVectorPoint,
                createByDefault=False
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_LINES,
                self.tr('Parallel Offset'),
                type=QgsProcessing.TypeVectorLine,
                createByDefault=False
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.ADD_MESH_LAYERS_TO_PROJECT,
                self.tr('Add mesh layers to project'),
                defaultValue=False
            )
        )

        self.addParameter(
            QgsProcessingParameterRasterDestination(
                self.OUTPUT_RASTER,
                self.tr('Rasterized channels'),
                createByDefault=True,
                defaultValue=None
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        # We report progress in three steps:
        # preparation phase (10%),
        # loop through the channels (60%)
        # merging the output rasters (30%)
        multi_step_feedback = QgsProcessingMultiStepFeedback(3, feedback)
        reg = QgsApplication.processingRegistry()
        channel_features = self.parameterAsSource(parameters, self.INPUT_CHANNELS, context)
        cross_section_location_features = self.parameterAsSource(parameters, self.INPUT_CROSS_SECTION_LOCATIONS,
                                                                 context)

        sink_fields = QgsFields()
        sink_fields.append(QgsField(name='id', type=QVariant.Int))
        sink_fields.append(QgsField(name='channel_id', type=QVariant.Int))

        triangle_fields = QgsFields()
        triangle_fields.append(QgsField(name='id', type=QVariant.Int))
        triangle_fields.append(QgsField(name='channel_id', type=QVariant.Int))
        triangle_fields.append(QgsField(name='vertex_indices', type=QVariant.String))

        (sink_triangles, dest_id_polygons) = self.parameterAsSink(
            parameters,
            self.OUTPUT_TRIANGLES,
            context,
            fields=triangle_fields,
            geometryType=QgsWkbTypes.PolygonZ,
            crs=channel_features.sourceCrs()
        )

        (sink_outlines, dest_id_polygons) = self.parameterAsSink(
            parameters,
            self.OUTPUT_OUTLINES,
            context,
            fields=sink_fields,
            geometryType=QgsWkbTypes.Polygon,
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

        (sink_lines, dest_id_lines) = self.parameterAsSink(
            parameters,
            self.OUTPUT_LINES,
            context,
            fields=sink_fields,
            geometryType=QgsWkbTypes.LineString,
            crs=channel_features.sourceCrs()
        )

        add_mesh_layers = self.parameterAsBoolean(
            parameters,
            self.ADD_MESH_LAYERS_TO_PROJECT,
            context
        )

        output_raster = self.parameterAsOutputLayer(parameters, self.OUTPUT_RASTER, context)

        mesh_layers = []
        rasters = []
        channels = []
        for i, channel_feature in enumerate(channel_features.getFeatures()):
            channel_id = channel_feature.attribute('id')
            feedback.pushInfo(f"Reading channel {channel_id}")
            channel = Channel.from_qgs_feature(channel_feature)
            for cross_section_location_feature in cross_section_location_features.getFeatures():
                if channel_id == cross_section_location_feature.attribute('channel_id'):
                    cross_section_location = CrossSectionLocation.from_qgs_feature(cross_section_location_feature)
                    channel.add_cross_section_location(cross_section_location)
            try:
                channel.generate_parallel_offsets()
                channels.append(channel)
            except EmptyOffsetError:
                feedback.pushWarning(
                    f"Could not read channel with id {channel.id}: no valid parallel offset can be generated for some "
                    f"cross-sectional widths"
                )
            multi_step_feedback.setProgress(100 * i / channel_features.featureCount())

        fill_wedges(channels)

        multi_step_feedback.setCurrentStep(1)
        if len(channels) == 0:
            multi_step_feedback.reportError(
                f"No valid channels to process", fatalError=True)
            raise QgsProcessingException()
        else:
            for i, channel in enumerate(channels):
                feedback.pushInfo(f"Processing channel {channel.id}")
                points = [QgsPoint(*point.coords[0]) for point in channel.points]

                # for debugging only
                # for po_id, po in enumerate(channel.parallel_offsets):
                #     feedback.pushInfo(f"vertex_indices for parallel offset {po_id}: {po.vertex_indices}")
                # for tri_id, tri in enumerate(channel.triangles):
                #     feedback.pushInfo(f"vertex_indices for triangle {tri_id}: {tri.vertex_indices}")

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
                editor = mesh_layers[-1].meshEditor()
                points_added = editor.addPointsAsVertices(points, 0.0000001)
                if points_added != len(points):
                    feedback.pushWarning(f"Added only {points_added} points from a total of {len(points)}!")

                # add faces to mesh
                faces_added = 0
                triangles_dict = {k: v for k, v in enumerate(channel.triangles)}
                total_triangles = 0
                occupied_vertices = np.array([], dtype=int)
                finished = False
                first_round = True
                processed_triangles = []
                while not finished:
                    finished = True
                    for k in processed_triangles:
                        triangles_dict.pop(k)
                    processed_triangles = []
                    for i, triangle in triangles_dict.items():
                        if first_round:
                            total_triangles += 1
                        if i == 0 or np.sum(np.in1d(triangle.vertex_indices, occupied_vertices)) >= 2:
                            error = editor.addFace(triangle.vertex_indices)
                            # Error types: https://api.qgis.org/api/classQgis.html#a69496edec4c420185984d9a2a63702dc
                            if error.errorType == 0:
                                finished = False
                                processed_triangles.append(i)
                                faces_added += 1
                                occupied_vertices = np.append(occupied_vertices, triangle.vertex_indices)
                    first_round = False
                if faces_added != total_triangles:
                    feedback.pushWarning(f"Added only {faces_added} out of {total_triangles} triangles to mesh!")

                mesh_layers[-1].commitFrameEditing(transform, continueEditing=False)
                context.temporaryLayerStore().addMapLayer(mesh_layers[-1])

                if add_mesh_layers:
                    layer_details = QgsProcessingContext.LayerDetails(temp_mesh_filename, context.project())
                    context.addLayerToLoadOnCompletion(mesh_layers[-1].id(), layer_details)

                for point_id, point in enumerate(points):
                    sink_feature = QgsFeature(sink_fields)
                    sink_feature[0] = point_id
                    sink_feature[1] = channel_id
                    sink_feature.setGeometry(point)
                    sink_points.addFeature(sink_feature, QgsFeatureSink.FastInsert)

                for triangle_id, triangle in enumerate(channel.triangles):
                    sink_feature = QgsFeature(triangle_fields)
                    sink_feature[0] = triangle_id
                    sink_feature[1] = channel_id
                    sink_feature[2] = str(triangle.vertex_indices)
                    sink_feature.setGeometry(QgsGeometry.fromWkt(triangle.geometry.wkt))
                    sink_triangles.addFeature(sink_feature, QgsFeatureSink.FastInsert)

                # Add outline to outlines layer
                outline_geometry = QgsGeometry.fromWkt(channel.outline.wkt)
                sink_feature = QgsFeature(sink_fields)
                sink_feature[0] = channel_id
                sink_feature[1] = channel_id
                sink_feature.setGeometry(outline_geometry)
                sink_outlines.addFeature(sink_feature, QgsFeatureSink.FastInsert)

                parallel_offsets = [QgsGeometry.fromWkt(po.geometry.wkt) for po in channel.parallel_offsets]
                for po_id, po in enumerate(parallel_offsets):
                    sink_feature = QgsFeature(sink_fields)
                    sink_feature[0] = po_id
                    sink_feature[1] = channel_id
                    sink_feature.setGeometry(po)
                    sink_lines.addFeature(sink_feature, QgsFeatureSink.FastInsert)

                rasterize_mesh_params = {
                    'INPUT': mesh_layers[-1].id(),
                    'DATASET_GROUPS': [0],
                    'DATASET_TIME': {'type': 'static'},
                    'EXTENT': None,
                    'PIXEL_SIZE': 0.5,
                    'CRS_OUTPUT': QgsCoordinateReferenceSystem('EPSG:28992'),
                    'OUTPUT': 'TEMPORARY_OUTPUT'
                }

                # use QgsProcessingAlgorithm.run() instead of processing.run() to be able to hide feedback but still be
                # able to check if algorithm ran succesfully (ok == True)
                alg_meshrasterize = reg.algorithmById("native:meshrasterize")
                results, ok = alg_meshrasterize.run(
                    parameters=rasterize_mesh_params,
                    context=context,
                    feedback=QgsProcessingFeedback()
                )
                if not ok:
                    multi_step_feedback.pushError(f"Error when rasterizing mesh for channel {channel.id}")
                    continue
                rasterized = results["OUTPUT"]

                channels_crs_auth_id = channel_features.sourceCrs().authid()
                uri = f"polygon?crs={channels_crs_auth_id}"
                clip_extent_layer = QgsVectorLayer(uri, "Clip extent", "memory")
                clip_feature = QgsFeature(QgsFields())
                clip_feature.setGeometry(outline_geometry)
                clip_extent_layer.dataProvider().addFeatures([clip_feature])

                clip_parameters = {
                    'INPUT': rasterized,
                    'MASK': clip_extent_layer,
                    'SOURCE_CRS': None,
                    'TARGET_CRS': None,
                    'NODATA': -9999,
                    'ALPHA_BAND': False,
                    'CROP_TO_CUTLINE': False,
                    'KEEP_RESOLUTION': True,
                    'SET_RESOLUTION': False,
                    'X_RESOLUTION': None,
                    'Y_RESOLUTION': None,
                    'MULTITHREADING': False,
                    'OPTIONS': 'COMPRESS=DEFLATE|PREDICTOR=2|ZLEVEL=9',
                    'DATA_TYPE': 6,  # Float32
                    'EXTRA': '-tap',
                    'OUTPUT': 'TEMPORARY_OUTPUT'
                }

                # use QgsProcessingAlgorithm.run() instead of processing.run() to be able to hide feedback but still be
                # able to check if algorithm ran succesfully (ok == True)
                alg_cliprasterbymasklayer = reg.algorithmById("gdal:cliprasterbymasklayer")
                results, ok = alg_cliprasterbymasklayer.run(
                    clip_parameters,
                    context=context,
                    feedback=QgsProcessingFeedback()
                )
                if not ok:
                    multi_step_feedback.reportError(
                        f"Error when clipping channel raster by outline for channel {channel.id}",
                        fatalError=False
                    )
                    continue
                rasters.append(results["OUTPUT"])

                multi_step_feedback.setProgress(100 * i / len(channels))

            multi_step_feedback.setCurrentStep(2)
            multi_step_feedback.setProgress(0)
            # calculate shared extent of all output rasters
            extent = QgsRectangle()
            extent.setMinimal()

            for raster in rasters:
                raster_layer = QgsRasterLayer(raster)
                extent.combineExtentWith(raster_layer.extent())

            # Create dummy reference raster of shared extent
            # use QgsProcessingAlgorithm.run() instead of processing.run() to be able to hide feedback but still be
            # able to check if algorithm ran succesfully (ok == True)
            createconstantrasterlayer_parameters = {
                'EXTENT': extent,
                'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:28992'),
                'PIXEL_SIZE': 0.5,
                'NUMBER': 1,
                'OUTPUT_TYPE': 5,
                'OUTPUT': 'TEMPORARY_OUTPUT'
            }
            alg_createconstantrasterlayer = reg.algorithmById("native:createconstantrasterlayer")
            results, ok = alg_createconstantrasterlayer.run(
                parameters=createconstantrasterlayer_parameters,
                context=context,
                feedback=QgsProcessingFeedback()
            )
            if not ok:
                multi_step_feedback.reportError(
                    f"Error when creating base raster for merging outputs", fatalError=True)
                raise QgsProcessingException

            reference_layer = results["OUTPUT"]

            cellstatistics_parameters = {
                'INPUT': rasters,
                'STATISTIC': 6,  # MINIMUM
                'IGNORE_NODATA': True,
                'REFERENCE_LAYER': reference_layer,
                'OUTPUT_NODATA_VALUE': -9999,
                'OUTPUT': output_raster
            }
            alg_cellstatistics = reg.algorithmById("native:cellstatistics")

            results, ok = alg_cellstatistics.run(
                parameters=cellstatistics_parameters,
                context=context,
                feedback=multi_step_feedback
            )
            if not ok:
                multi_step_feedback.reportError(
                    f"Error when merging raster outputs", fatalError=True)
                raise QgsProcessingException

            return {self.OUTPUT_RASTER: results['OUTPUT']}

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
