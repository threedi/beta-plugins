# Source: https://gis.stackexchange.com/questions/365584/convert-utm-zone-into-epsg-code
import math
from osgeo import ogr
from osgeo import osr
from typing import List, Tuple


# Special zones for Svalbard and Norway
def get_zone(latitude, longitude):
    if 72.0 <= latitude < 84.0:
        if 0.0 <= longitude < 9.0:
            return 31
    if 9.0 <= longitude < 21.0:
        return 33
    if 21.0 <= longitude < 33.0:
        return 35
    if 33.0 <= longitude < 42.0:
        return 37
    return (math.floor((longitude + 180) / 6)) + 1


def find_utm_zone_epsg(latitude, longitude):
    zone = get_zone(latitude, longitude)
    epsg_code = 32600
    epsg_code += int(zone)
    if latitude < 0:  # South
        epsg_code += 100
    return epsg_code


def xy_to_wgs84_lat_lon(
    x: float, y: float, srs: osr.SpatialReference
) -> Tuple[float, float]:
    wgs84_srs = osr.SpatialReference()
    wgs84_srs.ImportFromEPSG(4326)
    ct = osr.CoordinateTransformation(srs, wgs84_srs)
    lat, lon, z = ct.TransformPoint(x, y)
    return lat, lon


def centroid_lat_lon(geom: ogr.Geometry, srs: osr.SpatialReference):
    centroid = geom.Centroid()
    x = centroid.GetX()
    y = centroid.GetY()
    lat, lon = xy_to_wgs84_lat_lon(x, y, srs)
    return lat, lon


def transform_bounding_box(bounding_box: List, source_epsg: int, target_epsg: int) -> List:
    """

    :param bounding_box: [minx, maxx, miny, maxy]
    :param source_epsg: int
    :param target_epsg: int
    :return: [minx, maxx, miny, maxy]
    """
    minx, maxx, miny, maxy = bounding_box
    source_srs = osr.SpatialReference()
    source_srs.ImportFromEPSG(int(source_epsg))
    target_srs = osr.SpatialReference()
    target_srs.ImportFromEPSG(int(target_epsg))
    ct = osr.CoordinateTransformation(source_srs, target_srs)
    minx_result, miny_result, _z = ct.TransformPoint(minx, miny)
    maxx_result, maxy_result, _z = ct.TransformPoint(maxx, maxy)
    result = [minx_result, maxx_result, miny_result, maxy_result]
    return result


def transform_layer(layer: ogr.Layer, dest_datasource: ogr.DataSource, dest_layer_name: str, source_epsg: int, dest_epsg: int):
    """Adapted from https://pcjericks.github.io/py-gdalogr-cookbook/projection.html"""
    # input SpatialReference
    source_srs = osr.SpatialReference()
    source_srs.ImportFromEPSG(int(source_epsg))

    # output SpatialReference
    dst_srs = osr.SpatialReference()
    dst_srs.ImportFromEPSG(int(dest_epsg))

    ct = osr.CoordinateTransformation(source_srs, dst_srs)
    dest_layer = dest_datasource.CreateLayer(dest_layer_name, dst_srs, geom_type=layer.GetGeomType())

    src_layer_defn = layer.GetLayerDefn()
    for i in range(0, src_layer_defn.GetFieldCount()):
        field_defn = src_layer_defn.GetFieldDefn(i)
        dest_layer.CreateField(field_defn)

    dst_layer_defn = dest_layer.GetLayerDefn()
    src_feature = layer.GetNextFeature()
    while src_feature:
        geom = src_feature.GetGeometryRef()
        geom.Transform(ct)
        dest_feature = ogr.Feature(dst_layer_defn)
        dest_feature.SetGeometry(geom)
        for i in range(0, dst_layer_defn.GetFieldCount()):
            dest_feature.SetField(dst_layer_defn.GetFieldDefn(i).GetNameRef(), src_feature.GetField(i))
        dest_layer.CreateFeature(dest_feature)
        dest_feature = None
        src_feature = layer.GetNextFeature()

