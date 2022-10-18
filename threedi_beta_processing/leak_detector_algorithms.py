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
from pathlib import Path

from osgeo import gdal
from typing import Any, Dict, Tuple

from shapely import wkt

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
    QgsProcessingContext,
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


STYLE_DIR = Path(__file__).parent / "style"


class DetectLeakingObstaclesAlgorithm(QgsProcessingAlgorithm):
    """
    Detect obstacle lines in the DEM that are ignored by 3Di due to its location relative to cell edges
    """

    INPUT_GRIDADMIN = "INPUT_GRIDADMIN"
    INPUT_DEM = "INPUT_DEM"
    INPUT_OBSTACLES = "INPUT_OBSTACLES"
    INPUT_MIN_OBSTACLE_HEIGHT = "INPUT_MIN_OBSTACLE_HEIGHT"
    INPUT_SEARCH_PRECISION = "INPUT_SEARCH_PRECISION"

    OUTPUT_EDGES = "OUTPUT_EDGES"
    OUTPUT_OBSTACLES = "OUTPUT_OBSTACLES"

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

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_OBSTACLES,
                self.tr('Linear obstacles'),
                [QgsProcessing.TypeVectorLine]
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
                self.tr('Output: Obstacle on cell edge'),
                type=QgsProcessing.TypeVectorLine
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_OBSTACLES,
                self.tr('Output: Obstacle in DEM'),
                type=QgsProcessing.TypeVectorLine
            )
        )

    def checkParameterValues(self, parameters: Dict[str, Any], context: QgsProcessingContext) -> Tuple[bool, str]:
        success, msg = super().checkParameterValues(parameters, context)
        if success:
            msg_list = list()
            source = self.parameterAsSource(parameters, self.INPUT_OBSTACLES, context)
            if 'crest_level' not in source.fields().names():
                msg_list.append('Obstacle lines layer does not contain crest_level field')
            success = len(msg_list) == 0
            msg = '; '.join(msg_list)
        return success, msg

    def processAlgorithm(self, parameters, context, feedback):
        gridadmin_fn = self.parameterAsFile(parameters, self.INPUT_GRIDADMIN, context)
        gr = GridH5Admin(gridadmin_fn)
        dem = self.parameterAsRasterLayer(parameters, self.INPUT_DEM, context)
        dem_fn = dem.dataProvider().dataSourceUri()
        dem_ds = gdal.Open(dem_fn)
        obstacles_source = self.parameterAsSource(parameters, self.INPUT_OBSTACLES, context)
        min_obstacle_height = self.parameterAsDouble(parameters, self.INPUT_MIN_OBSTACLE_HEIGHT, context)
        search_precision = self.parameterAsDouble(parameters, self.INPUT_SEARCH_PRECISION, context)

        crs = QgsCoordinateReferenceSystem(f"EPSG:{gr.epsg_code}")

        edges_sink_fields = QgsFields()
        edges_sink_fields.append(QgsField(name="id", type=QVariant.Int))
        edges_sink_fields.append(QgsField(name="exchange_level", type=QVariant.Double))
        edges_sink_fields.append(QgsField(name="crest_level", type=QVariant.Double))
        (edges_sink, self.edges_sink_dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT_EDGES,
            context,
            fields=edges_sink_fields,
            geometryType=QgsWkbTypes.LineString,
            crs=crs
        )

        obstacles_sink_fields = QgsFields()
        obstacles_sink_fields.append(QgsField(name="id", type=QVariant.Int))
        obstacles_sink_fields.append(QgsField(name="exchange_level", type=QVariant.Double))
        obstacles_sink_fields.append(QgsField(name="crest_level", type=QVariant.Double))
        (obstacles_sink, self.obstacles_sink_dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT_OBSTACLES,
            context,
            fields=obstacles_sink_fields,
            geometryType=QgsWkbTypes.LineString,
            crs=crs
        )

        feedback.setProgressText("Read linear obstacles input...")
        crest_level_field_idx = obstacles_source.fields().indexFromName("crest_level")

        input_obstacles = list()
        for input_obstacle in obstacles_source.getFeatures():
            geom = wkt.loads(input_obstacle.geometry().asWkt())
            crest_level = float(input_obstacle[crest_level_field_idx])
            input_obstacles.append((geom, crest_level))

        feedback.setProgressText("Read computational grid...")
        leak_detector = LeakDetector(
            gridadmin=gr,
            dem=dem_ds,
            cell_ids=list(gr.cells.id),
            min_obstacle_height=min_obstacle_height,
            search_precision=search_precision,
            min_peak_prominence=min_obstacle_height,
            obstacles=input_obstacles,
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

        for result in leak_detector.result_obstacles():
            if feedback.isCanceled():
                return
            feature = QgsFeature()
            feature.setFields(obstacles_sink_fields)
            feature.setAttribute(0, int(result["flowline_id"]))
            feature.setAttribute(1, float(result["exchange_level"]))
            feature.setAttribute(2, float(result["crest_level"]))
            geometry = QgsGeometry()
            geometry.fromWkb(result["geometry"].wkb)
            feature.setGeometry(geometry)
            obstacles_sink.addFeature(feature, QgsFeatureSink.FastInsert)

        return {
            self.OUTPUT_EDGES: self.edges_sink_dest_id,
            self.OUTPUT_OBSTACLES: self.obstacles_sink_dest_id
        }

    def postProcessAlgorithm(self, context, feedback):
        """Set styling of output vector layers"""
        edges_layer = context.getMapLayer(self.edges_sink_dest_id)
        edges_layer.loadNamedStyle(str(STYLE_DIR / "obstacle_on_cell_edge.qml"))

        obstacles_layer = context.getMapLayer(self.obstacles_sink_dest_id)
        obstacles_layer.loadNamedStyle(str(STYLE_DIR / "obstacle_in_dem.qml"))

        return {
            self.OUTPUT_EDGES: self.edges_sink_dest_id,
            self.OUTPUT_OBSTACLES: self.obstacles_sink_dest_id
        }

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
                <h3>Introduction</h3>
                <p>The elevation at which flow between 2D cells is possible (the 'exchange level'), depends on the elevation of the pixels directly adjacent to the cell edge. Obstacles in the DEM that do not cover the entire edge will therefore not stop the flow, i.e. water 'leaks' through the obstacle. This is more likely to occur if obstacles are diagonal and/or narrow compared to the computational grid size.</p>
                <p>This processing algorithm detects such cases. Please inspect the locations where the algorithm identifies leaking obstacles and add grid refinement and/or obstacles to the schematisation to solve the issue if needed.</p>
                <h3>Parameters</h3>
                <h4>Gridadmin file</h4>
                <p>HDF-file (*.h5) containing a 3Di computational grid. Note that gridadmin files generated on the server contain exchange levels for 2D flowlines, whereas locally generated gridadmin files do not. In the latter case, the processing algorithm will analyse the DEM to obtain these values.</p>
                <h4>Digital elevation model</h4>
                <p>Raster of the schematisation's digital elevation model (DEM).</p>
                <h4>Linear obstacles</h4>
                <p>Obstacles in this layer will be used to update cell edge exchange levels, <i>in addition to</i> any obstacles already present in the gridadmin file (i.e. in files that were downloaded from the server). This input must be a vector layer with line geometry and a <i>crest_level</i> field</p>
                <h4>Minimum obstacle height (m)</h4>
                <p>Only obstacles with a crest level that is significantly higher than the exchange level will be identified. 'Significantly higher' is defined as <em>crest level &gt; exchange level + minimum obstacle height</em>.</p>
                <h4>Vertical search precision (m)</h4>
                <p>The crest level found by the obstacle will always be within <em>vertical search precision</em> of the actual crest level. A smaller value will yield more precise results; a higher value will make the algorithm faster to execute.</p>
                <h3>Outputs</h3>
                <h4>Obstacle in DEM&nbsp;</h4>
                <p>Approximate location of the obstacle in the DEM. Its geometry is a straight line between the highest pixels of the obstacle on the cell edges. Attributes:</p>
                <ul>
                <li> id: id of the flowline this obstacle affects. If more than one flowline is affected, the flowline with the lowest exchange level is used. </li>
                <li> crest_level: lowest elevation at which water can flow over the obstacle </li>
                <li> exchange_level: lowest exchange level of the cell edge(s) that this obstacle applies to </li>
                </ul>
                <p>The styling is shows the difference between the crest level and the exchange level</p>
                <h4>Obstacle on cell edge</h4>
                <p>Suggested obstacle to add to the schematisation. In most cases, it is recommended solve any leaking obstacle issues with grid refinement, and only add obstacles if this does not solve the issue.</p>
                <p>The styling is shows the difference between the crest level and the exchange level</p>
            """
        )

    def tr(self, string):
        return QCoreApplication.translate("Processing", string)

    def createInstance(self):
        return DetectLeakingObstaclesAlgorithm()
