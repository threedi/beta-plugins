#!/usr/bin/env python
# coding: utf-8

from shapely.geometry import MultiPoint, Polygon, LineString
from shapely.wkb import loads
from osgeo import ogr, osr
import sqlite3
import gdal
from functools import partial
import pyproj
from shapely.ops import transform, nearest_points
import numpy as np
from typing import List

# to convert 4326 to 28992
project = partial(
    pyproj.transform,
    pyproj.Proj(init='epsg:4326'),
    pyproj.Proj(init='epsg:28992'))


def create_connection(db_file: str) -> sqlite3.Connection:
    """
    Create spatialite connection, return None if an Exception occurs

    :param db_file: .sqlite file name
    :return: spatialite connection
    """

    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Exception as e:
        print(e)

    return conn


def features_from_sqlite(sqlite: str, table: str) -> List:
    """
    Get list of geometries with their FID from a specific table in an sqlite.

    If the feature is a cross section location, the channel_id, definition_id and reference_level are also stored in
    the attributes.

    :param sqlite: filename of the spatialite database
    :param table: name of the table
    :return: List of enriched shapely geometries. The FID is stored in each item's id attribute.

    """
    shapely_objects = []
    ogrsqlite = ogr.Open(sqlite)
    layer = ogrsqlite.GetLayerByName(table)
    for n in range(0, layer.GetFeatureCount()):
        feat = layer.GetNextFeature()
        wkb_feat = loads(feat.GetGeometryRef().ExportToWkb())
        wkb_feat = transform(project, wkb_feat)
        wkb_feat.id = feat.GetFID()
        if table == "v2_cross_section_location":
            wkb_feat.channel_id = feat.channel_id
            wkb_feat.definition_id = feat.definition_id
            wkb_feat.reference_level = feat.reference_level
        shapely_objects.append(wkb_feat)
    return shapely_objects


def createChannelOutline(channel_widths, channel):
    """ Create polygon representing the channel shape based on widths at its vertices. """
    channel_widths.sort(key=lambda x: x[0])
    channel_widths.append([1.0, channel_widths[-1][1]])
    channel_widths.append([0.0, channel_widths[0][1]])
    channel_widths.sort(key=lambda x: x[0])
    x = [item[0] for item in channel_widths]
    y = [item[1] for item in channel_widths]
    vertices = list(MultiPoint(channel.coords))
    outline_points = []
    for vertex in vertices:
        channel_vertex_width = np.interp(channel.project(vertex, normalized=True), x, y)
        left = channel.parallel_offset(channel_vertex_width / 2, 'left')
        outline_points.append(nearest_points(vertex, left)[1])
    vertices.reverse()
    for vertex in vertices:
        channel_vertex_width = np.interp(channel.project(vertex, normalized=True), x, y)
        right = channel.parallel_offset(channel_vertex_width / 2, 'right')
        outline_points.append(nearest_points(vertex, right)[1])

    outline_points.append(outline_points[0])
    coords = [p.coords[:][0] for p in outline_points]
    poly = Polygon(coords)
    return poly


def two_sided_parallel_offsets(linestring, offset_dists):
    """
    Generate a set of lines parallel to the input linestring, at both sides of the line

    :param linestring: shapely linestring
    :param offset_dists: list of floats
    :return: list of shapely linestrings
    """
    parallel_offsets = []
    for width in offset_dists:
        parallel_offsets.append(linestring.parallel_offset(width / 2, 'left'))
    for width in offset_dists:
        parallel_offsets.append(linestring.parallel_offset(width / 2, 'right'))
    return parallel_offsets


def get_channel_widths(channel: LineString, cross_section_locations: list, sqlite: str):
    """
    Determine the maximum width and width/height relation for each cross section.

    :param channel: Shapely Linestring
    :param cross_section_locations: list of
    :param sqlite:
    :return: a list of lists of [position, max_width] and a list of widths
    """

    channel_max_widths = []
    channel_all_widths = []

    conn = create_connection(sqlite)
    cur = conn.cursor()

    for xsec in cross_section_locations:
        cur.execute("SELECT width, height FROM v2_cross_section_definition where id={}".format(xsec.definition_id))
        rows = cur.fetchall()
        for row in rows:
            definition = list(row)
            xsec.widths = list(map(float, definition[0].split()))
            xsec.heights = list(map(float, definition[1].split())) # heights relative to reference_level
            xsec.heights = [x + xsec.reference_level for x in xsec.heights] # absolute heights
        channel_all_widths += xsec.widths
        channel_max_widths.append([channel.project(xsec, normalized=True), max(xsec.widths)])
        channel_all_widths.sort()
    return channel_max_widths, channel_all_widths


def write_shapes_to_vsimem(all_points, channel_outline, points_ds=None, poly_ds=None, point_lyr=None, poly_lyr=None):
    # write elevation points along channel and outline polygon to in memory shapefile
    shape_drv = ogr.GetDriverByName('ESRI Shapefile')
    if points_ds == None:
        points_ds = shape_drv.CreateDataSource('/vsimem/tmp/points.shp')
        point_lyr = points_ds.CreateLayer('points')
    else:
        pass
    for point in all_points:
        wkt = 'POINT(%f %f %s)' % (point.x, point.y, point.height)
        dst_feat = ogr.Feature(feature_def=point_lyr.GetLayerDefn())
        dst_feat.SetGeometry(ogr.CreateGeometryFromWkt(wkt))
        point_lyr.CreateFeature(dst_feat)
    points_ds.ExecuteSQL('CREATE SPATIAL INDEX ON points')

    shape_drv = ogr.GetDriverByName('ESRI Shapefile')
    if poly_ds == None:
        poly_ds = shape_drv.CreateDataSource('/vsimem/tmp/channel_outline.shp')
        poly_lyr = poly_ds.CreateLayer('channel_outline')
    else:
        pass
    dst_feat = ogr.Feature(feature_def=poly_lyr.GetLayerDefn())
    dst_feat.SetGeometry(ogr.CreateGeometryFromWkt(channel_outline.wkt))
    poly_lyr.CreateFeature(dst_feat)
    poly_ds.ExecuteSQL('CREATE SPATIAL INDEX ON channel_outline')
    return points_ds, poly_ds, point_lyr, poly_lyr


def writeRaster(output_raster, geotransform, geoprojection, data):
    """
    write a numpy array to a gdal raster (geotiff, float32, compress=deflate, nodatavalue -9999)

    :param output_raster: filename of the output raster
    :param geotransform: gdal geotransform
    :param geoprojection: proj4 string
    :param data: 2d numpy array
    :return:
    """
    (y, x) = data.shape
    format = "GTiff"
    driver = gdal.GetDriverByName(format)
    dst_datatype = gdal.GDT_Float32
    dst_ds = driver.Create(output_raster, xsize=x, ysize=y, bands=1, eType=dst_datatype, options=['COMPRESS=DEFLATE'])
    dst_ds.GetRasterBand(1).WriteArray(data)
    dst_ds.SetGeoTransform(geotransform)
    dst_ds.SetProjection(geoprojection)
    dst_ds.GetRasterBand(1).SetNoDataValue(-9999)
    return


def interpolate_and_write_vrt():
    # interpolate elevation points into in memory geotiff
    grid_ds = gdal.Grid('/vsimem/tmp/raster.tif', '/vsimem/tmp/points.shp', format='MEM',
                     outputType=gdal.GDT_Float32,
                     algorithm='linear:nodata=-9999', width=2000, height=2000)

    # Code below is experiment for using raster-tools fill algorithm
    # ds2 = gdal.Rasterize('/vsimem/tmp/raster.tif',
    #                      '/vsimem/tmp/points.shp',
    #                      format='MEM',
    #                      outputType=gdal.GDT_Float32,
    #                      xRes=0.5,
    #                      yRes=0.5,
    #                      useZ=True,
    #                      initValues=-9999,
    #                      noData=-9999,
    #                      targetAlignedPixels=True,
    #                      )
    grid_clip_ds = gdal.Warp(destNameOrDestDS='/vsimem/out.tif', srcDSOrSrcDSTab=grid_ds,
                               cutlineDSName="/vsimem/tmp/channel_outline.shp", cropToCutline=True, dstNodata=-9999)
    return grid_clip_ds


def write_raster_to_gtiff(wdepth_clip_ds, output_raster):
    band = wdepth_clip_ds.GetRasterBand(1)
    geotransform = wdepth_clip_ds.GetGeoTransform()
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(28992)
    Z = band.ReadAsArray()
    writeRaster(output_raster, geotransform, srs.ExportToWkt(), Z)
    band = geotransform = geoproj = Z = None


def rasterize_channels(sqlite, output_raster, ids=[]):

    channels = features_from_sqlite(sqlite, "v2_channel")
    cross_section_locations = features_from_sqlite(sqlite, "v2_cross_section_location")
    conn = create_connection(sqlite)
    cur = conn.cursor()

    for channel in channels:
        if channel.id in ids or ids == []:
            # list all cross section locations belonging to the channel,
            # including its position (fraction) along the channel
            channel_xsecs = []
            for xsec_loc in cross_section_locations:
                if xsec_loc.channel_id == channel.id:
                    xsec_loc.position = channel.project(xsec_loc, normalized=True)
                    channel_xsecs.append(xsec_loc)

            channel_max_widths, channel_all_widths_flat = get_channel_widths(channel=channel,
                                                                             cross_section_locations=channel_xsecs,
                                                                             sqlite=sqlite)
            channel_offsets = two_sided_parallel_offsets(channel,
                                                         channel_all_widths_flat
                                                         )

            all_profiles_interpolated = {}
            for xsec in channel_xsecs:
                interpolated_height = []
                for width in channel_all_widths_flat:
                    interpolated_height.append(np.interp(width, xsec.widths, xsec.heights))
                all_profiles_interpolated[xsec.position] = interpolated_height
            all_profiles_interpolated[float(0)] = all_profiles_interpolated[min(all_profiles_interpolated.keys())]
            all_profiles_interpolated[float(1)] = all_profiles_interpolated[max(all_profiles_interpolated.keys())]
            x = list(all_profiles_interpolated.keys())
            x.sort()

            all_points = []
            for chn in range(1, len(channel_offsets)):
                line = channel_offsets[chn]
                y = []
                for loc in range(0, len(x)):
                    if chn > len(all_profiles_interpolated[x[0]]) - 1:
                        chn2 = chn - len(all_profiles_interpolated[x[0]])
                        y.append(all_profiles_interpolated[x[loc]][chn2])
                    else:
                        y.append(all_profiles_interpolated[x[loc]][chn])
                if chn > len(all_profiles_interpolated[0]):
                    line = LineString(line.coords[::-1])
                for i in range(1, round(line.length / 2)):
                    point = line.interpolate(2 * i / line.length, normalized=True)
                    point.height = np.interp(channel.project(point, normalized=True), x, y)
                    all_points.append(point)

            channel_outline = createChannelOutline(channel_max_widths, channel)
            if 'points_ds' in locals():
                points_ds, poly_ds, point_lyr, poly_lyr = write_shapes_to_vsimem(all_points, channel_outline, points_ds,
                                                                                 poly_ds, point_lyr, poly_lyr)
            else:
                points_ds, poly_ds, point_lyr, poly_lyr = write_shapes_to_vsimem(all_points, channel_outline)

    wdepth_clip_ds = interpolate_and_write_vrt()
    write_raster_to_gtiff(wdepth_clip_ds, output_raster)

