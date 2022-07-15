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
from pathlib import Path
from qgis.core import QgsCoordinateReferenceSystem
from qgis.core import QgsFeature
from qgis.core import QgsFeatureSink
from qgis.core import QgsField
from qgis.core import QgsFields
from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingContext
from qgis.core import QgsProcessingParameterNumber
from qgis.core import QgsProcessingParameterEnum
from qgis.core import QgsProcessingParameterFeatureSink
from qgis.core import QgsProcessingParameterFeatureSource
from qgis.core import QgsProcessingParameterFile
from qgis.core import QgsProcessingParameterFileDestination
from qgis.core import QgsProcessingParameterString
from qgis.core import QgsVectorLayer
from qgis.core import QgsWkbTypes
from qgis.PyQt.QtCore import (QCoreApplication, QVariant)
from shapely import wkt
from threedigrid.admin.gridresultadmin import GridH5ResultAdmin
from threedigrid.admin.constants import TYPE_V2_CHANNEL
from threedigrid.admin.constants import TYPE_V2_CULVERT
from threedigrid.admin.constants import TYPE_V2_PIPE
from threedigrid.admin.constants import TYPE_V2_ORIFICE
from threedigrid.admin.constants import TYPE_V2_WEIR

from ..cross_sectional_discharge import left_to_right_discharge_ogr
from ..ogr2qgis import ogr_feature_as_qgis_feature


MEMORY_DRIVER = ogr.GetDriverByName("MEMORY")
STYLE_DIR = Path(__file__).parent.parent / "style"

class CrossSectionalDischargeAlgorithm(QgsProcessingAlgorithm):
    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    GRIDADMIN_INPUT = "GRIDADMIN_INPUT"
    RESULTS_3DI_INPUT = "RESULTS_3DI_INPUT"
    CROSS_SECTION_LINES_INPUT = "CROSS_SECTION_LINES_INPUT"
    START_TIME = "START_TIME"
    END_TIME = "END_TIME"
    SUBSET = "SUBSET"
    INCLUDE_TYPES_1D = "INCLUDE_TYPES_1D"
    FIELD_NAME_INPUT = "FIELD_NAME_INPUT"
    OUTPUT_CROSS_SECTION_LINES = "OUTPUT_CROSS_SECTION_LINES"
    OUTPUT_FLOWLINES = "OUTPUT_FLOWLINES"
    OUTPUT_TIME_SERIES = "OUTPUT_TIME_SERIES"

    # These are not algorithm parameters:
    SUBSET_NAMES = ["2D Surface flow", "2D Groundwater flow", "1D flow"]
    SUBSETS = ["2D_OPEN_WATER", "2D_GROUNDWATER", "1D"]

    TYPES_1D_NAMES = ["Channel", "Culvert", "Pipe", "Orifice", "Weir"]
    TYPES_1D = [TYPE_V2_CHANNEL, TYPE_V2_CULVERT, TYPE_V2_PIPE, TYPE_V2_ORIFICE, TYPE_V2_WEIR]

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
                self.CROSS_SECTION_LINES_INPUT,
                self.tr('Cross-section lines input'),
                [QgsProcessing.TypeVectorLine]
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.START_TIME, 'Start time (s)',
                type=QgsProcessingParameterNumber.Integer,
                optional=True
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.END_TIME, 'End time (s)',
                type=QgsProcessingParameterNumber.Integer,
                optional=True
            )
        )

        self.addParameter(
            QgsProcessingParameterEnum(
                self.SUBSET, 
                'Subset', 
                options=self.SUBSET_NAMES, 
                optional=True
            )
        )

        self.addParameter(
            QgsProcessingParameterEnum(
                self.INCLUDE_TYPES_1D,
                '1D Flowline types to include',
                options=self.TYPES_1D_NAMES,
                allowMultiple=True,
                defaultValue=list(range(len(self.TYPES_1D))),  # all enabled
                optional=True
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_FLOWLINES,
                self.tr('Output: Intersected flowlines'),
                type=QgsProcessing.TypeVectorLine
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_CROSS_SECTION_LINES,
                self.tr('Output: Cross-section lines'),
                type=QgsProcessing.TypeVectorLine
            )
        )

        self.addParameter(
            QgsProcessingParameterString(
                self.FIELD_NAME_INPUT,
                self.tr('Output field name'),
                defaultValue="q_net_sum"
            )
        )

        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT_TIME_SERIES, self.tr("Output: Timeseries"), fileFilter="*.csv"
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        gridadmin_fn = self.parameterAsFile(parameters, self.GRIDADMIN_INPUT, context)
        results_3di_fn = self.parameterAsFile(parameters, self.RESULTS_3DI_INPUT, context)
        gr = GridH5ResultAdmin(gridadmin_fn, results_3di_fn)
        cross_section_lines_source = self.parameterAsSource(parameters, self.CROSS_SECTION_LINES_INPUT, context)
        start_time = self.parameterAsInt(parameters, self.START_TIME, context) \
            if parameters[self.START_TIME] is not None else None  # use `is not None` to handle `== 0` properly
        end_time = self.parameterAsInt(parameters, self.END_TIME, context) \
            if parameters[self.END_TIME] is not None else None  # use `is not None` to handle `== 0` properly
        subset = self.SUBSETS[parameters[self.SUBSET]] \
            if parameters[self.SUBSET] is not None else None  # use `is not None` to handle `== 0` properly
        feedback.pushInfo(f"Using subset: {subset}")
        content_types = [self.TYPES_1D[i] for i in parameters[self.INCLUDE_TYPES_1D]]
        feedback.pushInfo(f"Using content_types: {content_types}")
        field_name = self.parameterAsString(parameters, self.FIELD_NAME_INPUT, context)
        self.csv_output_file_path = self.parameterAsFileOutput(parameters, self.OUTPUT_TIME_SERIES, context)
        self.csv_output_file_path = f"{os.path.splitext(self.csv_output_file_path)[0]}.csv"

        flowlines_sink_fields = QgsFields()
        flowlines_sink_fields.append(QgsField(name='id', type=QVariant.Int))
        flowlines_sink_fields.append(QgsField(name='spatialite_id', type=QVariant.Int))
        flowlines_sink_fields.append(QgsField(name='content_type', type=QVariant.String))
        flowlines_sink_fields.append(QgsField(name='kcu', type=QVariant.Int))
        flowlines_sink_fields.append(QgsField(name='kcu_description', type=QVariant.String))
        flowlines_sink_fields.append(QgsField(name='gauge_line_id', type=QVariant.Int))
        flowlines_sink_fields.append(QgsField(name='q_net_sum', type=QVariant.Double))

        crs = QgsCoordinateReferenceSystem(f"EPSG:{gr.epsg_code}")
        (flowlines_sink, self.flowlines_sink_dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT_FLOWLINES,
            context,
            fields=flowlines_sink_fields,
            geometryType=QgsWkbTypes.LineString,
            crs=crs
        )

        cross_section_lines_sink_fields = QgsFields()
        cross_section_lines_sink_fields.append(QgsField(name='id', type=QVariant.Int))
        cross_section_lines_sink_fields.append(QgsField(name=field_name, type=QVariant.Double))
        (cross_section_lines_sink, self.cross_section_lines_sink_dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT_CROSS_SECTION_LINES,
            context,
            fields=cross_section_lines_sink_fields,
            geometryType=QgsWkbTypes.LineString,
            crs=cross_section_lines_source.sourceCrs()
        )
        
        feedback.setProgress(0)
        for i, gauge_line in enumerate(cross_section_lines_source.getFeatures()):
            if feedback.isCanceled():
                return {}
            feedback.setProgressText(f"Processing cross-section line {gauge_line.id()}...")
            shapely_linestring = wkt.loads(gauge_line.geometry().asWkt())
            tgt_ds = MEMORY_DRIVER.CreateDataSource("")
            ts_gauge_line, total_discharge = left_to_right_discharge_ogr(
                gr=gr,
                gauge_line=shapely_linestring,
                tgt_ds=tgt_ds,
                gauge_line_id=gauge_line.id(),
                start_time=start_time,
                end_time=end_time,
                subset=subset,
                content_types=content_types
            )
            feedback.pushInfo(f"Net sum of discharge for cross-section line {gauge_line.id()}: {total_discharge}")
            if i == 0:
                ts_all_cross_section_lines = ts_gauge_line
                column_names = ['"timestep"', f'"{gauge_line.id()}"']
                formatting = ["%d", "%.6f"]
            else:
                ts_all_cross_section_lines = np.column_stack([ts_all_cross_section_lines, ts_gauge_line[:, 1]])
                column_names.append(f'"{gauge_line.id()}"')
                formatting.append("%.6f")
            gaugeline_feature = QgsFeature(cross_section_lines_sink_fields)
            gaugeline_feature[0] = gauge_line.id()
            gaugeline_feature[1] = float(total_discharge)
            gaugeline_feature.setGeometry(gauge_line.geometry())
            cross_section_lines_sink.addFeature(
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
            feedback.setProgress(100 * i / cross_section_lines_source.featureCount())


        np.savetxt(
            self.csv_output_file_path,
            ts_all_cross_section_lines,
            delimiter=",",
            header=",".join(column_names),
            fmt=formatting,
            comments=""
        )
        layer = QgsVectorLayer(self.csv_output_file_path, "Time series output")
        context.temporaryLayerStore().addMapLayer(layer)
        layer_details = QgsProcessingContext.LayerDetails(
            "Output: Timeseries", context.project(), "Output: Timeseries"
        )
        context.addLayerToLoadOnCompletion(layer.id(), layer_details)

        return {
            self.OUTPUT_FLOWLINES: self.flowlines_sink_dest_id,
            self.OUTPUT_CROSS_SECTION_LINES: self.cross_section_lines_sink_dest_id,
            self.OUTPUT_TIME_SERIES: self.csv_output_file_path
        }

    def postProcessAlgorithm(self, context, feedback):
        """Set styling of output vector layers"""
        cross_section_lines_output_layer = context.getMapLayer(self.cross_section_lines_sink_dest_id)
        cross_section_lines_output_layer.loadNamedStyle(str(STYLE_DIR / "cross_sectional_discharge.qml"))
        flowlines_output_layer = context.getMapLayer(self.flowlines_sink_dest_id)
        flowlines_output_layer.loadNamedStyle(str(STYLE_DIR / "cross_sectional_discharge_flowlines.qml"))

        return {
            self.OUTPUT_FLOWLINES: self.flowlines_sink_dest_id,
            self.OUTPUT_CROSS_SECTION_LINES: self.cross_section_lines_sink_dest_id,
            self.OUTPUT_TIME_SERIES: self.csv_output_file_path
        }


    def name(self):
        return "crosssectionaldischarge"

    def displayName(self):
        return self.tr("Cross-sectional discharge")

    def group(self):
        return self.tr("Discharge")

    def groupId(self):
        return "Discharge"

    def shortHelpString(self):
        return self.tr(
            "Calculate total net discharge over a gauge line. \n\n The sign (positive/negative) of the output "
            "values depend on the drawing direction of the gauge line. Positive values indicate flow from "
            "the left-hand side of the gauge line to the right-hand side. Negative values indicate flow from right "
            "to left.\n\n"
            "Specify start time (in seconds since start of simulation) to exclude all data before that time.\n\n"
            "Specify end time (in seconds since start of simulation) to exclude all data after that time.\n\n"
            "Specify output field name to write the results to a specific field. Useful for combining results of "
            "multiple simulations in one output layer\n\n"
            "By choosing a subset, you can tell the algorithm to limit the analysis to flowlines in a specific "
            "domain.\n\n"
            "Further filtering of specific 1D flowlines can be achieved by changing '1D Flowline types to include' "
            "settings. This does not affect 2D or 1D/2D flowlines.\n\n"
        )

    def tr(self, string):
        return QCoreApplication.translate("Processing", string)

    def createInstance(self):
        return CrossSectionalDischargeAlgorithm()
