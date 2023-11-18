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
from uuid import uuid4

import numpy as np
from osgeo import gdal
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (
    QgsApplication,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsGeometry,
    QgsMesh,
    QgsMeshLayer,
    QgsProcessingMultiStepFeedback,
    QgsFeature,
    QgsFields,
    QgsPoint,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterNumber,
    QgsProcessingParameterRasterDestination,
    QgsProcessingParameterRasterLayer,
    QgsProcessingUtils,
    QgsProviderRegistry,
    QgsRectangle,
    QgsVectorLayer,
)
import processing

from .rasterize_channel import (
    Channel,
    CrossSectionLocation,
    EmptyOffsetError,
    InvalidOffsetError,
    WidthsNotIncreasingError,
    fill_wedges,
)
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

    INPUT_CHANNELS = "INPUT_CHANNELS"
    INPUT_CROSS_SECTION_LOCATIONS = "INPUT_CROSS_SECTION_LOCATIONS"
    INPUT_DEM = "INPUT_DEM"
    INPUT_PIXEL_SIZE = "PIXEL_SIZE"

    OUTPUT = "OUTPUT"

    def initAlgorithm(self, config):

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_CHANNELS, self.tr("Channels"), [QgsProcessing.TypeVectorLine]
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_CROSS_SECTION_LOCATIONS,
                self.tr("Cross section locations"),
                [QgsProcessing.TypeVectorPoint],
            )
        )

        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.INPUT_DEM, self.tr("Digital Elevation Model"), optional=True
            )
        )

        pixel_size_param = QgsProcessingParameterNumber(
            self.INPUT_PIXEL_SIZE,
            self.tr("Pixel size"),
            type=QgsProcessingParameterNumber.Double,
            optional=True,
        )
        pixel_size_param.setMetadata({"widget_wrapper": {"decimals": 2}})
        self.addParameter(pixel_size_param)

        self.addParameter(
            QgsProcessingParameterRasterDestination(
                self.OUTPUT,
                self.tr("Rasterized channels"),
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        # Progress is reported in three steps:
        # preparation phase (10%),
        # loop through the channels (60%)
        # merging the output rasters (30%)
        multi_step_feedback = QgsProcessingMultiStepFeedback(3, feedback)
        reg = QgsApplication.processingRegistry()
        channel_features = self.parameterAsSource(
            parameters, self.INPUT_CHANNELS, context
        )
        cross_section_location_features = self.parameterAsSource(
            parameters, self.INPUT_CROSS_SECTION_LOCATIONS, context
        )

        output_raster = self.parameterAsOutputLayer(parameters, self.OUTPUT, context)
        dem = self.parameterAsRasterLayer(parameters, self.INPUT_DEM, context)
        user_pixel_size = self.parameterAsDouble(
            parameters, self.INPUT_PIXEL_SIZE, context
        )
        if dem:
            if dem.rasterUnitsPerPixelX() != dem.rasterUnitsPerPixelY():
                multi_step_feedback.reportError(
                    "Input Digital Elevation Model has different X and Y resolutions",
                    fatalError=True,
                )
                raise QgsProcessingException()
            pixel_size = dem.rasterUnitsPerPixelX()
            feedback.pushInfo("Using pixel size from input Digital Elevation Model")
        elif user_pixel_size:
            pixel_size = user_pixel_size
        else:
            multi_step_feedback.reportError(
                "Either 'Digital Elevation Model' or 'Pixel size' has to be specified, fatalError=True)"
            )
            raise QgsProcessingException()

        rasters = []
        channels = []
        errors = []
        warnings = []
        total_missing_pixels = 0
        for i, channel_feature in enumerate(channel_features.getFeatures()):
            channel_id = channel_feature.attribute("id")
            multi_step_feedback.setProgressText(
                f"Reading channel and cross section data for channel {channel_id}..."
            )
            channel = Channel.from_qgs_feature(channel_feature)
            for (
                cross_section_location_feature
            ) in cross_section_location_features.getFeatures():
                if channel_id == cross_section_location_feature.attribute("channel_id"):
                    cross_section_location = CrossSectionLocation.from_qgs_feature(
                        cross_section_location_feature,
                        wall_displacement=pixel_size/4.0,
                        simplify_tolerance=pixel_size/2.0
                    )
                    channel.add_cross_section_location(cross_section_location)
            try:
                channel.generate_parallel_offsets()
                channels.append(channel)
            except EmptyOffsetError:
                errors.append(channel_id)
                feedback.reportError(
                    f"ERROR: Could not read channel with id {channel.id}: no valid parallel offset can be generated "
                    f"for some cross-sectional widths. "
                )
            except InvalidOffsetError:
                errors.append(channel_id)
                feedback.reportError(
                    f"ERROR: Could not read channel with id {channel.id}: no valid parallel offset can be generated "
                    f"for some cross-sectional widths. It may help to split the channel in the middle of its bends."
                )
            except WidthsNotIncreasingError:
                errors.append(channel_id)
                feedback.reportError(
                    f"ERROR: Could not read channel with id {channel.id}: the widths in the cross-section table for one "
                    f"or more cross-section locations are not all increasing with height."
                )
            multi_step_feedback.setProgress(100 * i / channel_features.featureCount())

        fill_wedges(channels)

        multi_step_feedback.setCurrentStep(1)
        if len(channels) == 0:
            multi_step_feedback.reportError(
                "No valid channels to process", fatalError=True
            )
            raise QgsProcessingException()
        else:
            for i, channel in enumerate(channels):
                multi_step_feedback.setProgressText(
                    f"Rasterizing channel {channel.id}..."
                )
                points = [QgsPoint(*point.geom.coords[0]) for point in channel.points]

                # create temporary mesh file
                provider_meta = QgsProviderRegistry.instance().providerMetadata("mdal")
                mesh = QgsMesh()
                temp_mesh_filename = f"{uuid4()}.nc"
                temp_mesh_fullpath = QgsProcessingUtils.generateTempFilename(
                    temp_mesh_filename
                )
                mesh_format = "Ugrid"
                crs = QgsCoordinateReferenceSystem()
                provider_meta.createMeshData(mesh, temp_mesh_fullpath, mesh_format, crs)
                provider_meta.createMeshData(mesh=mesh, fileName=temp_mesh_fullpath, driverName="mdal", crs=crs)
                mesh_layer = QgsMeshLayer(temp_mesh_fullpath, "editable mesh", "mdal")

                # add points to mesh
                transform = QgsCoordinateTransform()
                mesh_layer.startFrameEditing(transform)
                editor = mesh_layer.meshEditor()
                points_added = editor.addPointsAsVertices(points, 0.0000001)
                if points_added != len(points):
                    feedback.pushWarning(
                        f"Warning: Added only {points_added} points from a total of {len(points)}!"
                    )

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
                        if (
                            j == 0
                            or np.sum(
                                np.in1d(triangle.vertex_indices, occupied_vertices)
                            )
                            >= 2
                        ):
                            error = editor.addFace(triangle.vertex_indices)
                            # Error types: https://api.qgis.org/api/classQgis.html#a69496edec4c420185984d9a2a63702dc
                            if error.errorType == 0:
                                finished = False
                                processed_triangles.append(j)
                                faces_added += 1
                                occupied_vertices = np.append(
                                    occupied_vertices, triangle.vertex_indices
                                )
                if faces_added != total_triangles:
                    missing_area = np.sum(
                        np.array([tri.geometry.area for tri in triangles_dict.values()])
                    )
                    if missing_area > (pixel_size**2):
                        warnings.append(channel.id),
                        missing_pixels = int(missing_area / (pixel_size**2))
                        total_missing_pixels += missing_pixels
                        feedback.pushWarning(
                            f"Warning: Up to {missing_pixels} pixel(s) may be missing from the "
                            f"raster for channel {channel.id} !"
                        )

                mesh_layer.commitFrameEditing(transform, continueEditing=False)
                context.temporaryLayerStore().addMapLayer(
                    mesh_layer
                )  # otherwise it cannot be used in processing alg

                extent = align_qgs_rectangle(
                    mesh_layer.extent(), xres=pixel_size, yres=pixel_size
                )
                rasterize_mesh_params = {
                    "INPUT": mesh_layer.id(),
                    "DATASET_GROUPS": [0],
                    "DATASET_TIME": {"type": "static"},
                    "EXTENT": extent,
                    "PIXEL_SIZE": pixel_size,
                    "CRS_OUTPUT": channel_features.sourceCrs(),
                    "OUTPUT": "TEMPORARY_OUTPUT",
                }

                # Do not pass feedback to child algorithm to keep the logging clean
                rasterized = processing.run(
                    "native:meshrasterize", rasterize_mesh_params, context=context
                )["OUTPUT"]

                channels_crs_auth_id = channel_features.sourceCrs().authid()
                uri = f"polygon?crs={channels_crs_auth_id}"
                clip_extent_layer = QgsVectorLayer(uri, "Clip extent", "memory")
                clip_feature = QgsFeature(QgsFields())
                outline_geometry = QgsGeometry.fromWkt(channel.outline.wkt)
                clip_feature.setGeometry(outline_geometry)
                clip_extent_layer.dataProvider().addFeatures([clip_feature])

                clip_parameters = {
                    "INPUT": rasterized,
                    "MASK": clip_extent_layer,
                    "SOURCE_CRS": None,
                    "TARGET_CRS": None,
                    "NODATA": -9999,
                    "ALPHA_BAND": False,
                    "CROP_TO_CUTLINE": False,
                    "KEEP_RESOLUTION": True,
                    "SET_RESOLUTION": False,
                    "X_RESOLUTION": None,
                    "Y_RESOLUTION": None,
                    "MULTITHREADING": False,
                    "OPTIONS": "COMPRESS=DEFLATE|PREDICTOR=2|ZLEVEL=9",
                    "DATA_TYPE": 6,  # Float32
                    "EXTRA": "-tap",
                    "OUTPUT": "TEMPORARY_OUTPUT",
                }

                # use QgsProcessingAlgorithm.run() instead of processing.run() to be able to hide feedback but still be
                # able to check if algorithm ran succesfully (ok == True)
                alg_cliprasterbymasklayer = reg.algorithmById(
                    "gdal:cliprasterbymasklayer"
                )
                results, ok = alg_cliprasterbymasklayer.run(
                    clip_parameters, context=context, feedback=QgsProcessingFeedback()
                )
                if not ok:
                    multi_step_feedback.reportError(
                        f"Error when clipping channel raster by outline for channel {channel.id}",
                        fatalError=False,
                    )
                    continue
                rasters.append(results["OUTPUT"])

                multi_step_feedback.setProgress(100 * i / len(channels))

            multi_step_feedback.setCurrentStep(2)
            multi_step_feedback.setProgressText("Merging rasters...")

            rasters_datasets = [gdal.Open(raster) for raster in rasters]
            if dem:
                uri = dem.dataProvider().dataSourceUri()
                dem_gdal_datasource = gdal.Open(uri)
                rasters_datasets.append(dem_gdal_datasource)
            merge_rasters(
                rasters_datasets,
                tile_size=1000,
                aggregation_method="min",
                output_filename=output_raster,
                output_nodatavalue=-9999,
                output_pixel_size=pixel_size,
                feedback=multi_step_feedback,
            )

            if errors:
                feedback.pushWarning(
                    f"Warning: The following channels where not rasterized: {', '.join([str(i) for i in errors])}. "
                    f"See previous log messages for more information."
                )

            if warnings:
                feedback.pushWarning(
                    f"Warning: The following channels may have missing pixels: {', '.join([str(i) for i in warnings])}. "
                    f"In total, up to {total_missing_pixels} pixels may be missing. See previous log messages for more "
                    f"information."
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
        return "rasterize_channels"

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr("Rasterize channels")

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
        return "Conversion 1D-2D"

    def shortHelpString(self):
        return self.tr(
            """
            <h3>Please note</h3>
            <ul>
            <li>Please run the 3Di Check Schematisation algorithm and resolve any issues relating to channels or cross section locations before running this algorithm</li>
            <li>Use the <em>3Di Schematisation Editor &gt; Load from spatialite</em> to create the required input layers for the algorithm.</li>
            <li>Some channels cannot be (fully) rasterized, e.g. wide cross section definitions on channels with sharp bends may lead to self-intersection of the described cross-section</li>
            <li>Tabulated trapezium, Tabulated rectangle, and YZ cross-sections are supported, as long as they always become wider when going up (vertical segments are allowed).</li>
            <li>Other cross section shapes are not supported</li>
            </ul>
            <h3>Parameters</h3>
            <h4>Channels</h4>
            <p>Channel layer as generated by the 3Di Schematisation Editor. You may limit processing to a selection of the input features.</p>
            <h4>Cross section locations</h4>
            <p>Cross section location layer as generated by the 3Di Schematisation Editor. You may limit processing to a selection of the input features. This may be useful if the channel has one or several cross section locations with non-tabulated cross section shapes.</p>
            <h4>Digital elevation model</h4>
            <p>Optional input. If used, the pixel size will be taken from the DEM. The rasterized channels will be carved into the DEM using a 'deepen-only' approach: pixel values will only be changed where the rasterized channels are lower than the DEM. This is evaluated pixel by pixel.</p>
            <p>If not used, <em>Pixel size&nbsp;</em>has to be filled in.</p>
            <h4>Pixel size</h4>
            <p>Optional input. If&nbsp;<em>Digital elevation model</em> is not specified, specify the pixel size of the output raster.</p>
            <h4>Rasterized channels</h4>
            <p>Output file location. A temporary output can also be chosen - note that in that case, the file will be deleted when closing the project.</p>
            """
        )

    def tr(self, string):
        return QCoreApplication.translate("Processing", string)

    def createInstance(self):
        return RasterizeChannelsAlgorithm()
