# -*- coding: utf-8 -*-

"""
/***************************************************************************
 CrossSectionalDischargeAlgorithm
                                 A QGIS plugin
 Calculates net total discharge over a gauge line
                              -------------------
        begin                : 2022-04-18
        copyright            : (C) 2022 by Nelen en Schuurmans
        email                : leendert.vanwolfswinkel@nelen-schuurmans.nl
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = "Nelen en Schuurmans"
__date__ = "2022-04-18"
__copyright__ = "(C) 2022 by Nelen en Schuurmans"

# This will get replaced with a git SHA1 when you do a git archive
__revision__ = "$Format:%H$"

import numpy as np
import os
from osgeo import ogr
from qgis.core import QgsCoordinateReferenceSystem
from qgis.core import QgsFeature
from qgis.core import QgsFeatureSink
from qgis.core import QgsField
from qgis.core import QgsFields
from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingContext
from qgis.core import QgsProcessingParameterFeatureSink
from qgis.core import QgsProcessingParameterFeatureSource
from qgis.core import QgsProcessingParameterFile
from qgis.core import QgsProcessingParameterFileDestination
from qgis.core import QgsVectorLayer
from qgis.core import QgsWkbTypes
from qgis.PyQt.QtCore import (QCoreApplication, QVariant)
from shapely import wkt
from threedigrid.admin.gridresultadmin import GridH5ResultAdmin

from ..cross_sectional_discharge import left_to_right_discharge_ogr
from ..ogr2qgis import ogr_feature_as_qgis_feature


MEMORY_DRIVER = ogr.GetDriverByName("MEMORY")


class CrossSectionalDischargeAlgorithm(QgsProcessingAlgorithm):
    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    GRIDADMIN_INPUT = "GRIDADMIN_INPUT"
    RESULTS_3DI_INPUT = "RESULTS_3DI_INPUT"
    GAUGE_LINE_INPUT = "GAUGE_LINES_INPUT"
    FIELD_NAME_INPUT = "FIELD_NAME_INPUT"
    OUTPUT_GAUGE_LINES = "OUTPUT_GAUGE_LINES"
    OUTPUT_FLOWLINES = "OUTPUT_FLOWLINES"
    OUTPUT_TIME_SERIES = "OUTPUT_TIME_SERIES"

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        self.addParameter(
            QgsProcessingParameterFile(
                self.GRIDADMIN_INPUT, self.tr("Gridadmin file"), extension="h5"
            )
        )
        self.addParameter(
            QgsProcessingParameterFile(
                self.RESULTS_3DI_INPUT, self.tr("Results 3Di file"), extension="nc"
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.GAUGE_LINE_INPUT,
                self.tr('Gauge lines input'),
                [QgsProcessing.TypeVectorLine]
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_FLOWLINES,
                self.tr('Intersected flowlines'),
                type=QgsProcessing.TypeVectorLine
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_GAUGE_LINES,
                self.tr('Gauge lines output'),
                type=QgsProcessing.TypeVectorLine
            )
        )

        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT_TIME_SERIES, self.tr("Timeseries output"), fileFilter="csv"
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        gridadmin_fn = self.parameterAsFile(parameters, self.GRIDADMIN_INPUT, context)
        results_3di_fn = self.parameterAsFile(parameters, self.RESULTS_3DI_INPUT, context)
        gr = GridH5ResultAdmin(gridadmin_fn, results_3di_fn)
        gauge_lines_source = self.parameterAsSource(parameters, self.GAUGE_LINE_INPUT, context)
        csv_output_file_path = self.parameterAsFileOutput(
            parameters, self.OUTPUT_TIME_SERIES, context
        )
        csv_output_file_path = f"{os.path.splitext(csv_output_file_path)[0]}.csv"

        flowlines_sink_fields = QgsFields()
        flowlines_sink_fields.append(QgsField(name='id', type=QVariant.Int))
        flowlines_sink_fields.append(QgsField(name='spatialite_id', type=QVariant.Int))
        flowlines_sink_fields.append(QgsField(name='content_type', type=QVariant.String))
        flowlines_sink_fields.append(QgsField(name='kcu', type=QVariant.Int))
        flowlines_sink_fields.append(QgsField(name='kcu_description', type=QVariant.String))
        flowlines_sink_fields.append(QgsField(name='gauge_line_id', type=QVariant.Int))
        flowlines_sink_fields.append(QgsField(name='q_net_sum', type=QVariant.Double))

        crs = QgsCoordinateReferenceSystem(f"EPSG:{gr.epsg_code}")
        (flowlines_sink, flowlines_sink_dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT_FLOWLINES,
            context,
            fields=flowlines_sink_fields,
            geometryType=QgsWkbTypes.LineString,
            crs=crs
        )

        gaugelines_sink_fields = QgsFields()
        gaugelines_sink_fields.append(QgsField(name='id', type=QVariant.Int))
        gaugelines_sink_fields.append(QgsField(name='q_net_sum', type=QVariant.Double))
        (gaugelines_sink, gaugelines_sink_dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT_GAUGE_LINES,
            context,
            fields=gaugelines_sink_fields,
            geometryType=QgsWkbTypes.LineString,
            crs=gauge_lines_source.sourceCrs()
        )

        for i, gauge_line in enumerate(gauge_lines_source.getFeatures()):
            shapely_linestring = wkt.loads(gauge_line.geometry().asWkt())
            tgt_ds = MEMORY_DRIVER.CreateDataSource("")
            ts_gauge_line, total_discharge = left_to_right_discharge_ogr(
                gr=gr,
                gauge_line=shapely_linestring,
                tgt_ds=tgt_ds,
                gauge_line_id=gauge_line.id()
            )
            feedback.pushInfo(f"total discharge for gauge line {gauge_line.id()}: {total_discharge}")
            if i == 0:
                ts_all_gauge_lines = ts_gauge_line
                column_names = ['"timestep"', f'"{gauge_line.id()}"']
                formatting = ["%d", "%.6f"]
            else:
                ts_all_gauge_lines = np.column_stack([ts_all_gauge_lines, ts_gauge_line[:, 1]])
                column_names.append(f'"{gauge_line.id()}"')
                formatting.append("%.6f")
            gaugeline_feature = QgsFeature(gaugelines_sink_fields)
            gaugeline_feature[0] = gauge_line.id()
            gaugeline_feature[1] = float(total_discharge)
            gaugeline_feature.setGeometry(gauge_line.geometry())
            gaugelines_sink.addFeature(
                gaugeline_feature,
                QgsFeatureSink.FastInsert
            )
            ogr_layer = tgt_ds.GetLayerByName("flowline")
            for ogr_feature in ogr_layer:
                qgs_feature = ogr_feature_as_qgis_feature(
                    ogr_feature,
                    flowlines_sink,
                    tgt_wkb_type=QgsWkbTypes.LineString,
                    tgt_fields=flowlines_sink_fields
                )
                flowlines_sink.addFeature(qgs_feature, QgsFeatureSink.FastInsert)

        np.savetxt(
            csv_output_file_path,
            ts_all_gauge_lines,
            delimiter=",",
            header=",".join(column_names),
            fmt=formatting,
            comments=""
        )
        layer = QgsVectorLayer(csv_output_file_path, "Time series output")
        context.temporaryLayerStore().addMapLayer(layer)
        layer_details = QgsProcessingContext.LayerDetails(
            csv_output_file_path, context.project(), "Time series output"
        )
        context.addLayerToLoadOnCompletion(layer.id(), layer_details)

        return {
            self.OUTPUT_FLOWLINES: flowlines_sink_dest_id,
            self.OUTPUT_GAUGE_LINES: gaugelines_sink_dest_id,
            self.OUTPUT_TIME_SERIES: csv_output_file_path
        }

    def name(self):
        return "crosssectionaldischarge"

    def displayName(self):
        return self.tr("Cross-sectional discharge")

    def group(self):
        return self.tr("Analysis")

    def groupId(self):
        return "Analysis"

    def shortHelpString(self):
        return self.tr(
            "Calculate total net discharge over a gauge line. \n\n The sign (positive/negative) of the output "
            "values depend on the drawing direction of the gauge line. Positive values indicate flow from "
            "the left-hand side of the gauge line to the right-hand side. Negative values indicate flow from right "
            "to left."
        )

    def tr(self, string):
        return QCoreApplication.translate("Processing", string)

    def createInstance(self):
        return CrossSectionalDischargeAlgorithm()
