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
    QgsProcessingAlgorithm,
    QgsProcessingContext,
    QgsCoordinateTransform,
    QgsCoordinateReferenceSystem,
    QgsFeature,
    QgsField,
    QgsFields,
    QgsProject
)
import processing

from .raster_tools.dem_sampler import AttributeProcessor
from .test_rasterize_channel.test_oo import run_tests


class MesherizeChannelsAlgorithm(QgsProcessingAlgorithm):
    """
    Rasterize channels using its cross sections
    """
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config):
        pass

    def processAlgorithm(self, parameters, context, feedback):
        output_layer_name = "Channel as mesh"
        points = run_tests()
        qgs_points = [QgsPoint(*point.coords[0]) for point in points]
        uri = "pointz?crs=epsg:28992&field=id:integer"
        layer = QgsVectorLayer(uri, output_layer_name, "memory")
        fields = QgsFields()
        id_field = QgsField(name='id', type=QVariant.Int)
        fields.append(id_field)
        features = dict()
        for i, point in enumerate(qgs_points):
            features[i] = QgsFeature(fields)
            features[i].setGeometry(point)

        layer.dataProvider().addFeatures(features.values())
        context.temporaryLayerStore().addMapLayer(layer)
        layer_details = QgsProcessingContext.LayerDetails(output_layer_name, context.project(), self.OUTPUT)
        context.addLayerToLoadOnCompletion(layer.id(), layer_details)
        return {self.OUTPUT: layer.id()}

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
