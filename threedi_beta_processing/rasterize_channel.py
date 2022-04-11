from shapely.geometry import shape, Point, Polygon, LineString
from shapely.wkb import loads
import fiona
from osgeo import ogr, osr, gdal, gdal_array
import sqlite3
import numpy as np
from typing import List
from pathlib import Path
import os
import logging
import datetime
import time

ogr.UseExceptions()
gdal.UseExceptions()

#Tasks with priority:
"""
TODO use classes for cross sections and channels (see rasterize_channel_oo.py for a first sketch).

TODO channel for channel rasterising
    TODO get rid of fiona dependency (fiona vervalt op het moment dat we channel per channel gaan rasterizeren)
TODO merge channels based on minimum (later merge with DEM based on min or max)

TODO get rid of sqlite3 dependency
"""

#Improvements:
"""
TODO replace raster related functions by functions from raster_tools where possible (some functions that are not
 included in .raster_tools may be available in https://github.com/nens/raster-tools )

TODO make the tool compatible with the new geopackage / 3Di model editor data structure
"""

start_script = time.time()
folder = Path(
    r"C:/Users/stijn.overmeen/Documents/Projecten_lokaal/Intern/Rasterize channel/logging"
)
if not os.path.exists(folder):
    os.makedirs(folder)
lines = [
    "|                   1D to 2D: profile and bank level tool                |",
    "|------------------------------------------------------------------------|",
    "|                               Authors:                                 |",
    "|           Stijn Overmeen (stijn.overmeen@nelen-schuurmans.nl)          |",
    "|           Ivar Lokhorst (ivar.lokhorst@nelen-schuurmans.nl)            |",
    "| Leendert van Wolfswinkel (leendert.vanwolfswinkel@nelen-schuurmans.nl) |",
    "|------------------------------------------------------------------------|",
    "|                           Date: "
    f"{datetime.datetime.now().strftime('%d-%m-%Y')}"
    "                             |",
    "",
]
LOG = (
    f"{datetime.datetime.fromtimestamp(start_script).strftime('%Y-%m-%d__%H-%M-%S')}"
    ".log"
)
with open(os.path.join(folder, LOG), "w") as f:
    for line in lines:
        f.write(line)
        f.write("\n")
logging.basicConfig(
    level=logging.INFO,
    handlers=[logging.FileHandler(os.path.join(folder, LOG)), logging.StreamHandler()],
    format="%(message)s",
    force=True,
)

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

    logging.info("Connection created")
    return conn

def features_from_sqlite(proj_target: int, sqlite: str, table: str) -> List:
    """
    Get list of geometries with their FID from a specific table in an sqlite.

    If the feature is a cross section location, the channel_id, definition_id and reference_level are also stored in
    the attributes.
    
    Important note: projection had to happen in same function for it to work with osr

    :param proj_target: target projection
    :param sqlite: filename of the spatialite database
    :param table: name of the table
    :return: List of enriched shapely geometries. The FID is stored in each item's id attribute.
    """
    shapely_objects=[]
    ogrsqlite=ogr.Open(sqlite)
    layer=ogrsqlite.GetLayerByName(table)
    for n in range(0, layer.GetFeatureCount()):
        feat=layer.GetNextFeature()
        geom=feat.GetGeometryRef()
        source=osr.SpatialReference()
        source.ImportFromEPSG(4326)
        target=osr.SpatialReference()
        target.ImportFromEPSG(proj_target)
        transformation=osr.CoordinateTransformation(source,target)
        geom.Transform(transformation)
        wkb_feat=loads(geom.ExportToWkb())
        wkb_feat.id=feat.GetFID()
        if table == "v2_cross_section_location":
            wkb_feat.channel_id = feat.channel_id
            wkb_feat.definition_id = feat.definition_id
            wkb_feat.reference_level = feat.reference_level
            wkb_feat.bank_level = feat.bank_level
        shapely_objects.append(wkb_feat)
    return shapely_objects

def two_sided_parallel_offsets(linestring, offset_dists):
    """
    Generate a set of lines parallel to the input linestring, at both sides of the line

    :param linestring: shapely linestring
    :param offset_dists: list of floats
    :return: list of shapely linestrings
    """
    parallel_offsets = []
    for width in offset_dists:
        parallel_offsets.append(linestring.parallel_offset(width / 2, "left"))
    for width in offset_dists:
        parallel_offsets.append(linestring.parallel_offset(width / 2, "right"))
    logging.info(
        "Generated a set of lines parallel to the input linestring, at both sides of the line"
    )
    return parallel_offsets


def get_channel_widths_and_heigths(
    cur: sqlite3.Cursor,
    add_value,
    profile_or_bank_level: str,
    channel: LineString,
    cross_section_locations: list
):
    """
    Determine the maximum width and width/height relation for each cross section.
    :return: a list of lists of [position, max_width] and a list of widths
    """
    channel_max_widths = []
    channel_all_widths = []
    for xsec in cross_section_locations:
        cur.execute(
            "SELECT width, height FROM v2_cross_section_definition where id={}".format(
                xsec.definition_id
            )
        )
        rows = cur.fetchall()
        for row in rows:
            definition = list(row)
            xsec.widths = list(map(float, definition[0].split()))
            xsec.heights = list(
                map(float, definition[1].split())
            )  # heights relative to reference_level
            if profile_or_bank_level == "bank_level":
                xsec.heights = [xsec.bank_level + add_value]*len(xsec.heights)  # absolute heights

            elif profile_or_bank_level == "profile":
                xsec.heights = [
                    x + xsec.reference_level + add_value for x in xsec.heights
                ]  # absolute heights
            else:
                raise ValueError(
                    f"profile_or_bank_level must be 'profile' or 'bank_level', not {profile_or_bank_level}"
                )
        channel_all_widths += xsec.widths
        channel_max_widths.append(
            [channel.project(xsec, normalized=True), max(xsec.widths)]
        )
        channel_all_widths.sort()
    logging.info(
        "Determined the maximum width and width/height relation for each cross section"
    )
    return channel_max_widths, channel_all_widths


def create_channel_outline(first_boundary_points, last_boundary_points):
    """ Create polygon representing the channel shape 
    based on collected right boundary points and (reversed) left boundary channel points
    
    :param first_boundary_points: 
    :param last_boundary_points: 
    :return: polygon of channel outline
    """
    listarray = []
    for pp in first_boundary_points:
        listarray.append([pp.x, pp.y])
    for pp in last_boundary_points[::-1]:
        listarray.append([pp.x, pp.y])
    nparray = np.array(listarray)
    poly = Polygon(nparray)
    logging.info("Polygon representing the channel shape gained")
    return poly


def write_shapes_to_vsimem(
    all_points,
    channel_outline,
    points_ds=None,
    poly_ds=None,
    point_lyr=None,
    poly_lyr=None,
):
    # write elevation points along channel and outline polygon to in memory shapefile
    shape_drv = ogr.GetDriverByName("ESRI Shapefile")
    if points_ds is None:
        points_ds = shape_drv.CreateDataSource("/vsimem/tmp/points.shp")
        point_lyr = points_ds.CreateLayer("points")
    else:
        pass
    for point in all_points:
        wkt = "POINT(%f %f %s)" % (point.x, point.y, point.height)
        dst_feat = ogr.Feature(feature_def=point_lyr.GetLayerDefn())
        dst_feat.SetGeometry(ogr.CreateGeometryFromWkt(wkt))
        point_lyr.CreateFeature(dst_feat)
    points_ds.ExecuteSQL("CREATE SPATIAL INDEX ON points")
    shape_drv = ogr.GetDriverByName("ESRI Shapefile")
    if poly_ds is None:
        poly_ds = shape_drv.CreateDataSource("/vsimem/tmp/channel_outline.shp")
        poly_lyr = poly_ds.CreateLayer("channel_outline")
    else:
        pass
    dst_feat = ogr.Feature(feature_def=poly_lyr.GetLayerDefn())
    dst_feat.SetGeometry(ogr.CreateGeometryFromWkt(channel_outline.wkt))
    poly_lyr.CreateFeature(dst_feat)
    poly_ds.ExecuteSQL("CREATE SPATIAL INDEX ON channel_outline")
    logging.info(
        "Elevation points along channel and outline polygon saved to in memory shapefile"
    )
    return points_ds, poly_ds, point_lyr, poly_lyr

def createDS(ds_name,ds_format,geom_type,srs,overwrite=False):
    drv=ogr.GetDriverByName(ds_format)
    if os.path.exists(ds_name) and overwrite is True:
        os.remove(ds_name)
    ds=drv.CreateDataSource(ds_name)
    lyr_name=os.path.splitext(os.path.basename(ds_name))[0]
    lyr=ds.CreateLayer(lyr_name,srs,geom_type)
    return ds,lyr

def dissolve(input_file,output_file,multipoly=False,overwrite=False):
    """
    Dissolve polygon layer using UnionCascaded
    UnionCascaded operates on a geometry collection. According to GEOS documentation, 
    this method is more efficient than performing a union piecewise on individual geometries.
    UnionCascaded requires MultiPolygon as a geometry type. 
    That is why a multipolygon is created in this function.
    """
    logging.info('dissolving...')
    ds=ogr.Open(input_file)
    lyr=ds.GetLayer()
    out_ds,out_lyr=createDS(output_file,ds.GetDriver().GetName(),lyr.GetGeomType(),lyr.GetSpatialRef(),overwrite)
    defn=out_lyr.GetLayerDefn()
    multi=ogr.Geometry(ogr.wkbMultiPolygon)
    for feat in lyr:
        if feat.geometry():
            feat.geometry().CloseRings() # this copies the first point to the end
            wkt=feat.geometry().ExportToWkt()
            multi.AddGeometryDirectly(ogr.CreateGeometryFromWkt(wkt))
    union=multi.UnionCascaded()
    if multipoly is False:
        for geom in union:
            poly=ogr.CreateGeometryFromWkb(geom.ExportToWkb())
            feat=ogr.Feature(defn)
            feat.SetGeometry(poly)
            out_lyr.CreateFeature(feat)
    else:
        out_feat=ogr.Feature(defn)
        out_feat.SetGeometry(union)
        out_lyr.CreateFeature(out_feat)
        out_ds.Destroy()
    ds.Destroy()
    return True
    
def buffer(input_file,output_file,buffer_reach,overwrite=False):
    """
    Buffer polygon layer using Buffer
    """
    logging.info('buffering by 'f"{buffer_reach}"' m...')
    ds=ogr.Open(input_file)
    lyr=ds.GetLayer()
    out_ds,out_lyr=createDS(output_file,ds.GetDriver().GetName(),lyr.GetGeomType(),lyr.GetSpatialRef(),overwrite)
    featureDefn=out_lyr.GetLayerDefn()
    for feat in lyr:
        geom=feat.GetGeometryRef()
        buffer=geom.Buffer(buffer_reach)
        out_feat=ogr.Feature(featureDefn)
        out_feat.SetGeometry(buffer)
        out_lyr.CreateFeature(out_feat)
        out_feat=None
    ds.Destroy()

def rasterize_points():

    time1 = time.time()
    ds = gdal.Rasterize(
        "/vsimem/tmp/raster.tif",
        "/vsimem/tmp/points.shp",
        format="MEM",
        outputType=gdal.GDT_Float32,
        xRes=0.5,
        yRes=0.5,
        useZ=True,
        initValues=-9999,
        noData=-9999,
        targetAlignedPixels=True,
    )
    logging.info("\nRasterizing took this much time: " f"{time.time()-time1:.0f}" "s")
    return ds


def fill_no_data(ds):
    # TODO: May be interesting to use https://github.com/nens/raster-tools/blob/master/raster_tools/fill/fill.py
    time2 = time.time()
    gdal.FillNodata(
        targetBand=ds.GetRasterBand(1),
        maskBand=None,
        maxSearchDist=100,
        smoothingIterations=0,
        options=[],
    )
    driver = gdal.GetDriverByName("GTiff")
    dst_datatype = gdal.GDT_Float32
    (y, x) = ds.GetRasterBand(1).ReadAsArray().shape
    dataset = driver.Create(
        "/vsimem/tmp/raster2.tif",
        xsize=x,
        ysize=y,
        bands=1,
        eType=dst_datatype,
        options=["COMPRESS=DEFLATE"],
    )
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(28992)
    dataset.SetGeoTransform(ds.GetGeoTransform())
    dataset.SetProjection(srs.ExportToWkt())
    dataset.GetRasterBand(1).WriteArray(ds.GetRasterBand(1).ReadAsArray()[:, :])
    dataset.GetRasterBand(1).SetNoDataValue(-9999)
    logging.info("Fillnodata took this much time: " f"{time.time()-time2:.0f}" "s")
    return dataset


def crop_to_cutline(dataset):

    time3 = time.time()
    clip_ds = gdal.Warp(
        destNameOrDestDS="/vsimem/tmp/raster3.tif",
        srcDSOrSrcDSTab=dataset,
        cutlineDSName="/vsimem/tmp/channel_outline4.shp",
        cropToCutline=True,
        dstNodata=-9999,
    )
    logging.info(
        "Cropping to cutline took this much time: " f"{time.time()-time3:.0f}" "s"
    )
    return clip_ds


def merge(dem, clip_ds):

    time4 = time.time()
    merged = gdal.Warp(
        destNameOrDestDS="/vsimem/tmp/raster4.tif",
        srcDSOrSrcDSTab=[dem, clip_ds],
        dstNodata=-9999,
    )
    logging.info("Merging took this much time: " f"{time.time()-time4:.0f}" "s")
    return merged


def write_raster(output_raster, geotransform, geoprojection, data):
    """
    write a numpy array to a gdal raster (geotiff, float32, compress=deflate, nodatavalue -9999)

    :param output_raster: filename of the output raster
    :param geotransform: gdal geotransform
    :param geoprojection: proj4 string
    :param data: 2d numpy array
    :return:
    """
    (y, x) = data.shape
    output_format = "GTiff"
    driver = gdal.GetDriverByName(output_format)
    dst_datatype = gdal.GDT_Float32
    dst_ds = driver.Create(
        output_raster,
        xsize=x,
        ysize=y,
        bands=1,
        eType=dst_datatype,
        options=["COMPRESS=DEFLATE"],
    )
    dst_ds.GetRasterBand(1).WriteArray(data)
    dst_ds.SetGeoTransform(geotransform)
    dst_ds.SetProjection(geoprojection)
    dst_ds.GetRasterBand(1).SetNoDataValue(-9999)
    logging.info("Array to raster")
    return


def max_min_raster(dem, merged, profile_or_bank_level, output_raster, proj_target):
    """
    Get both arrays (are same size) and get maximum or minimum values using np.maximum/np.minimum
    In case no-data values are not the same (is not -9999) it should also work
    Find no data values of dem, use a mask and fill with -9999 (this value we will use with array2raster)
    From merged we know nodatavalue is -9999, see function merge
    """

    time5 = time.time()
    dem_raster = gdal.Open(dem)
    no_data_dem = dem_raster.GetRasterBand(1).GetNoDataValue()
    dem_array = np.ma.filled(
        np.ma.masked_equal(dem_raster.ReadAsArray(), no_data_dem), -9999
    )
    merged_array = gdal_array.LoadFile("/vsimem/tmp/raster4.tif")
    if profile_or_bank_level == "bank_level":
        z = np.maximum(dem_array, merged_array)
    else:
        z = np.minimum(dem_array, merged_array)
    geotransform = merged.GetGeoTransform()
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(proj_target)
    write_raster(output_raster, geotransform, srs.ExportToWkt(), z)
    logging.info(
        "Creating max/min raster took this much time: " f"{time.time()-time5:.0f}" "s"
    )


def write_raster_to_gtiff(merged, output_raster, proj_target):
    band = merged.GetRasterBand(1)
    geotransform = merged.GetGeoTransform()
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(proj_target)
    z = band.ReadAsArray()
    write_raster(output_raster, geotransform, srs.ExportToWkt(), z)
    logging.info("Wrote raster to geotiff")


def rasterize_channels(
    sqlite,
    dem,
    output_raster,
    profile_or_bank_level,
    burn_in_dem,
    higher_or_lower_only,
    add_value,
    proj_target,
    ids=None
):
    """
    Main function calling other functions
    
    First channel and cross section data is gathered
    
    Channel in channels loops over all channels:
        Get cross-sectional data
        Create line-strings over length channel
        Get interpolated heigths over these lines
        loop loops over all channel lines in the length of the channel:
            Loop2 loops over points in the length of channel:
                Interpolated height is described to point
                Points that are within a previously defined channel outline are skipped to prevent messy interpolation
                Boundary points are gathered to form the channel outline polygon (which will be used for cropping the
                channel raster)
        
    After the loop over channels:
        Dissolve and buffering (twice) of the channel outline to create a valid cropping layer
        Points are rasterized
        Interpolation between heights of points
        Cropping interpolated raster to channel outline
        Merging with dem
        Write this to raster or write minimum/maximum to raster 
    """
    try:
        if os.path.exists(output_raster):
            os.remove(output_raster)
            logging.info("Found existing raster named " f"{output_raster}")
            logging.info("Removed it to create a new one...")

        channels = features_from_sqlite(proj_target, sqlite, "v2_channel")
        logging.info("List of enriched shapely geometries gained for: channels")
        cross_section_locations = features_from_sqlite(
            proj_target, sqlite, "v2_cross_section_location"
        )
        logging.info(
            "List of enriched shapely geometries gained for: cross_section_locations"
        )

        conn = create_connection(sqlite)
        cur = conn.cursor()

        count = 0
        save_time = time.time()
        for channel in channels:
            if channel.id in ids or ids is None:
                logging.info("")
                logging.info("Channel id = " f"{channel.id}")
                count = count + 1
                if count != 1:  # if count == 1 polygon layer does not exist yet
                    polygons = [
                        pol for pol in fiona.open("/vsimem/tmp/channel_outline.shp")
                    ]
                channel_xsecs = []
                for xsec_loc in cross_section_locations:
                    if xsec_loc.channel_id == channel.id:
                        xsec_loc.position = channel.project(xsec_loc, normalized=True)
                        channel_xsecs.append(xsec_loc)

                (
                    channel_max_widths,
                    channel_all_widths_flat,
                ) = get_channel_widths_and_heigths(
                    cur,
                    add_value,
                    profile_or_bank_level,
                    channel=channel,
                    cross_section_locations=channel_xsecs
                )
                channel_offsets = two_sided_parallel_offsets(
                    channel, channel_all_widths_flat
                )
                all_profiles_interpolated = {}
                for xsec in channel_xsecs:
                    interpolated_height = []
                    for width in channel_all_widths_flat:
                        interpolated_height.append(
                            np.interp(width, xsec.widths, xsec.heights)
                        )
                    all_profiles_interpolated[xsec.position] = interpolated_height
                all_profiles_interpolated[float(0)] = all_profiles_interpolated[
                    min(all_profiles_interpolated.keys())
                ]
                all_profiles_interpolated[float(1)] = all_profiles_interpolated[
                    max(all_profiles_interpolated.keys())
                ]
                x = list(all_profiles_interpolated.keys())
                x.sort()

                all_points = []
                first_boundary_points = []
                last_boundary_points = []
                boundary_points = []
                loop = range(1, len(channel_offsets))
                for chn in loop:
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

                    loop2 = range(1, round(line.length / 2))
                    for i in loop2:
                        if profile_or_bank_level == "bank_level":
                            if (
                                chn == loop[int(len(loop) / 2 - 1.5)] or chn == loop[-1]
                            ):  # lines along banks of channel
                                skip_point = False
                                point = line.interpolate(
                                    2 * i / line.length, normalized=True
                                )
                                point.height = np.interp(
                                    channel.project(point, normalized=True), x, y
                                )
                                if count != 1:
                                    if i <= 10 or i >= (len(loop2) - 10):
                                        for polygon in polygons:
                                            if point.within(shape(polygon["geometry"])):
                                                skip_point = True
                                if skip_point:
                                    logging.info(
                                        "One of the points is within another channel outline, so is skipped"
                                    )
                                else:
                                    all_points.append(point)
                                if chn == loop[int(len(loop) / 2 - 1.5)]:
                                    if i == loop2[0]:
                                        first_boundary_points.append(
                                            Point(line.coords[0][0], line.coords[0][1])
                                        )
                                    first_boundary_points.append(point)
                                    boundary_points.append(point)
                                    if i == loop2[-1]:
                                        first_boundary_points.append(
                                            Point(
                                                line.coords[-1][0], line.coords[-1][1]
                                            )
                                        )
                                elif chn == loop[-1]:
                                    if i == loop2[0]:
                                        last_boundary_points.append(
                                            Point(line.coords[0][0], line.coords[0][1])
                                        )
                                    last_boundary_points.append(point)
                                    boundary_points.append(point)
                                    if i == loop2[-1]:
                                        last_boundary_points.append(
                                            Point(
                                                line.coords[-1][0], line.coords[-1][1]
                                            )
                                        )
                            else:  # we do not need to gather other points than the boundary points for the bank
                                # level tool
                                continue
                        else:
                            skip_point = False
                            point = line.interpolate(
                                2 * i / line.length, normalized=True
                            )
                            point.height = np.interp(
                                channel.project(point, normalized=True), x, y
                            )
                            if count != 1:
                                if i <= 10 or i >= (len(loop2) - 10):
                                    for polygon in polygons:
                                        if point.within(shape(polygon["geometry"])):
                                            skip_point = True
                            if skip_point:
                                logging.info(
                                    "One of the points is within another channel outline, so is skipped"
                                )
                            else:
                                all_points.append(point)
                            if (
                                chn == loop[int(len(loop) / 2 - 1.5)]
                            ):  # line along one of the banks
                                if i == loop2[0]:
                                    first_boundary_points.append(
                                        Point(line.coords[0][0], line.coords[0][1])
                                    )
                                first_boundary_points.append(point)
                                boundary_points.append(point)
                                if i == loop2[-1]:
                                    first_boundary_points.append(
                                        Point(line.coords[-1][0], line.coords[-1][1])
                                    )
                            elif chn == loop[-1]:  # line along other bank
                                if i == loop2[0]:
                                    last_boundary_points.append(
                                        Point(line.coords[0][0], line.coords[0][1])
                                    )
                                last_boundary_points.append(point)
                                boundary_points.append(point)
                                if i == loop2[-1]:
                                    last_boundary_points.append(
                                        Point(line.coords[-1][0], line.coords[-1][1])
                                    )

                channel_outline = create_channel_outline(
                    first_boundary_points, last_boundary_points
                )
                if "points_ds" in locals():
                    points_ds, poly_ds, point_lyr, poly_lyr = write_shapes_to_vsimem(
                        all_points,
                        channel_outline,
                        points_ds,
                        poly_ds,
                        point_lyr,
                        poly_lyr,
                    )
                else:
                    points_ds, poly_ds, point_lyr, poly_lyr = write_shapes_to_vsimem(
                        all_points, channel_outline
                    )

        dissolve("/vsimem/tmp/channel_outline.shp","/vsimem/tmp/channel_outline2.shp")
        buffer("/vsimem/tmp/channel_outline2.shp","/vsimem/tmp/channel_outline3.shp",1)
        buffer("/vsimem/tmp/channel_outline3.shp","/vsimem/tmp/channel_outline4.shp",-1)
        logging.info(
            "Getting channel points and outline took this much time: "
            f"{(time.time()-save_time):.0f}"
            " s."
        )
        ds = rasterize_points()
        dataset = fill_no_data(ds)
        clip_ds = crop_to_cutline(dataset)
        if burn_in_dem:
            merged = merge(dem, clip_ds)
            if higher_or_lower_only:
                max_min_raster(dem, merged, profile_or_bank_level, output_raster, proj_target)
            else:
                write_raster_to_gtiff(merged, output_raster, proj_target)
        else:
            write_raster_to_gtiff(clip_ds, output_raster, proj_target)

        logging.info(
            "Total time elapsed: " f"{(time.time()-start_script)/60:.0f}" " min."
        )
    except Exception as e:
        logging.exception(e)
        raise