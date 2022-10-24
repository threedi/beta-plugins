from epsg import *

EXTENT_FN = "C:/Temp/3Di Global/test_extent_india.shp"


def test_get_zone():
    lat = 32
    lon = 76
    zone = get_zone(longitude=lon, latitude=lat)
    print(zone)
    assert zone == 43


def test_find_utm_zone_epsg():
    lat = 32
    lon = 76
    epsg = find_utm_zone_epsg(longitude=lon, latitude=lat)
    print(epsg)
    assert epsg == 32643


def test_centroid_lon_lat():
    datasource = ogr.Open(EXTENT_FN)
    layer = datasource.GetLayer(0)
    srs = layer.GetSpatialRef()
    feature = layer.GetFeature(0)
    geom = feature.GetGeometryRef()
    centroid_lat, centroid_lon = centroid_lat_lon(geom, srs)
    print(centroid_lat, centroid_lon)
    assert int(centroid_lat) == 32
    assert int(centroid_lon) == 76


def test_utm_zone_epsg_for_polygon():
    datasource = ogr.Open(EXTENT_FN)
    layer = datasource.GetLayer(0)
    srs = layer.GetSpatialRef()
    feature = layer.GetFeature(0)
    geom = feature.GetGeometryRef()
    epsg = utm_zone_epsg_for_polygon(geom=geom, srs=srs)
    print(epsg)
    assert epsg == 32643


test_get_zone()
test_find_utm_zone_epsg()
test_centroid_lon_lat()
test_find_utm_zone_epsg()
