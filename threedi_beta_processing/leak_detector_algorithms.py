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
from osgeo import gdal

from threedigrid.admin.gridadmin import GridH5Admin
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
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFile,
    QgsProcessingParameterNumber,
    QgsProcessingParameterRasterDestination,
    QgsProcessingParameterRasterLayer,
    QgsProcessingUtils,
    QgsProviderRegistry,
    QgsRectangle,
    QgsVectorLayer,
    QgsWkbTypes,
)

from .leak_detector import LeakDetector


class DetectLeakingObstaclesAlgorithm(QgsProcessingAlgorithm):
    """
    Detect obstacle lines in the DEM that are ignored by 3Di due to its location relative to cell edges
    """

    INPUT_GRIDADMIN = "INPUT_GRIDADMIN"
    INPUT_DEM = "INPUT_DEM"
    INPUT_MIN_OBSTACLE_HEIGHT = "INPUT_MIN_OBSTACLE_HEIGHT"
    INPUT_SEARCH_PRECISION = "INPUT_SEARCH_PRECISION"

    OUTPUT_EDGES = "OUTPUT_EDGES"

    def initAlgorithm(self, config):

        self.addParameter(
            QgsProcessingParameterFile(
                self.INPUT_GRIDADMIN, self.tr("Gridadmin file"), extension="h5"
            )
        )

        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.INPUT_DEM, self.tr("Digital Elevation Model")
            )
        )

        min_obstacle_height_param = QgsProcessingParameterNumber(
            self.INPUT_MIN_OBSTACLE_HEIGHT,
            self.tr("Minimum obstacle height (m)"),
            type=QgsProcessingParameterNumber.Double
        )
        min_obstacle_height_param.setMetadata({"widget_wrapper": {"decimals": 3}})
        self.addParameter(min_obstacle_height_param)

        search_precision_param = QgsProcessingParameterNumber(
            self.INPUT_SEARCH_PRECISION,
            self.tr("Vertical search precision (m)"),
            type=QgsProcessingParameterNumber.Double,
            defaultValue=0.01
        )
        search_precision_param.setMetadata({"widget_wrapper": {"decimals": 3}})
        self.addParameter(search_precision_param)


        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_EDGES,
                self.tr('Output: Cell edges with obstacles'),
                type=QgsProcessing.TypeVectorLine
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        gridadmin_fn = self.parameterAsFile(parameters, self.INPUT_GRIDADMIN, context)
        gr = GridH5Admin(gridadmin_fn)
        dem = self.parameterAsRasterLayer(parameters, self.INPUT_DEM, context)
        dem_fn = dem.dataProvider().dataSourceUri()
        dem_ds = gdal.Open(dem_fn)
        min_obstacle_height = self.parameterAsDouble(parameters, self.INPUT_MIN_OBSTACLE_HEIGHT, context)
        search_precision = self.parameterAsDouble(parameters, self.INPUT_SEARCH_PRECISION, context)

        edges_sink_fields = QgsFields()
        edges_sink_fields.append(QgsField(name="id", type=QVariant.Int))
        edges_sink_fields.append(QgsField(name="exchange_level", type=QVariant.Double))
        edges_sink_fields.append(QgsField(name="crest_level", type=QVariant.Double))

        crs = QgsCoordinateReferenceSystem(f"EPSG:{gr.epsg_code}")
        (edges_sink, self.edges_sink_dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT_EDGES,
            context,
            fields=edges_sink_fields,
            geometryType=QgsWkbTypes.LineString,
            crs=crs
        )

        feedback.setProgressText("Read computational grid...")
        leak_detector = LeakDetector(
            gridadmin=gr,
            dem=dem_ds,
            cell_ids=list(gr.cells.id),
            min_obstacle_height=min_obstacle_height,
            search_precision=search_precision,
            min_peak_prominence=min_obstacle_height,
            feedback=feedback
        )
        feedback.setProgressText("Find obstacles...")
        leak_detector.run(feedback=feedback)
        feedback.setProgressText("Create cell edge features...")
        for result in leak_detector.result_edges():
            if feedback.isCanceled():
                return
            feature = QgsFeature()
            feature.setFields(edges_sink_fields)
            feature.setAttribute(0, int(result["flowline_id"]))
            feature.setAttribute(1, float(result["exchange_level"]))
            feature.setAttribute(2, float(result["crest_level"]))
            geometry = QgsGeometry()
            geometry.fromWkb(result["geometry"].wkb)
            feature.setGeometry(geometry)
            edges_sink.addFeature(feature, QgsFeatureSink.FastInsert)
            # feedback.setProgress(feedback.progress() + (1 / nr_progress_steps) / len(topo.edges) * max_progress)

        return {self.OUTPUT_EDGES: self.edges_sink_dest_id}

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return "detect_leaking_obstacles"

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr("Detect leaking obstacles")

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
        return "Computational grid"

    def shortHelpString(self):
        return self.tr(
            """
            <h3>Please note</h3>
            <ul>
            <li>Please run the 3Di Check Schematisation algorithm and resolve any issues relating to channels or cross section locations before running this algorithm</li>
            <li>Use the <em>3Di Schematisation Editor &gt; Load from spatialite</em> to create the required input layers for the algorithm.</li>
            <li>Some channels cannot be (fully) rasterized, e.g. wide cross section definitions on channels with sharp bends may lead to self-intersection of the described cross-section</li>
            <li>Tabulated trapezium cross sections are fully supported</li>
            <li>Tabulated rectangle cross sections will be processed as tabulated trapezium profiles</li>
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
        return DetectLeakingObstaclesAlgorithm()
