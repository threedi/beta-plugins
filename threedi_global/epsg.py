# Source: https://gis.stackexchange.com/questions/365584/convert-utm-zone-into-epsg-code
import math
from osgeo import ogr
from osgeo import osr


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


def centroid_lat_lon(geom: ogr.Geometry, srs: osr.SpatialReference):
    wgs84_srs = osr.SpatialReference()
    wgs84_srs.ImportFromEPSG(4326)
    ct = osr.CoordinateTransformation(srs, wgs84_srs)
    centroid = geom.Centroid()
    x = centroid.GetX()
    y = centroid.GetY()
    lat, lon, z = ct.TransformPoint(x, y)
    return lat, lon


def utm_zone_epsg_for_polygon(geom: ogr.Geometry, srs: osr.SpatialReference):
    lat, lon = centroid_lat_lon(geom, srs)
    utm_zone_epsg = find_utm_zone_epsg(lat, lon)
    return utm_zone_epsg

