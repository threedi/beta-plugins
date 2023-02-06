from osgeo import ogr
from qgis.core import (
    QgsVectorLayer,
    QgsFeature,
    QgsWkbTypes,
    QgsGeometry,
)

FIELD_TYPES = {
    ogr.OFTInteger: "integer",  # OFTInteger, Simple 32bit integer
    ogr.OFTReal: "double",  # OFTReal, Double Precision floating point
    ogr.OFTString: "string",  # OFTString, String of ASCII chars
}

GEOMETRY_TYPES = {  # See full list: https://gdal.org/doxygen/ogr__core_8h.html, search for OGRwkbGeometryType
    1: "Point",
    2: "Linestring",
    3: "Polygon",
    4: "MultiPoint",
    5: "MultiLinestring",
    6: "MultiPolygon",
}


def field_defn_as_uri_param(field_defn):
    """
    Converts an OGR field definition to a QgsVectorLayer uri field parameter string
    :param field_defn: ogr.FeatureDefn
    :return: str
    """
    name = field_defn.GetName()
    type = FIELD_TYPES[field_defn.GetType()]
    length = field_defn.GetWidth()
    precision = field_defn.GetPrecision()

    uri_param = "field=" + name + ":" + type
    if length is not None and length != 0:
        uri_param += "(" + str(length)
        if precision is not None and length != 0:
            uri_param += "," + str(precision)
        uri_param += ")"
    return uri_param


def layer_as_uri(layer, index=True):
    """
    Converts an OGR feature definition to a QgsVectorLayer uri field parameters string
    :param field_defn: ogr.FeatureDefn
    :return: str
    """
    other_params = []

    # geometry
    geom_param = GEOMETRY_TYPES[layer.GetGeomType()]

    # crs (only EPSG code style crs are supported)
    auth_name = layer.GetSpatialRef().GetAuthorityName(None)
    if auth_name == "EPSG":
        auth_code = layer.GetSpatialRef().GetAuthorityCode(None)
        crs_param = "crs=epsg:" + str(auth_code)
    else:
        raise Exception("Layer does not have a EPSG coded crs")
    other_params.append(crs_param)

    # fields
    feature_defn = layer.GetLayerDefn()
    field_uris = []
    for i in range(feature_defn.GetFieldCount()):
        field_uris.append(
            field_defn_as_uri_param(feature_defn.GetFieldDefn(i))
        )

    other_params += field_uris

    # index
    if index:
        index_param = "index=yes"
        other_params.append(index_param)

    return geom_param + "?" + "&".join(other_params)


def ogr_feature_as_qgis_feature(
    ogr_feature, qgs_vector_lyr, tgt_wkb_type=None, tgt_fields=None
):
    # start_time = time.perf_counter()
    # f = open("C:\\Users\\leendert.vanwolfswin\\Downloads\\ogr_feature_as_qgis_feature.log", "a+")
    # f.write('action; time\n')

    # geometry
    ogr_geom_ref = ogr_feature.GetGeometryRef()
    if tgt_wkb_type is None:
        tgt_wkb_type = qgs_vector_lyr.wkbType()
    if not QgsWkbTypes.hasZ(tgt_wkb_type):
        ogr_geom_ref.FlattenTo2D()
    ogr_geom_wkb = ogr_geom_ref.ExportToWkb()
    qgs_geom = QgsGeometry()
    qgs_geom.fromWkb(ogr_geom_wkb)

    # delta_time=time.perf_counter() - start_time
    # f.write('Create QgsGeometry;{}\n'.format(str(delta_time)))

    # attributes
    # attributes = {}
    # for idx, field in enumerate(qgs_vector_lyr.fields()):
    #     ogr_field_idx = ogr_feature.GetFieldIndex(field.name())
    #     ogr_field_value = ogr_feature.GetField(ogr_field_idx)
    #     attributes[idx] = ogr_field_value
    attributes = []
    if tgt_fields is None:
        tgt_fields = qgs_vector_lyr.fields()
    for field in tgt_fields:
        ogr_field_idx = ogr_feature.GetFieldIndex(field.name())
        if ogr_field_idx != -1:
            ogr_field_value = ogr_feature.GetField(ogr_field_idx)
            attributes.append(ogr_field_value)

    # delta_time=time.perf_counter() - start_time
    # f.write('Make attribute dict;{}\n'.format(str(delta_time)))

    qgs_feature = QgsFeature()
    qgs_feature.setGeometry(qgs_geom)
    qgs_feature.setAttributes(attributes)
    # qgs_feature = QgsVectorLayerUtils.createFeature(target_node_layer=qgs_vector_lyr,
    #                                                 geometry=qgs_geom,
    #                                                 attributes=attributes
    #                                                 )

    # delta_time=time.perf_counter() - start_time
    # f.write('Create QgsFeature;{}\n'.format(str(delta_time)))
    #
    # f.close()

    return qgs_feature


def append_to_qgs_vector_layer(ogr_layer, qgs_vector_layer):
    qgs_features = []
    for ogr_feature in ogr_layer:
        qgs_feature = ogr_feature_as_qgis_feature(
            ogr_feature, qgs_vector_layer
        )
        qgs_features.append(qgs_feature)

    # qgs_vector_layer.startEditing()
    qgs_vector_layer.dataProvider().addFeatures(qgs_features)
    # qgs_vector_layer.commitChanges()


def as_qgis_memory_layer(ogr_layer, base_name):
    """
    Creates a QgsVectorLayer from an in memory ogr Layer
    :param base_name: name of output qgis target_node_layer
    :param ogr_layer: osgeo.ogr.Layer
    :return: qgis.core.QgsVectorLayer
    """
    # start_time = time.perf_counter()
    # f = open("C:\\Users\\leendert.vanwolfswin\\Downloads\\as_qgis_memory_layer.log", "w+")

    uri = layer_as_uri(ogr_layer)
    qgs_vector_layer = QgsVectorLayer(
        path=uri,
        baseName=base_name,
        providerLib="memory",
        options=QgsVectorLayer.LayerOptions(),
    )

    append_to_qgs_vector_layer(
        ogr_layer=ogr_layer, qgs_vector_layer=qgs_vector_layer
    )

    return qgs_vector_layer


# ## testing
# test_data = "C:/Users/leendert.vanwolfswin/Documents/threedi_custom_stats_test_data/minipyltjes.gpkg"
# ogr_file = ogr.Open(test_data)
# lyr = ogr_file.GetLayerByName('minipyltjes')
# qgs_lyr = as_qgis_memory_layer(lyr, 'mymemlyr4')
#
# project.addMapLayer(qgs_lyr)
