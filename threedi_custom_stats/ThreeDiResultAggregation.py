#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Calculate the resultant of the total outflow per node, resampled to grid_space """

import argparse
import warnings

from threedigrid.admin.gridresultadmin import GridH5ResultAdmin
from threedigrid.admin.nodes.models import Nodes, Cells
from threedigrid.admin.lines.models import Lines
from threedigrid.admin.utils import KCUDescriptor

import gdal
import numpy as np
import ogr
import osr

try:
    from constants import *
except:
    from .constants import *

KCU_DICT = KCUDescriptor()
NODE_TYPE_DICT = {
    1: '2D surface water',
    2: '2D groundwater',
    3: '1D without storage',
    4: '1D with storage',
    5: '2D surface water boundary',
    6: '2D groundwater boundary',
    7: '1D boundary'
}


warnings.filterwarnings('ignore')
ogr.UseExceptions()


def get_extension_mapping(vector, raster, create_capability):
    ext_mapping = {}
    for i in range(ogr.GetDriverCount()):
        drv = ogr.GetDriver(i)
        if ((vector and drv.GetMetadataItem('DCAP_VECTOR') == 'YES') or (
                raster and drv.GetMetadataItem('DCAP_RASTER') == 'YES')) and \
                ((create_capability and drv.GetMetadataItem('DCAP_CREATE') == 'YES') or (not create_capability)) and \
                drv.GetMetadataItem('DMD_EXTENSION') is not None:
            ext_mapping[drv.GetMetadataItem('DMD_EXTENSION')] = drv.GetName()
    return ext_mapping


def time_intervals(nodes_or_lines, start_time, end_time):
    """Get a 1D numpy array of time intervals between timestamps, inclusing 'broken' first and last time intervals
    It also returns the last timestamp before start_time (ts_start_time)
    and the first timestamp after end_time (ts_end_time)
    The length of the time_intervals arrays is guaranteed to be the same as the number of timestamps between
    the returned ts_start_time and ts_end_time"""
    if end_time is None:
        end_time = nodes_or_lines.timestamps[-1]  # last timestamp
    if start_time is None:
        start_time = 0
    # Check validity of temporal filtering, part 1 of 2
    assert start_time < end_time

    all_timestamps = np.array(nodes_or_lines.timestamps)
    filtered_timestamps = all_timestamps[np.where(all_timestamps >= start_time)]  # filters timestamps for start_time
    filtered_timestamps = filtered_timestamps[
        np.where(filtered_timestamps <= end_time)]  # filters timestamps for end_time

    ts_start_time_idx = int(np.where(all_timestamps == filtered_timestamps[0])[0])
    ts_end_time_idx = int(np.where(all_timestamps == filtered_timestamps[-1])[0])

    # Prepend start_time as timestamp if the start_time falls between two timestamps
    if start_time not in filtered_timestamps:
        filtered_timestamps = np.append(start_time, filtered_timestamps)
        ts_start_time_idx -= 1

    # Append end_time as timestamp if the start_time falls between two timestamps
    if end_time not in filtered_timestamps:
        filtered_timestamps = np.append(filtered_timestamps, end_time)
        ts_end_time_idx += 1

    # Check validity of temporal filtering, part 2 of 2
    if all_timestamps[ts_start_time_idx:ts_end_time_idx].size == 0:
        raise Exception('No values found within temporal filter')

    # raw_values must be of same length as time_intervals,
    # because we multiply the flow variable by the time interval to obtain the aggregate.
    # therefore, ts_end_time is set to the timestamp at [ts_end_time_index - 1]
    ts_start_time = all_timestamps[ts_start_time_idx]
    ts_end_time = all_timestamps[ts_end_time_idx - 1]

    time_intervals_result = filtered_timestamps[1:] - filtered_timestamps[0:-1]
    return ts_start_time, ts_end_time, time_intervals_result


def line_geometry_length(line_geometry: np.ndarray):
    a = line_geometry.reshape(2, int(len(line_geometry) / 2.0))
    return np.sum(np.sqrt((a[0, 1:] - a[0, :-1]) ** 2 + (a[1, 1:] - a[1, :-1]) ** 2))


line_geometries_to_lengths = np.vectorize(line_geometry_length)


def time_aggregate(nodes_or_lines, start_time, end_time, variable, method, sign='net', threshold=None, multiplier=1,
                   cfl_strictness=1):
    """
    Aggregate the variable with method using threshold within time frame

        :param sign: on of ['pos', 'neg', 'abs', 'net']
        :param start_time:
        :param end_time:
        :param method:
        :param threshold:
        :param cfl_strictness:
        :return:
        :param nodes_or_lines: threedigrid.admin.gridresultadmin.GridH5ResultAdmin.lines
        :param variable: one of AGGREGATION_VARIABLES.short_names(var_type=VT_FLOW) from constants.py
        :rtype: np.ndarray

    This method implicitly assumes that the discharge at a specific timestamp remains the same until the next
    timestamp, i.e. if there are timestamps at every 300 s, and the user inputs '450' as end_time, the discharge at
    300 s is multiplied by 150 s for the last 'broken' time interval. In this case, the first timestamp after
    end_time is also required. For that reason, temporal filtering is done within this function, while other types
    of filtering (spatial, typological, id-based) are not.
    """

    ts_start_time, ts_end_time, tintervals = time_intervals(nodes_or_lines=nodes_or_lines,
                                                            start_time=start_time,
                                                            end_time=end_time)
    ts = nodes_or_lines.timeseries(ts_start_time, ts_end_time)

    raw_values = np.ndarray((0, 0))

    # Line variables
    if variable == 'q':
        raw_values = ts.q
    elif variable == 'u':
        raw_values = ts.u1
    elif variable == 'au':
        raw_values = ts.au
    elif variable == 'ts_max':
        if hasattr(nodes_or_lines, 'line_geometries'):
            if nodes_or_lines.line_geometries.ndim == 0:
                a = nodes_or_lines.line_coords[[0, 2, 1, 3], :]
                b = np.split(a, np.shape(a)[1], 1)
                lengths = np.array(list(map(line_geometry_length, b)))
            else:
                lengths = line_geometries_to_lengths(nodes_or_lines.line_geometries)
        else:
            a = nodes_or_lines.line_coords[[0, 2, 1, 3], :]
            b = np.split(a, np.shape(a)[1], 1)
            lengths = np.array(list(map(line_geometry_length, b)))

        ts_u1 = ts.u1
        ts_u1[ts_u1 == -9999] = np.nan
        velocities = np.absolute(ts_u1)
        max_possible_ts = np.divide((lengths * cfl_strictness), velocities)
        raw_values = max_possible_ts
        kcu_types = nodes_or_lines.kcu
        raw_values[:, np.in1d(kcu_types, np.array(NON_TS_REDUCING_KCU))] = 9999

    # Node variables
    elif variable == 's1':
        raw_values = ts.s1
    elif variable == 'vol':
        raw_values = ts.vol
    elif variable == 'rain':
        raw_values = ts.rain
    elif variable == 'rain_depth':
        ts_rain = ts.rain
        ts_rain[ts_rain == -9999] = np.nan
        raw_values = np.divide(ts_rain, nodes_or_lines.sumax)
    elif variable == 'su':
        raw_values = ts.su
    elif variable == 'ucx':
        raw_values = ts.ucx
    elif variable == 'ucy':
        raw_values = ts.ucy
    elif variable == 'uc':
        ucx = ts.ucx
        ucx[ucx == -9999] = np.nan
        ucy = ts.ucy
        ucy[ucy == -9999] = np.nan
        raw_values = np.sqrt(np.square(ucx), np.square(ucy))
    elif variable == 'infiltration_rate':
        raw_values = ts.infiltration_rate_simple
    elif variable == 'infiltration_rate_mm':
        ts_infiltration_rate_simple = ts.infiltration_rate_simple
        ts_infiltration_rate_simple[ts_infiltration_rate_simple == -9999] = np.nan
        raw_values = np.divide(np.multiply(ts_infiltration_rate_simple, 1000), ts.sumax)
    elif variable == 'q_lat':
        raw_values = ts.q_lat
    elif variable == 'q_lat_m':
        ts_q_lat = ts.q_lat
        ts_q_lat[ts_q_lat == -9999] = np.nan
        raw_values = np.divide(np.multiply(ts_q_lat, 1000), nodes_or_lines.sumax)
    elif variable == 'intercepted_volume':
        raw_values = ts.intercepted_volume
    elif variable == 'intercepted_volume_mm':
        ts_intercepted_volume = ts.intercepted_volume
        ts_intercepted_volume[ts_intercepted_volume == -9999] = np.nan
        raw_values = np.divide(np.multiply(ts_intercepted_volume, 1000), nodes_or_lines.sumax)
    elif variable == 'q_sss':
        raw_values = ts.q_sss
    elif variable == 'q_sss_mm':
        ts_q_sss = ts.q_sss
        ts_q_sss[ts_q_sss == -9999] = np.nan
        raw_values = np.divide(np.multiply(ts_q_sss, 1000), nodes_or_lines.sumax)

    else:
        raise Exception('Unknown aggregation variable "{}".'.format(variable))

    # replace -9999 in raw values by NaN
    raw_values[raw_values == -9999] = np.nan

    if sign == 'pos':
        raw_values_signed = raw_values * (raw_values >= 0).astype(int)
    elif sign == 'neg':
        raw_values_signed = raw_values * (raw_values < 0).astype(int)
    elif sign == 'abs':
        raw_values_signed = np.absolute(raw_values)
    elif sign == 'net':
        raw_values_signed = raw_values
    else:
        raw_values_signed = raw_values

    # Apply method
    if method == 'sum':
        raw_values_per_time_interval = np.multiply(raw_values_signed.T, tintervals).T
        result = np.sum(raw_values_per_time_interval, axis=0)
    elif method == 'min':
        result = np.nanmin(raw_values_signed, axis=0)
    elif method == 'max':
        result = np.nanmax(raw_values_signed, axis=0)
    elif method == 'mean':
        result = np.nanmean(raw_values_signed, axis=0)
    elif method == 'median':
        result = np.nanmedian(raw_values_signed, axis=0)
    elif method == 'first':
        result = raw_values_signed[0, :]
    elif method == 'last':
        result = raw_values_signed[-1, :]
    elif method == 'above_thres':
        raw_values_above_threshold = np.greater(raw_values_signed, threshold)
        time_above_treshold = np.sum(np.multiply(raw_values_above_threshold.T, tintervals).T, axis=0)
        total_time = np.sum(tintervals)
        result = np.multiply(np.divide(time_above_treshold, total_time), 100.0)
    elif method == 'below_thres':
        raw_values_below_threshold = np.less(raw_values_signed, threshold)
        time_below_treshold = np.sum(np.multiply(raw_values_below_threshold.T, tintervals).T, axis=0)
        total_time = np.sum(tintervals)
        result = np.multiply(np.divide(time_below_treshold, total_time), 100.0)
    else:
        raise Exception('Unknown aggregation method "{}".'.format(method))

    # multiplier (unit conversion)
    result *= multiplier

    return result


def hybrid_time_aggregate(gr,
                          ids,
                          start_time,
                          end_time,
                          variable,
                          sign,
                          method,
                          threshold,
                          multiplier
                          ):
    if 'q_' in variable:
        flows = flow_per_node(gr=gr, node_ids=ids,
                              start_time=start_time,
                              end_time=end_time,
                              out='_out' in variable,
                              aggregation_method=method)
        if '_x' in variable:
            result = flows[:, 1]
        elif '_y' in variable:
            result = flows[:, 2]
        else:
            raise Exception('Unknown aggregation variable "{}".'.format(variable))
    else:
        raise Exception('Unknown aggregation variable "{}".'.format(variable))

    result *= multiplier

    return result


def empty_raster_from_vector_layer(layer, pixel_size_x, pixel_size_y, bands=1, nodatavalue=-9999):
    """ Create in-memory gdal dataset of the same size as the input layer, filled with nodatavalue. """
    xmin, xmax, ymin, ymax = layer.GetExtent()
    width = int((xmax - xmin) / pixel_size_x)
    height = int((ymax - ymin) / pixel_size_y)
    drv = gdal.GetDriverByName('mem')

    dataset = drv.Create('', xsize=width, ysize=height, bands=bands, eType=gdal.GDT_Float32)

    shift = 0.0  # set to -0.5 if applied to point data that represent pixel centers
    dataset.SetGeoTransform((xmin + shift * pixel_size_x,
                             pixel_size_x,
                             0,
                             ymax - shift * pixel_size_x,
                             0,
                             -1 * abs(pixel_size_y))
                            )
    dataset.SetProjection(layer.GetSpatialRef().ExportToWkt())

    for i in range(bands):
        band = dataset.GetRasterBand(i + 1)
        band.SetNoDataValue(nodatavalue)
        band.Fill(nodatavalue)

    return dataset


def flowline_angle_x(lines):
    """ Calculate the angle between each flowline and the x-axis 
    Angles in counter-clockwise values from -pi to pi
    """
    coords = lines.line_coords
    line_start = coords.T[:, 0:2]
    line_end = coords.T[:, 2:4]
    delta = line_end - line_start
    return np.arctan2(delta[:, 1], delta[:, 0])  # results in counter-clockwise values from -pi to pi


def rasterize_cell_layer(cell_layer, column_name, pixel_size, interpolation_method=None, pre_resample_method=PRM_NONE):
    non_interpolated_ds = empty_raster_from_vector_layer(layer=cell_layer,
                                               pixel_size_x=pixel_size,
                                               pixel_size_y=pixel_size
                                               )
    gdal.RasterizeLayer(dataset=non_interpolated_ds,
                        bands=[1],
                        layer=cell_layer,
                        options=['ATTRIBUTE=' + column_name])
    if interpolation_method is None:
        return non_interpolated_ds
    else:
        mask_band = non_interpolated_ds.GetRasterBand(1)
        mask_array = mask_band.ReadAsArray()

        tmp_drv = ogr.GetDriverByName('ESRI Shapefile')
        tmp_fn = '/vsimem/point.shp'
        tmp_ds = tmp_drv.CreateDataSource(tmp_fn)
        srs = cell_layer.GetSpatialRef()
        tmp_lyr = tmp_ds.CreateLayer('point', srs, ogr.wkbPoint)

        # Add input Layer Fields to the output Layer
        field_defn = ogr.FieldDefn('val', ogr.OFTReal)
        tmp_lyr.CreateField(field_defn)

        # Get the output Layer's Feature Definition
        out_layer_defn = tmp_lyr.GetLayerDefn()

        # Add features to the output Layer
        for i in range(0, cell_layer.GetFeatureCount()):
            # Get the input Feature
            in_feature = cell_layer.GetFeature(i)

            # Create output Feature
            out_feature = ogr.Feature(out_layer_defn)

            # Set geometry as centroid
            geom = in_feature.GetGeometryRef()
            centroid = geom.Centroid()
            out_feature.SetGeometry(centroid)

            # Apply Pre-Resample Method
            in_value = in_feature.GetField(column_name)
            in_cell_size = np.sqrt(in_feature.GetGeometryRef().Area())
            if pre_resample_method == PRM_NONE:  # no processing before resampling (e.g. for water levels,
                                                 # velocities); divide by 1
                out_value = in_value
            elif pre_resample_method == PRM_SPLIT:  # split the original value over the new pixels
                out_value = in_value / (in_cell_size / pixel_size)**2
            elif pre_resample_method == PRM_1D:  # for flows (q) in x or y direction: scale with pixel resolution;
                                                 # divide by (res_old/res_new)
                out_value = in_value / (in_cell_size / pixel_size)
            else:
                raise Exception('Unknown pre-resample method')

            # Add field values from input Layer
            out_feature.SetField('val', out_value)

            # Add new feature to output Layer
            tmp_lyr.CreateFeature(out_feature)

        tmp_lyr.SyncToDisk()

        xmin, xmax, ymin, ymax = cell_layer.GetExtent()
        raster_x_size = (xmax - xmin) / pixel_size
        raster_y_size = (ymax - ymin) / pixel_size
        output_bounds = [xmin, ymax, xmax, ymin]
        interpolated_ds = gdal.Grid('tmp_rast',
                              tmp_fn,
                              format='MEM',
                              outputType=gdal.GDT_Float32,
                              # layers=['point'],
                              algorithm=interpolation_method,
                              zfield='val',
                              width=raster_x_size,
                              height=raster_y_size,
                              outputBounds=output_bounds,
                              noData=-9999)
        interpolated_band = interpolated_ds.GetRasterBand(1)
        interpolated_array = interpolated_band.ReadAsArray()
        interpolated_array[mask_array == -9999] = -9999
        interpolated_ds.GetRasterBand(1).WriteArray(interpolated_array)
        interpolated_ds.GetRasterBand(1).SetNoDataValue(-9999)
        gdal.Unlink(tmp_fn)
    return interpolated_ds


def pixels_to_geoms(raster: gdal.Dataset, column_names, output_geom_type, output_layer_name: str):
    """
    Convert a single or multiband raster to a point or polygon layer.

    Each feature represents one pixel. The raster values are stored in the output layer attributes.
    Raster bands are mapped to column names by mapping column_names list order to the raster bands order.

    :param raster: gdal Dataset
    :param column_names: list of column names for the output layers, or str for singleband raster
    :param output_geom_type: ogr wkpPoint or wkbPolygon
    :param output_layer_name: name of the output layer
    :return: ogr.Layer
    """

    if isinstance(column_names, str):
        column_names = [column_names]

    # collect fishnet dimensions
    gt = raster.GetGeoTransform()
    xmin = gt[0]
    ymax = gt[3]

    pixel_size_x = gt[1]
    pixel_size_y = gt[5]

    nr_cols = raster.RasterXSize
    nr_rows = raster.RasterYSize

    # start grid cell envelope
    if output_geom_type == ogr.wkbPolygon:
        ring_xleft_origin = xmin
        ring_xright_origin = xmin + pixel_size_x
        ring_ytop_origin = ymax
        ring_ybottom_origin = ymax + pixel_size_y
    elif output_geom_type == ogr.wkbPoint:
        first_col_x = xmin + pixel_size_x / 2.0
        first_row_y = ymax + pixel_size_y / 2.0
    else:
        raise Exception('Invalid output geometry type. Choose one of [ogr.wkbPoint, ogr.wkbPolygon].')

    # create output datasource
    out_driver = ogr.GetDriverByName('MEMORY')
    out_data_source = out_driver.CreateDataSource('')
    srs = osr.SpatialReference()
    srs.ImportFromWkt(raster.GetProjection())
    out_layer = out_data_source.CreateLayer(output_layer_name, srs, geom_type=output_geom_type)

    band_arrays = []
    ndv = []

    for i, attr_name in enumerate(column_names, start=1):
        band = raster.GetRasterBand(i)
        if band is None:
            continue
        if band.DataType in (gdal.GDT_Byte,
                             gdal.GDT_CInt16,
                             gdal.GDT_CInt32,
                             gdal.GDT_Int16,
                             gdal.GDT_Int32,
                             gdal.GDT_UInt16,
                             gdal.GDT_UInt32):
            field_data_type = ogr.OFTInteger
        if band.DataType in (gdal.GDT_CFloat32,
                             gdal.GDT_CFloat64,
                             gdal.GDT_Float32,
                             gdal.GDT_Float64
                             ):
            field_data_type = ogr.OFTReal
        field = ogr.FieldDefn(attr_name, field_data_type)
        out_layer.CreateField(field)

        band_array_i = band.ReadAsArray()
        band_arrays.append(band_array_i)
        ndv.append(band.GetNoDataValue())

    feature_defn = out_layer.GetLayerDefn()

    # create grid cells
    countcols = 0
    x = first_col_x
    while countcols < nr_cols:
        countcols += 1

        # reset envelope for rows
        if output_geom_type == ogr.wkbPolygon:
            ring_ytop = ring_ytop_origin
            ring_ybottom = ring_ybottom_origin
        elif output_geom_type == ogr.wkbPoint:
            y = first_row_y

        countrows = 0
        while countrows < nr_rows:
            countrows += 1
            out_feature = ogr.Feature(feature_defn)

            # fill field values, checking if at least one isn't nodata
            any_valid_val = False
            for i, field in enumerate(column_names):
                val = band_arrays[i][countrows - 1, countcols - 1]
                if val is None:
                    val = ndv[i]
                else:
                    val = val.item()
                    if val != ndv[i]:
                        any_valid_val = True
                out_feature.SetField(field, val)

            if any_valid_val:

                # create geometry
                geom = ogr.Geometry(output_geom_type)
                if output_geom_type == ogr.wkbPolygon:
                    ring = ogr.Geometry(ogr.wkbLinearRing)
                    ring.AddPoint(ring_xleft_origin, ring_ytop)
                    ring.AddPoint(ring_xright_origin, ring_ytop)
                    ring.AddPoint(ring_xright_origin, ring_ybottom)
                    ring.AddPoint(ring_xleft_origin, ring_ybottom)
                    ring.AddPoint(ring_xleft_origin, ring_ytop)
                    geom.AddGeometry(ring)
                elif output_geom_type == ogr.wkbPoint:
                    geom.AddPoint(x, y)
                out_feature.SetGeometry(geom)

                # create feature
                out_layer.CreateFeature(out_feature)

            # new envelope for next poly
            if output_geom_type == ogr.wkbPolygon:
                ring_ytop += pixel_size_y
                ring_ybottom += pixel_size_y
            elif output_geom_type == ogr.wkbPoint:
                y += pixel_size_y

        # new envelope for next poly
        if output_geom_type == ogr.wkbPolygon:
            ring_xleft_origin += pixel_size_x
            ring_xright_origin += pixel_size_x
        elif output_geom_type == ogr.wkbPoint:
            x += pixel_size_x

    return out_data_source


def filter_lines_by_node_ids(lines, node_ids):
    boolean_mask = np.sum(np.isin(lines.line_nodes, node_ids), axis=1) > 0
    line_ids = lines.id[boolean_mask]
    result = lines.filter(id__in=line_ids)
    return result


def select_from_2d_array_where_col_x_in(array_2d, col_nr, values):
    return array_2d[np.in1d(array_2d[:, col_nr], values), :]


def flow_per_node(gr: GridH5ResultAdmin, node_ids: list, start_time: int, end_time: int, out: bool, aggregation_method):
    """
    Calculate the sum of all flows per node, split in x and y directions

    :param out: if True, outgoing flows are calculated. If false, incoming flows
    :returns: numpy 2d array; columns: node ids, x direction flow, y direction flow
    """
    lines = filter_lines_by_node_ids(gr.lines, node_ids)

    start_end_node_ids = lines.line_nodes.T.reshape(
        lines.line_nodes.size)  # 1d array with first all start nodes, than all end nodes
    # if there are any nodes without flowlinks, they will not be included in start_end_node_ids
    # this is dealt with just before the end of this function

    q_agg = time_aggregate(nodes_or_lines=lines,
                           start_time=start_time,
                           end_time=end_time,
                           variable='q',
                           sign='net',
                           method=aggregation_method)
    if out:
        q_agg_start_nodes = q_agg * (q_agg > 0).astype(int)  # positive flows, to be grouped by start node
        q_agg_end_nodes = q_agg * (q_agg < 0).astype(int)  # negative flows, to be grouped by end node
    else:
        q_agg_start_nodes = q_agg * (q_agg < 0).astype(int)  # positive flows, to be grouped by start node
        q_agg_end_nodes = q_agg * (q_agg > 0).astype(int)  # negative flows, to be grouped by end node

    q_agg_in_or_out = np.hstack(
        [q_agg_start_nodes, q_agg_end_nodes])  # 1d array with first all positive flows, than all negative flows

    # for both pos and neg flows, use the flowline in pos direction to calc the angle
    angle_x = flowline_angle_x(lines)
    angle_x_twice = np.hstack([angle_x, angle_x])
    q_agg_in_or_out_x = np.cos(angle_x_twice) * q_agg_in_or_out  # x component of that flow
    q_agg_in_or_out_y = np.sin(angle_x_twice) * q_agg_in_or_out  # y component of that flow

    # group by met numpy: zie stack overflow "numpy array group by one column sum another"

    # bind start_end_node_ids, q_x, and q_y into one 2d array / table
    qtable = np.array([start_end_node_ids, q_agg_in_or_out_x, q_agg_in_or_out_y, q_agg_in_or_out]).T
    # sort by node id
    qtable = qtable[qtable[:, 0].argsort()]
    # find the split indices
    i = np.nonzero(np.diff(qtable[:, 0]))[0] + 1
    i = np.insert(i, 0, 0)

    # sum qx and qy, group by start node
    start_node_ids_unique = qtable[i, 0]  # array of unique start nodes
    sums = np.add.reduceat(qtable[:, [1, 2]], i)  # sum qx and qy, group by start node
    q_agg_in_or_out_x_sum = sums[:, 0]
    q_agg_in_or_out_y_sum = sums[:, 1]

    in_or_out_flow = np.array([start_node_ids_unique,
                               q_agg_in_or_out_x_sum,
                               q_agg_in_or_out_y_sum]).T

    # if there are any nodes without flowlinks, they will have been missed so far
    linkless_node_ids = node_ids[np.logical_not(np.in1d(node_ids, start_node_ids_unique))]
    if linkless_node_ids.ndim > 0 and linkless_node_ids.size > 0:
        linkless_node_zeroflow = np.c_[linkless_node_ids, np.zeros(
            [linkless_node_ids.size, 2])]  # can't use hstack here to add a (x,2)-shaped array to a (x)-shaped array
        in_or_out_flow = np.vstack([in_or_out_flow, linkless_node_zeroflow])

    in_or_out_flow = in_or_out_flow[in_or_out_flow[:, 0].argsort()]  # sort by first column, i.e., node id
    # select only the requested nodes
    result = select_from_2d_array_where_col_x_in(array_2d=in_or_out_flow, col_nr=0, values=node_ids)
    return result


def enrich_mini_arrows(mini_arrows, cell_size):
    # calculate resultant of q
    resultant = np.sqrt(np.square(mini_arrows[:, 1]) + np.square(mini_arrows[:, 2]))

    # calculate the azimuth of the resultant (radians)
    azimuth = np.arctan2(mini_arrows[:, 1], mini_arrows[:, 2])  # results in clockwise values from -pi to pi
    azimuth[azimuth < 0] += 2 * np.pi  # clockwise values from 0 to 2pi

    # calculate the outflow in mm
    outflow_mm = ((resultant * 1000) / (cell_size ** 2)).astype('float32')
    outflow_x_mm = (mini_arrows[:, 1] * 1000) / (cell_size ** 2)
    outflow_y_mm = (mini_arrows[:, 2] * 1000) / (cell_size ** 2)

    # calculate the percentile of the flow
    # print(outflow_mm.shape[0])
    # print(outflow_mm)
    # print(outflow_mm.argsort())
    ranks = np.argsort(np.argsort(outflow_mm))
    percentile = ranks / float((outflow_mm.shape[0]) - 1)

    # concatenate the columns
    result = np.c_[mini_arrows,
                   resultant,
                   azimuth,
                   outflow_mm,
                   outflow_x_mm,
                   outflow_y_mm,
                   percentile]

    return result


def xy_abc2rast(xy_abc, pixel_size_x, pixel_size_y, nodatavalue, epsg=28992, where='center'):
    """ Convert nd array to a gdal raster Dataset, where columns a,b,c..n will be placed in separate bands
        :param epsg: epsg code
        :param xy_abc: numpy ndarray (dtype float32) of shape nrow = n, ncol >= 3. \
                    col #0 = x ordinate, \
                    col #1 = y ordinate, \
                    col #2..n = value (a,b,c)
        :param pixel_size_x: x resolution of the output raster
        :param pixel_size_y: y resolution of the output raster
        :param nodatavalue: nodata-value of the output raster
        :param where: 'center' or 'upperLeft' to indicate what point in the pixel the xy coordinates represent
        :return osgeo.gdal.Dataset
    """
    xmin = np.min(xy_abc[:, 0])
    xmax = np.max(xy_abc[:, 0])
    ymin = np.min(xy_abc[:, 1])
    ymax = np.max(xy_abc[:, 1])
    width = int((xmax - xmin) / pixel_size_x + 1)
    height = int((ymax - ymin) / pixel_size_y + 1)

    # create output 2d array of required size, fill with nodata value
    bandcount = xy_abc.shape[1] - 2

    outarr = np.full([height, width, bandcount], nodatavalue, dtype='float32')

    # write values from xyz to their location in the out array

    for i in xy_abc:
        x_idx = int((i[0] - xmin) / pixel_size_x)
        y_idx = int((i[1] - ymin) / pixel_size_y)
        for j in range(bandcount):
            outarr[y_idx, x_idx, j] = i[j + 2]

    # write out array to in-memory gdal raster
    drv = gdal.GetDriverByName('MEM')
    ds = drv.Create('', xsize=width, ysize=height, bands=1, eType=gdal.GDT_Float32)
    # Set the geotransform using ds.SetGeoTransform where the argument is a six element tuple:
    #    (upper_left_x, x_resolution, x_skew, upper_left_y, y_skew, y_resolution)
    shift = -0.5
    if where == 'upperLeft':
        shift = 0.0
    ds.SetGeoTransform((xmin + shift * pixel_size_x,
                        pixel_size_x,
                        0,
                        ymax - shift * pixel_size_x,
                        0,
                        -1 * abs(pixel_size_y))
                       )
    raster_srs = osr.SpatialReference()
    raster_srs.ImportFromEPSG(epsg)
    ds.SetProjection(raster_srs.ExportToWkt())

    for i in range(bandcount):
        bandnr = i + 1
        if bandnr > 1:
            ds.AddBand(datatype=gdal.GDT_Float32)
        ds.GetRasterBand(bandnr).WriteArray(np.flipud(outarr[:, :, i]))
        ds.GetRasterBand(bandnr).SetNoDataValue(nodatavalue)

    return ds


def add_coordinates_as_bands(rast, where='center'):
    geotransform = rast.GetGeoTransform()
    indexgrid = np.mgrid[0:rast.RasterYSize, 0:rast.RasterXSize]  # [0,:,:] = y index, [1,:,:] = x index
    shift = 0.5
    if where == 'upperLeft':
        shift = 0
    x_ordinate = geotransform[0] + (indexgrid[1, :, :] + shift) * geotransform[1]
    y_ordinate = geotransform[3] + (indexgrid[0, :, :] + shift) * geotransform[5]
    nbands = rast.RasterCount

    drv = gdal.GetDriverByName('MEM')
    outrast = drv.CreateCopy('', rast)
    outrast.AddBand(datatype=gdal.GDT_Float32)
    outrast.GetRasterBand(nbands + 1).WriteArray(x_ordinate)
    outrast.AddBand(datatype=gdal.GDT_Float32)
    outrast.GetRasterBand(nbands + 2).WriteArray(y_ordinate)
    return outrast


def mini_arrows_to_ogr(src, tgt_layer, epsg=28992):
    """ Write mini arrows numpy array (src) to ogr in-memory vector layer as point features with attributes
    """

    # create an output datasource in memory
    tgt_drv = ogr.GetDriverByName('MEMORY')
    tgt_ds = tgt_drv.CreateDataSource('')

    srs = osr.SpatialReference()
    srs.ImportFromEPSG(epsg)

    outLayer = tgt_ds.CreateLayer(tgt_layer,
                                  srs,
                                  geom_type=ogr.wkbPoint
                                  )

    # define fields
    uIdField = ogr.FieldDefn("uid", ogr.OFTInteger)
    outLayer.CreateField(uIdField)

    nodeIdField = ogr.FieldDefn("node_id", ogr.OFTInteger)
    outLayer.CreateField(nodeIdField)

    q_m3Field = ogr.FieldDefn("outflow_m3", ogr.OFTReal)
    outLayer.CreateField(q_m3Field)

    q_mmField = ogr.FieldDefn("outflow_mm", ogr.OFTReal)
    outLayer.CreateField(q_mmField)

    q_x_mmField = ogr.FieldDefn("outflow_x_mm", ogr.OFTReal)
    outLayer.CreateField(q_x_mmField)

    q_y_mmField = ogr.FieldDefn("outflow_y_mm", ogr.OFTReal)
    outLayer.CreateField(q_y_mmField)

    azimuthField = ogr.FieldDefn("azimuth", ogr.OFTReal)
    outLayer.CreateField(azimuthField)

    percentileField = ogr.FieldDefn("percentile", ogr.OFTReal)
    outLayer.CreateField(percentileField)

    # Create the feature and set values
    featureDefn = outLayer.GetLayerDefn()

    for i in range(src.shape[0]):
        uid = i + 1
        node_id = src[i, 0]
        outflow_m3_i = src[i, 5]
        azimuth_i = src[i, 6]
        outflow_mm_i = src[i, 7]
        outflow_x_mm_i = src[i, 8]
        outflow_y_mm_i = src[i, 9]
        percentile_i = src[i, 10]

        shape = ogr.Geometry(ogr.wkbPoint)
        shape.SetPoint(0, src[i, 3], src[i, 4])

        feature = ogr.Feature(featureDefn)
        feature.SetGeometry(shape)
        feature.SetField("uid", uid)
        feature.SetField("node_id", node_id)
        feature.SetField("outflow_m3", outflow_m3_i)
        feature.SetField("outflow_mm", outflow_mm_i)
        feature.SetField("outflow_x_mm", outflow_x_mm_i)
        feature.SetField("outflow_y_mm", outflow_y_mm_i)
        feature.SetField("azimuth", azimuth_i)
        feature.SetField("percentile", percentile_i)

        outLayer.CreateFeature(feature)
        feature = None

    return tgt_ds


def ogr_connection(host, port, user, password, database, **kwargs):
    ogr_conn = ("PG:host={} port={} user='{}'"
                "password='{}' dbname='{}'").format(host,
                                                    port,
                                                    user,
                                                    password,
                                                    database)
    return ogr.Open(ogr_conn)


# def make_mini_arrows(gr, tgt_layer, bbox=None, start_time=0, end_time=None):
#     """ Calculate the resultant of the total outflow per node, resampled to grid_space
#         :param tgt_layer: name of the resulting layer
#         :param gr: threedigrid GridH5ResultAdmin object
#         :param bbox: bounding box: list of [LowerLeftX, LowerLeftY, UpperRightX, UpperRightY] for filtering or None for
#         no filtering
#         :param start_time: start time (seconds after start of simulation).
#         :param end_time: end time (seconds after start of simulation). None for 'end of simulation'
#     """
#
#     lines_2d = gr.lines.subset('2D_OPEN_WATER')
#     nodes_2d = gr.nodes.subset('2D_OPEN_WATER')
#
#     # Select 2D nodes and flowlinks in bbox
#     if bbox is not None:
#         if not (bbox[0] < bbox[2]) and (bbox[1] < bbox[3]):
#             raise Exception('Invalid bounding box.')
#         lines_2d = lines_2d.filter(line_coords__in_bbox=bbox)
#         if lines_2d.count == 0:
#             raise Exception('No 2d flowlines found within bounding box.')
#         nodes_2d = nodes_2d.filter(coordinates__in_bbox=bbox)
#         if nodes_2d.count == 0:
#             raise Exception('No 2d nodes found within bounding box.')
#
#     # Calculate mini arrows
#     outflow = flow_per_node(lines_2d, start_time=start_time, end_time=end_time)
#     # if there are any 2d open water nodes without flowlinks, there will be a shape mismatch between 'outflow' and nodes
#     linkless_node_ids = nodes_2d.id[np.logical_not(np.in1d(nodes_2d.id, outflow[:, 0]))]
#     zeroes = np.zeros(linkless_node_ids.size * 2).reshape(2, linkless_node_ids.size)
#     linkless_node_outflow = np.c_[linkless_node_ids, zeroes.T]
#     outflow = np.vstack([outflow, linkless_node_outflow])
#     outflow = outflow[outflow[:, 0].argsort()]  # sort by first column, i.e., node id
#     mini_arrows = np.c_[outflow, nodes_2d.data['coordinates'].T]
#     # Calculate cell size per node
#     cell_sizes = gr.grid.dx
#     coordinates = nodes_2d.data['cell_coords']
#     dx = coordinates[2, :] - coordinates[0, :]
#
#     # Process nodes by cell size
#     first_pass = True
#     for i, cell_size in enumerate(cell_sizes):
#         if cell_size in dx:  # if bbox is used, the selected data may not contain all cell sizes in the model
#             cells_size_i_idx = np.where(dx == cell_size)  # indices of the nodes that have cell size i
#             cells_size_i_ids = nodes_2d.id[cells_size_i_idx]  # ids of the nodes that have cell size i
#
#             # select q_2d_cum_out_x_sum and q_2d_cum_out_y_sum for the ids in this set
#             # this works because mini_arrows array and nodes_2d.data are both sorted by id
#             mini_arrows_i = mini_arrows[np.in1d(mini_arrows[:, 0], cells_size_i_ids), :]
#             if first_pass:  # no resampling required for smallest cell size
#                 mini_arrows_resampled = mini_arrows_i
#                 first_pass = False
#             elif i > 0:
#                 # resample to grid_space
#                 mini_arrows_i_resampled = resample_mini_arrows(mini_arrows_i, src_cell_size=cell_size,
#                                                                tgt_cell_size=cell_sizes[0])
#                 # add to the existing result set
#                 mini_arrows_resampled = np.vstack([mini_arrows_resampled, mini_arrows_i_resampled])
#
#     rich_arrows = enrich_mini_arrows(mini_arrows_resampled, cell_size=cell_sizes[0])
#     mem_mini_arrows = mini_arrows_to_ogr(src=rich_arrows, tgt_layer=tgt_layer)
#
#     return mem_mini_arrows

#
# def MiniArrowsIO(GridAdminH5, Results3DiNetCDF, tgtLayer, tgtFileName=None, host=None, port=5432, database=None,
#                  user=None, password=None, **kwargs):
#     # Make a GridH5ResultAdmin object
#     gr = GridH5ResultAdmin(GridAdminH5, Results3DiNetCDF)
#
#     kwargs['tgtLayer'] = tgtLayer
#     kwargs['gr'] = gr
#     # kwargs['bbox'] = bbox
#     # kwargs['start_time'] = start_time
#     # kwargs['end_time'] = end_time
#
#     # Determine output format and location
#     if tgtFileName is None:  # case: result must be written to database
#         tgtDS = ogr_connection(host=host, port=port, user=user, password=password,
#                                database=database)  # will raise exception if connection details are incorrect
#         if tgtDS is None:
#             raise Exception(
#                 'Could not establish connection with database with connection details: host={h}, port={p}, user={u}, '
#                 'database={d}'.format(
#                     h=host, p=port, u=user, d=database))
#         tgtDS.ExecuteSQL('CREATE EXTENSION IF NOT EXISTS postgis;')
#         if len(tgtLayer.split('.')) > 1:
#             tgtDS.ExecuteSQL('CREATE SCHEMA IF NOT EXISTS {};'.format(tgtLayer.split('.')[0]))
#
#     else:  # case: result must be written to file
#         if not (host is None and database is None and user is None and password is not None):
#             print('Notice: tgtFileName specified, database connection parameters are ignored.')
#         extension = tgtFileName.split('.')[-1].lower()
#         extensionMapping = get_extension_mapping(vector=True, raster=False, create_capability=True)
#         tgtDriverName = extensionMapping[extension]
#         tgtDriver = ogr.GetDriverByName(tgtDriverName)
#         tgtDS = tgtDriver.CreateDataSource(tgtFileName)
#
#     # Make miniArrows
#     print('Calculating mini arrows...')
#     mem_mini_arrows = make_mini_arrows(**kwargs)
#
#     # open layer
#     print('Writing mini arrows to target file or database...')
#     srcLayer = mem_mini_arrows.GetLayer(tgtLayer)
#     outLayer = tgtDS.CopyLayer(src_layer=srcLayer, new_name=tgtLayer,
#                                options=['GEOMETRY_NAME=geom', 'OVERWRITE=YES', 'PGSQL_OGR_FID=uid',
#                                         'PG_USE_COPY=YES']
#                                )
#
#     # materialize layer
#     outLayer = None
#     tgtDS = None
#     srcLayer = None
#
#     print('Successfully created mini arrows.')
#     return 0


def demanded_aggregation_as_column_name(da):
    column_name_list = []
    try:
        column_name_list.append(da['variable'])
        if AGGREGATION_VARIABLES.get_by_short_name(da['variable']).signed:
            column_name_list.append(da['sign'])
        column_name_list.append(da['method'])
        if da['method'] in ['above_thres', 'below_thres']:
            thres_parsed = str(da['threshold']).replace('.', '_')
            column_name_list.append(thres_parsed)
        return '_'.join(column_name_list).lower()
    except KeyError:
        return None

def filter_demanded_aggregations(das, variable_types):
    result = []
    for da in das:
        var_short_name = da['variable']
        variable = AGGREGATION_VARIABLES.get_by_short_name(var_short_name)
        if variable.var_type in variable_types:
            result.append(da)
    return result


def threedigrid_to_ogr(threedigrid_src, tgt_ds, attributes: dict, attr_data_types: dict, epsg: int = 28992):
    """
    Create a ogr layer from the coordinates of threedigrid Nodes, Cells, or Lines with custom attributes

    :param threedigrid_src: threedigrid Nodes, Cells, or Lines object
    :param tgt_ds: ogr Datasource
    :param attributes: {attribute name: list of values}
    :param attr_data_types: {attribute name: ogr data type}
    :param epsg: EPSG code
    :return: ogr Datasource
    """
    if isinstance(threedigrid_src, Nodes):
        src_type = Nodes
        coords = threedigrid_src.coordinates
        invalid_coords = np.array([-9999, -9999])
        out_layer_name = 'node'
        out_geom_type = ogr.wkbPoint
    if isinstance(threedigrid_src, Cells):
        src_type = Cells
        coords = threedigrid_src.cell_coords
        invalid_coords = np.array([-9999, -9999, -9999, -9999])
        out_layer_name = 'cell'
        out_geom_type = ogr.wkbPolygon
    if isinstance(threedigrid_src, Lines):
        src_type = Lines
        coords = threedigrid_src.line_coords
        invalid_coords = np.array([-9999, -9999, -9999, -9999])
        out_layer_name = 'flowline'
        out_geom_type = ogr.wkbLineString

    # create layer
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(epsg)
    out_layer = tgt_ds.CreateLayer(out_layer_name, srs, geom_type=out_geom_type)

    # create fields
    for attr in attributes.keys():
        field = ogr.FieldDefn(attr, attr_data_types[attr])
        out_layer.CreateField(field)

    feature_defn = out_layer.GetLayerDefn()

    # create features
    for i in range(threedigrid_src.count):
        if np.all(np.equal(coords[:, i], invalid_coords)):  # skip if coordinates are invalid
            continue
        else:
            # create feature geometry
            feature = ogr.Feature(feature_defn)
            geom = ogr.Geometry(out_geom_type)
            if src_type == Nodes:
                x, y = coords[:, i]
                geom.SetPoint(0, x, y)
                feature.SetGeometry(geom)
            elif src_type == Lines:
                x0, y0, x1, y1 = coords[:, i]
                geom.AddPoint(float(x0), float(y0))
                geom.AddPoint(float(x1), float(y1))
                feature.SetGeometry(geom)
            elif src_type == Cells:
                xmin, ymin, xmax, ymax = coords[:, i]
                geom_ring = ogr.Geometry(ogr.wkbLinearRing)
                geom_ring.AddPoint(xmin, ymin)
                geom_ring.AddPoint(xmin, ymax)
                geom_ring.AddPoint(xmax, ymax)
                geom_ring.AddPoint(xmax, ymin)
                geom_ring.AddPoint(xmin, ymin)
                geom.AddGeometry(geom_ring)
                if (not geom.IsValid()) or geom.IsEmpty():
                    continue
                else:
                    feature.SetGeometry(geom)

            # create feature attributes
            for attr in attributes.keys():
                val = attributes[attr][i]
                if attr_data_types[attr] in [ogr.OFTInteger]:
                    val = int(val)
                if attr_data_types[attr] in [ogr.OFTString]:
                    if type(val) == np.str_:
                        val = str(val)
                    else:
                        val = val.decode('utf-8')
                feature.SetField(attr, val)

            # create the actual feature
            out_layer.CreateFeature(feature)
            feature = None

    return


def aggregate_threedi_results(gridadmin: str, results_3di: str, demanded_aggregations: list,
                              bbox=None, start_time: int = None, end_time: int = None, subsets=None, epsg: int = 28992,
                              interpolation_method: str = None, resolution: float = None):
    """

    :param gridadmin: path to gridadmin.h5
    :param results_3di: path to results_3di.nc
    :param demanded_aggregations: list of dicts containing variable, method, [threshold]
    :param bbox: bounding box [min_x, min_y, max_x, max_y]
    :param start_time: start of time filter (seconds since start of simulation)
    :param end_time: end of time filter (seconds since start of simulation)
    :param subsets:
    :param epsg: epsg code to project the results to
    :return: an ogr Memory DataSource with one or more Layers: node (point), cell (polygon) or flowline (linestring) with the aggregation results
    :rtype: ogr.DataSource
    """

    # perform demanded aggregations
    node_results = dict()
    line_results = dict()
    first_pass_nodes = True
    first_pass_flowlines = True
    for da in demanded_aggregations:
        # It would seem more sensical to keep the instantiatian of gr, the subsetting and filtering outside the loop...
        # ... but for some strange reason that leads to an error if more than 2 flowline aggregations are demanded
        gr = GridH5ResultAdmin(gridadmin, results_3di)

        # TODO: select subset

        # Spatial filtering
        if bbox is None:
            lines = gr.lines
            nodes = gr.nodes
            cells = gr.cells
        else:
            if bbox[0] >= bbox[2] or bbox[1] >= bbox[3]:
                raise Exception('Invalid bounding box.')
            lines = gr.lines.filter(line_coords__in_bbox=bbox)
            if lines.count == 0:
                raise Exception('No flowlines found within bounding box.')
            nodes = gr.nodes.filter(coordinates__in_bbox=bbox)
            cells = gr.cells.filter(
                coordinates__in_bbox=bbox)  # filter on cell center coordinates to have the same results for cells as for nodes
            if nodes.count == 0:
                raise Exception('No nodes found within bounding box.')

        new_column_name = demanded_aggregation_as_column_name(da)
        if da['variable'] in AGGREGATION_VARIABLES.short_names(var_types=[VT_FLOW]):
            if first_pass_flowlines:
                line_results['id'] = lines.id.astype(int)
                if gr.has_1d:
                    line_results['content_type'] = lines.content_type
                    line_results['spatialite_id'] = lines.content_pk
                line_results['kcu'] = lines.kcu
                line_results['kcu_description'] = np.vectorize(KCU_DICT.get)(lines.kcu)
                first_pass_flowlines = False
            line_results[new_column_name] = time_aggregate(nodes_or_lines=lines,
                                                           start_time=start_time,
                                                           end_time=end_time,
                                                           variable=da['variable'],
                                                           sign=da['sign'],
                                                           method=da['method'],
                                                           threshold=da['threshold'],
                                                           multiplier=da['multiplier']
                                                           )
        elif da['variable'] in AGGREGATION_VARIABLES.short_names(var_types=[VT_NODE]):
            if first_pass_nodes:
                node_results['id'] = nodes.id.astype(int)
                if gr.has_1d:
                    node_results['spatialite_id'] = nodes.content_pk
                node_results['node_type'] = nodes.node_type
                node_results['node_type_description'] = np.vectorize(NODE_TYPE_DICT.get)(nodes.node_type)
                first_pass_nodes = False
            node_results[new_column_name] = time_aggregate(nodes_or_lines=nodes,
                                                           start_time=start_time,
                                                           end_time=end_time,
                                                           variable=da['variable'],
                                                           sign=da['sign'],
                                                           method=da['method'],
                                                           threshold=da['threshold'],
                                                           multiplier=da['multiplier']
                                                           )
        elif da['variable'] in AGGREGATION_VARIABLES.short_names(var_types=[VT_NODE_HYBRID]):
            if first_pass_nodes:
                node_results['id'] = nodes.id.astype(int)
                if gr.has_1d:
                    node_results['spatialite_id'] = nodes.content_pk
                node_results['node_type'] = nodes.node_type
                node_results['node_type_description'] = np.vectorize(NODE_TYPE_DICT.get)(nodes.node_type)
                first_pass_nodes = False
            node_results[new_column_name] = hybrid_time_aggregate(gr=gr,
                                                                  ids=nodes.id,
                                                                  start_time=start_time,
                                                                  end_time=end_time,
                                                                  variable=da['variable'],
                                                                  sign=da['sign'],
                                                                  method=da['method'],
                                                                  threshold=da['threshold'],
                                                                  multiplier=da['multiplier']
                                                                  )

    # make output datasource and layers
    tgt_drv = ogr.GetDriverByName('MEMORY')
    tgt_ds = tgt_drv.CreateDataSource('')
    out_rasters = {}

    # node and cell layers
    if len(node_results) > 0:
        attributes = node_results
        attr_data_types = {}
        for attr, vals in node_results.items():
            try:
                attr_data_types[attr] = NP_OGR_DTYPES[vals.dtype]
            except KeyError:
                attr_data_types[attr] = ogr.OFTString
        threedigrid_to_ogr(threedigrid_src=nodes, tgt_ds=tgt_ds, attributes=attributes, attr_data_types=attr_data_types)
        threedigrid_to_ogr(threedigrid_src=cells, tgt_ds=tgt_ds, attributes=attributes, attr_data_types=attr_data_types)

        # rasters
        cell_layer = tgt_ds.GetLayerByName('cell')
        if cell_layer.GetFeatureCount() > 0:
            first_pass_rasters = True
            if resolution is None:
                resolution = gr.grid.dx[0]
            column_names = []
            band_nr = 0
            # for col in node_results.keys():
            for da in demanded_aggregations:
                if da['variable'] in AGGREGATION_VARIABLES.short_names(var_types=[VT_NODE, VT_NODE_HYBRID]):
                    col = demanded_aggregation_as_column_name(da)
                    band_nr += 1
                    agg_var = AGGREGATION_VARIABLES.get_by_short_name(da['variable'])
                    prm=agg_var.pre_resample_method
                    out_rasters[col] = rasterize_cell_layer(cell_layer=cell_layer,
                                                            column_name=col,
                                                            pixel_size=resolution,
                                                            interpolation_method=interpolation_method,
                                                            pre_resample_method=prm)
                    ndv = out_rasters[col].GetRasterBand(1).GetNoDataValue()
                    column_names.append(col)
                    if first_pass_rasters:
                        first_pass_rasters = False
                        tmp_drv = gdal.GetDriverByName('MEM')
                        tmp_ds = tmp_drv.CreateCopy('multiband', out_rasters[col])

                        # create output layer
                        srs = osr.SpatialReference()
                        srs.ImportFromWkt(tmp_ds.GetProjection())
                        points_resampled_lyr = tgt_ds.CreateLayer('node_resampled',
                                                                  srs=srs,
                                                                  geom_type=ogr.wkbPoint)
                        field = ogr.FieldDefn(col, ogr.OFTReal)
                        points_resampled_lyr.CreateField(field)
                    else:
                        tmp_ds.AddBand(datatype=gdal.GDT_Float32)
                        src_band = out_rasters[col].GetRasterBand(1)
                        src_arr = src_band.ReadAsArray()
                        tmp_band = tmp_ds.GetRasterBand(band_nr)
                        tmp_band.WriteArray(src_arr)
                        tmp_band.SetNoDataValue(src_band.GetNoDataValue())
                        field = ogr.FieldDefn(col, ogr.OFTReal)
                        points_resampled_lyr.CreateField(field)

            tmp_points_resampled = pixels_to_geoms(raster=tmp_ds,
                                                   column_names=column_names,
                                                   output_geom_type=ogr.wkbPoint,
                                                   output_layer_name='unimportant name')
            tmp_points_resampled_lyr = tmp_points_resampled.GetLayer(0)
            for feat in tmp_points_resampled_lyr:
                points_resampled_lyr.CreateFeature(feat)
                feat = None

    # flowline layer
    if len(line_results) > 0:
        attributes = line_results
        attr_data_types = {}
        for attr, vals in line_results.items():
            try:
                attr_data_types[attr] = NP_OGR_DTYPES[vals.dtype]
            except KeyError:
                attr_data_types[attr] = ogr.OFTString
        threedigrid_to_ogr(threedigrid_src=lines, tgt_ds=tgt_ds, attributes=attributes, attr_data_types=attr_data_types)

    return tgt_ds, out_rasters


def get_parser():
    """ Return argument parser. """
    parser = argparse.ArgumentParser(
        description=__doc__
    )
    parser.add_argument(metavar='GRIDADMIN', dest='GridAdminH5', help='gridadmin.h5 file name')
    parser.add_argument(metavar='RESULTSNETCDF', dest='Results3DiNetCDF', help='results_3di.nc file name')
    parser.add_argument(metavar='OUTPUT_LAYER', dest='tgtLayer', help='Output layer name')
    parser.add_argument('-fn', dest='tgtFileName',
                        help='Target file name. If specified, database parameters are ignored.')
    parser.add_argument('-ho', dest='host', help='PG host name.')
    parser.add_argument('-po', dest='port', help='PG port. Defaults to 5432.')
    parser.add_argument('-d', dest='database', help='PG database name.')
    parser.add_argument('-u', dest='user', help='PG username.')
    parser.add_argument('-pw', dest='password', help='PG password.')
    parser.add_argument('-b', dest='bbox', metavar='COORD', nargs=4, type=float,
                        help='Bounding box. Format: MinX MinY MaxX MaxY')
    parser.add_argument('-s -start', dest='start_time', metavar='START_TIME', type=int,
                        help='Start time in s from start of simulation')
    parser.add_argument('-e -end', dest='end_time', metavar='END_TIME', type=int,
                        help='End time in s from start of simulation')

    return parser


def main():
    """ Call command with args from parser. """
    # kwargs = vars(get_parser().parse_args())
    # NotNoneKwargs = {k: v for k, v in kwargs.items() if v is not None}
    # MiniArrowsIO(**NotNoneKwargs)
    pass


if __name__ == '__main__':
    exit(main())
