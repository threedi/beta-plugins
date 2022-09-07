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
# TODO Fix channel 10157
# TODO Replace cliprasterbyextent by call to gdal.Warp()

from uuid import uuid4

import numpy as np
from osgeo import gdal
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
    QgsProcessingParameterNumber,
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

from .rasterize_channel_oo import Channel, CrossSectionLocation, EmptyOffsetError, InvalidOffsetError, fill_wedges
from .rasterize_channel_utils import merge_rasters


def align_qgs_rectangle(extent: QgsRectangle, xres, yres):
    """round the coordinates of an extent tuple (minx, miny, maxx, maxy) to a multiple of the resolution (pixel size) in
    such a way that the new extent contains the input extent"""
    minx = float(np.trunc(extent.xMinimum() / xres) * xres)
    miny = float(np.trunc(extent.yMinimum() / yres) * yres)
    maxx = float(np.ceil(extent.xMaximum() / xres) * xres)
    maxy = float(np.ceil(extent.yMaximum() / yres) * yres)
    return QgsRectangle(minx, miny, maxx, maxy)


class RasterizeChannelsAlgorithm(QgsProcessingAlgorithm):
    """
    Rasterize channels using its cross sections
    """
    INPUT_CHANNELS = 'INPUT_CHANNELS'
    INPUT_CROSS_SECTION_LOCATIONS = 'INPUT_CROSS_SECTION_LOCATIONS'
    INPUT_PIXEL_SIZE = 'PIXEL_SIZE'

    OUTPUT = 'OUTPUT'

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

        pixel_size_param = QgsProcessingParameterNumber(
            self.INPUT_PIXEL_SIZE,
            self.tr('Pixel size'),
            type=QgsProcessingParameterNumber.Double
        )
        pixel_size_param.setMetadata({'widget_wrapper':{'decimals': 2}})
        self.addParameter(pixel_size_param)

        self.addParameter(
            QgsProcessingParameterRasterDestination(
                self.OUTPUT,
                self.tr('Rasterized channels'),
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

        output_raster = self.parameterAsOutputLayer(parameters, self.OUTPUT, context)
        pixel_size = self.parameterAsDouble(parameters, self.INPUT_PIXEL_SIZE, context)

        rasters = []
        channels = []
        for i, channel_feature in enumerate(channel_features.getFeatures()):
            channel_id = channel_feature.attribute('id')
            multi_step_feedback.setProgressText(f"Reading channel and cross section data for channel {channel_id}...")
            channel = Channel.from_qgs_feature(channel_feature)
            for cross_section_location_feature in cross_section_location_features.getFeatures():
                if channel_id == cross_section_location_feature.attribute('channel_id'):
                    cross_section_location = CrossSectionLocation.from_qgs_feature(cross_section_location_feature)
                    channel.add_cross_section_location(cross_section_location)
            try:
                channel.generate_parallel_offsets()
                channels.append(channel)
            except EmptyOffsetError:
                feedback.reportError(
                    f"ERROR: Could not read channel with id {channel.id}: no valid parallel offset can be generated "
                    f"for some cross-sectional widths. "
                )
            except InvalidOffsetError:
                feedback.reportError(
                    f"ERROR: Could not read channel with id {channel.id}: no valid parallel offset can be generated "
                    f"for some cross-sectional widths. It may help to split the channel in the middle of its bends."
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
                multi_step_feedback.setProgressText(f"Rasterizing channel {channel.id}...")
                points = [QgsPoint(*point.coords[0]) for point in channel.points]

                # create temporary mesh file
                provider_meta = QgsProviderRegistry.instance().providerMetadata('mdal')
                mesh = QgsMesh()
                temp_mesh_filename = f"{uuid4()}.nc"
                temp_mesh_fullpath = QgsProcessingUtils.generateTempFilename(temp_mesh_filename)
                mesh_format = 'Ugrid'
                crs = QgsCoordinateReferenceSystem()
                provider_meta.createMeshData(mesh, temp_mesh_fullpath, mesh_format, crs)
                mesh_layer = QgsMeshLayer(temp_mesh_fullpath, 'editable mesh', 'mdal')

                # add points to mesh
                transform = QgsCoordinateTransform()
                mesh_layer.startFrameEditing(transform)
                editor = mesh_layer.meshEditor()
                points_added = editor.addPointsAsVertices(points, 0.0000001)
                if points_added != len(points):
                    feedback.pushWarning(f"Warning: Added only {points_added} points from a total of {len(points)}!")

                # add faces to mesh
                triangles_dict = {k: v for k, v in enumerate(channel.triangles)}
                total_triangles = len(triangles_dict)
                faces_added = 0
                occupied_vertices = np.array([], dtype=int)
                finished = False
                processed_triangles = []
                while not finished:
                    finished = True
                    for k in processed_triangles:
                        triangles_dict.pop(k)
                    processed_triangles = []
                    for j, triangle in triangles_dict.items():
                        if j == 0 or np.sum(np.in1d(triangle.vertex_indices, occupied_vertices)) >= 2:
                            error = editor.addFace(triangle.vertex_indices)
                            # Error types: https://api.qgis.org/api/classQgis.html#a69496edec4c420185984d9a2a63702dc
                            if error.errorType == 0:
                                finished = False
                                processed_triangles.append(j)
                                faces_added += 1
                                occupied_vertices = np.append(occupied_vertices, triangle.vertex_indices)
                if faces_added != total_triangles:
                    missing_area = np.sum(np.array([tri.geometry.area for tri in triangles_dict.values()]))
                    if missing_area > (pixel_size**2):
                        feedback.pushWarning(
                            f"Warning: Up to {int(missing_area/(pixel_size**2))} pixel(s) may be missing from the "
                            f"raster for channel {channel.id} !")

                mesh_layer.commitFrameEditing(transform, continueEditing=False)
                context.temporaryLayerStore().addMapLayer(mesh_layer)  # otherwise it cannot be used in processing alg

                extent = align_qgs_rectangle(mesh_layer.extent(), xres=pixel_size, yres=pixel_size)
                rasterize_mesh_params = {
                    'INPUT': mesh_layer.id(),
                    'DATASET_GROUPS': [0],
                    'DATASET_TIME': {'type': 'static'},
                    'EXTENT': extent,
                    'PIXEL_SIZE': pixel_size,
                    'CRS_OUTPUT': channel_features.sourceCrs(),
                    'OUTPUT': 'TEMPORARY_OUTPUT'
                }

                # Do not pass feedback to child algorithm to keep the logging clean
                rasterized = processing.run(
                    "native:meshrasterize",
                    rasterize_mesh_params,
                    context=context
                )["OUTPUT"]

                channels_crs_auth_id = channel_features.sourceCrs().authid()
                uri = f"polygon?crs={channels_crs_auth_id}"
                clip_extent_layer = QgsVectorLayer(uri, "Clip extent", "memory")
                clip_feature = QgsFeature(QgsFields())
                outline_geometry = QgsGeometry.fromWkt(channel.outline.wkt)
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
            multi_step_feedback.setProgressText("Merging rasters...")

            rasters_datasets = [gdal.Open(raster) for raster in rasters]
            merge_rasters(
                rasters_datasets,
                tile_size=1000,
                aggregation_method='min',
                output_filename=output_raster,
                output_nodatavalue=-9999,
                feedback=multi_step_feedback
            )

            return {self.OUTPUT: output_raster}

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'rasterize_channels'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Rasterize channels')

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
        return RasterizeChannelsAlgorithm()
