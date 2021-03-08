#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Calculate the resultant of the total outflow per node, resampled to grid_space """
#TODO: aggregatie-NetCDF ook gebruiken

import argparse
import warnings
from typing import List

from threedigrid.admin.gridresultadmin import GridH5ResultAdmin
from threedigrid.admin.nodes.models import Nodes, Cells
from threedigrid.admin.lines.models import Lines

import gdal
import numpy as np
import ogr
import osr

try:
    from constants import *
    from threedigrid_ogr import *
except ImportError:
    from .constants import *
    from .threedigrid_ogr import *

warnings.filterwarnings('ignore')
ogr.UseExceptions()


def time_intervals(nodes_or_lines, start_time, end_time):
    """Get a 1D numpy array of time intervals between timestamps, inclusing 'broken' first and last time intervals
    It also returns the last timestamp before start_time (ts_start_time)
    and the first timestamp after end_time (ts_end_time)
    The length of the time_intervals arrays is guaranteed to be the same as the number of timestamps between
    the returned ts_start_time and ts_end_time"""
    last_timestamp = nodes_or_lines.timestamps[-1]
    if end_time is None or end_time > last_timestamp:
        end_time = last_timestamp
    if start_time is None or start_time < 0:
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


def find_finite_1d(x: np.array, index: int):
    """ Find the a finite (non-nan) value in a numpy 1d array,
    returning np.nan if the array contains no valid value

    :param x: numpy 1d array
    :param index: which finite value to return, e.g. 0 for first finite value, -1 for last finite value
    """
    try:
        return x[np.isfinite(x)][index]
    except IndexError:
        return np.nan


def time_aggregate(nodes_or_lines, start_time, end_time, aggregation: Aggregation,
                   cfl_strictness=1):
    """
    Aggregate the variable with method using threshold within time frame

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
    if aggregation.variable.short_name in ['q', 'u1', 'au']:
        raw_values = getattr(ts, aggregation.variable.short_name)
    elif aggregation.variable.short_name == 'ts_max':
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
    elif aggregation.variable.short_name in ['s1', 'vol', 'rain', 'su', 'ucx', 'ucy', 'infiltration_rate_simple',
                                             'q_lat', 'intercepted_volume', 'q_sss']:
        raw_values = getattr(ts, aggregation.variable.short_name)
    elif aggregation.variable.short_name == 'rain_depth':
        ts_rain = ts.rain
        ts_rain[ts_rain == -9999] = np.nan
        raw_values = np.divide(ts_rain, nodes_or_lines.sumax)
    elif aggregation.variable.short_name == 'uc':
        ucx = ts.ucx
        ucx[ucx == -9999] = np.nan
        ucy = ts.ucy
        ucy[ucy == -9999] = np.nan
        raw_values = np.sqrt(np.square(ucx), np.square(ucy))
    elif aggregation.variable.short_name == 'infiltration_rate_simple_mm':
        ts_infiltration_rate_simple = ts.infiltration_rate_simple
        ts_infiltration_rate_simple[ts_infiltration_rate_simple == -9999] = np.nan
        raw_values = np.divide(ts_infiltration_rate_simple, ts.sumax)
    elif aggregation.variable.short_name == 'q_lat_mm':
        ts_q_lat = ts.q_lat
        ts_q_lat[ts_q_lat == -9999] = np.nan
        raw_values = np.divide(ts_q_lat, nodes_or_lines.sumax)
    elif aggregation.variable.short_name == 'intercepted_volume_mm':
        ts_intercepted_volume = ts.intercepted_volume
        ts_intercepted_volume[ts_intercepted_volume == -9999] = np.nan
        raw_values = np.divide(ts_intercepted_volume, nodes_or_lines.sumax)
    elif aggregation.variable.short_name == 'q_sss_mm':
        ts_q_sss = ts.q_sss
        ts_q_sss[ts_q_sss == -9999] = np.nan
        raw_values = np.divide(ts_q_sss, nodes_or_lines.sumax)

    else:
        raise ValueError('Unknown aggregation variable "{}".'.format(aggregation.variable.long_name))

    # replace -9999 in raw values by NaN
    raw_values[raw_values == -9999] = np.nan

    # reverse flow direction in 1d-2d links
    # threedigrid reads these flowlines from the netcdf in reversed order (known inconsistency)
    if isinstance(nodes_or_lines, Lines):
        kcu_types_1d2d = np.array([51, 52, 53, 54, 54, 55, 56, 57, 58])
        raw_values[:, np.in1d(nodes_or_lines.kcu, kcu_types_1d2d)] *= -1

    if aggregation.sign.short_name == 'pos':
        raw_values_signed = raw_values * (raw_values >= 0).astype(int)
    elif aggregation.sign.short_name == 'neg':
        raw_values_signed = raw_values * (raw_values < 0).astype(int)
    elif aggregation.sign.short_name == 'abs':
        raw_values_signed = np.absolute(raw_values)
    elif aggregation.sign.short_name == 'net':
        raw_values_signed = raw_values
    else:
        raw_values_signed = raw_values

    # Apply method
    if aggregation.method.short_name == 'sum':
        raw_values_per_time_interval = np.multiply(raw_values_signed.T, tintervals).T
        result = np.sum(raw_values_per_time_interval, axis=0)
    elif aggregation.method.short_name == 'min':
        result = np.nanmin(raw_values_signed, axis=0)
    elif aggregation.method.short_name == 'max':
        result = np.nanmax(raw_values_signed, axis=0)
    elif aggregation.method.short_name == 'max_time':
        raw_values_signed[np.isnan(raw_values_signed)] = -9999
        first_max_pos = np.nanargmax(raw_values_signed, axis=0)
        time_steps = np.cumsum(np.insert(tintervals[0:-1], 0, start_time))
        result = time_steps[first_max_pos]
    elif aggregation.method.short_name == 'mean':
        result = np.nanmean(raw_values_signed, axis=0)
    elif aggregation.method.short_name == 'median':
        result = np.nanmedian(raw_values_signed, axis=0)
    elif aggregation.method.short_name == 'first':
        result = raw_values_signed[0, :]
    elif aggregation.method.short_name == 'first_non_empty':
        result = np.array([find_finite_1d(col, index=0) for col in raw_values_signed.T])
    elif aggregation.method.short_name == 'last':
        result = raw_values_signed[-1, :]
    elif aggregation.method.short_name == 'last_non_empty':
        result = np.array([find_finite_1d(col, index=-1) for col in raw_values_signed.T])
    elif aggregation.method.short_name == 'above_thres':
        raw_values_above_threshold = np.greater(raw_values_signed, aggregation.threshold)
        time_above_treshold = np.sum(np.multiply(raw_values_above_threshold.T, tintervals).T, axis=0)
        total_time = np.sum(tintervals)
        result = np.multiply(np.divide(time_above_treshold, total_time), 100.0)
    elif aggregation.method.short_name == 'below_thres':
        raw_values_below_threshold = np.less(raw_values_signed, aggregation.threshold)
        time_below_treshold = np.sum(np.multiply(raw_values_below_threshold.T, tintervals).T, axis=0)
        total_time = np.sum(tintervals)
        result = np.multiply(np.divide(time_below_treshold, total_time), 100.0)
    else:
        raise ValueError('Unknown aggregation method "{}".'.format(aggregation.method.long_name))

    # multiplier (unit conversion)
    result *= aggregation.multiplier

    return result


def hybrid_time_aggregate(gr,
                          ids,
                          start_time,
                          end_time,
                          aggregation):
    if 'q_' in aggregation.variable.short_name:
        flows = flow_per_node(gr=gr, node_ids=ids,
                              start_time=start_time,
                              end_time=end_time,
                              out='_out' in aggregation.variable.short_name,
                              aggregation_method=aggregation.method)
        if '_x' in aggregation.variable.short_name:
            result = flows[:, 1]
        elif '_y' in aggregation.variable.short_name:
            result = flows[:, 2]
        else:
            raise ValueError('Unknown aggregation variable "{}".'.format(aggregation.variable.long_name))
        if '_mm' in aggregation.variable.short_name:
            surface_area = gr.nodes.filter(id__in=ids).sumax
            result = result / surface_area
    else:
        raise ValueError('Unknown aggregation variable "{}".'.format(aggregation.variable.long_name))

    result *= aggregation.multiplier

    return result


def flow_per_node(gr: GridH5ResultAdmin, node_ids: list, start_time: int, end_time: int, out: bool, aggregation_method):
    """
    Calculate the aggregate of all flows per node, split in x and y directions

    :param out: if True, only outgoing flows are calculated. If false, only incoming flows
    :returns: numpy 2d array; columns: node ids, x sign flow, y sign flow
    """
    lines = filter_lines_by_node_ids(gr.lines, node_ids)

    start_end_node_ids = lines.line_nodes.T.reshape(
        lines.line_nodes.size)  # 1d array with first all start nodes, than all end nodes
    # if there are any nodes without flowlinks, they will not be included in start_end_node_ids
    # this is dealt with just before the end of this function

    da = Aggregation(variable=AGGREGATION_VARIABLES.get_by_short_name('q'),
                     method=aggregation_method,
                     sign=AggregationSign(short_name='net', long_name='Net')
                     )
    q_agg = time_aggregate(nodes_or_lines=lines,
                           start_time=start_time,
                           end_time=end_time,
                           aggregation=da)
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


def empty_raster_from_vector_layer(layer, pixel_size_x, pixel_size_y, bands=1, nodatavalue=-9999):
    """ Create in-memory gdal dataset of the same size as the input target_node_layer, filled with nodatavalue. """
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
                out_value = in_value / (in_cell_size / pixel_size) ** 2
            elif pre_resample_method == PRM_1D:  # for flows (q) in x or y sign: scale with pixel resolution;
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
    Convert a single or multiband raster to a point or polygon target_node_layer.

    Each feature represents one pixel. The raster values are stored in the output target_node_layer attributes.
    Raster bands are mapped to column names by mapping column_names list order to the raster bands order.

    :param raster: gdal Dataset
    :param column_names: list of column names for the output layers, or str for singleband raster
    :param output_geom_type: ogr wkpPoint or wkbPolygon
    :param output_layer_name: name of the output target_node_layer
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


def aggregate_threedi_results(gridadmin: str, results_3di: str, demanded_aggregations: List[Aggregation],
                              bbox=None, start_time: int = None, end_time: int = None, subsets=None, epsg: int = 28992,
                              interpolation_method: str = None, resample_point_layer: bool = False,
                              resolution: float = None, output_flowlines: bool = True, output_nodes: bool = True,
                              output_cells: bool = True, output_rasters: bool = True):
    """
    # TODO: use new version of threedi_ogr that inludes adding default attributes to nodes, cells and flowline layers
    :param resolution:
    :param interpolation_method:
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

    # make output datasource and layers
    tgt_drv = ogr.GetDriverByName('MEMORY')
    tgt_ds = tgt_drv.CreateDataSource('')
    out_rasters = {}

    if not (output_flowlines or output_nodes or output_cells or output_rasters):
        return tgt_ds, out_rasters

    if resample_point_layer and (not output_nodes):
        resample_point_layer = False

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

        new_column_name = da.as_column_name()

        if da.variable.short_name in AGGREGATION_VARIABLES.short_names(var_types=[VT_FLOW]):
            if output_flowlines:
                if first_pass_flowlines:
                    first_pass_flowlines = False
                try:
                    line_results[new_column_name] = time_aggregate(nodes_or_lines=lines,
                                                                   start_time=start_time,
                                                                   end_time=end_time,
                                                                   aggregation=da
                                                                   )
                except AttributeError:
                    warnings.warn('Demanded aggregation of variable that is not included in these 3Di results')
                    line_results[new_column_name] = np.full(len(line_results['id']), fill_value=None, dtype=np.float)

        elif da.variable.short_name in AGGREGATION_VARIABLES.short_names(var_types=[VT_NODE]):
            if output_nodes or output_cells or output_rasters:
                if first_pass_nodes:
                    first_pass_nodes = False
                try:
                    node_results[new_column_name] = time_aggregate(nodes_or_lines=nodes,
                                                                   start_time=start_time,
                                                                   end_time=end_time,
                                                                   aggregation=da
                                                                   )
                except AttributeError:
                    warnings.warn('Demanded aggregation of variable that is not included in these 3Di results')
                    node_results[new_column_name] = np.full(len(node_results['id']), fill_value=None, dtype=np.float)

        elif da.variable.short_name in AGGREGATION_VARIABLES.short_names(var_types=[VT_NODE_HYBRID]):
            if output_nodes or output_cells or output_rasters:
                if first_pass_nodes:
                    first_pass_nodes = False
                try:
                    node_results[new_column_name] = hybrid_time_aggregate(gr=gr,
                                                                          ids=nodes.id,
                                                                          start_time=start_time,
                                                                          end_time=end_time,
                                                                          aggregation=da
                                                                          )
                except AttributeError:
                    warnings.warn('Demanded aggregation of variable that is not included in these 3Di results')
                    node_results[new_column_name] = np.full(len(node_results['id']), fill_value=None, dtype=np.float)

    # translate results to GIS layers
    # node and cell layers
    if len(node_results) > 0:
        attributes = node_results
        attr_data_types = {}
        for attr, vals in node_results.items():
            try:
                attr_data_types[attr] = NP_OGR_DTYPES[vals.dtype]
            except KeyError:
                attr_data_types[attr] = ogr.OFTString
        if output_nodes:
            threedigrid_to_ogr(threedigrid_src=nodes,
                               tgt_ds=tgt_ds,
                               attributes=attributes,
                               attr_data_types=attr_data_types
                               )
        if output_cells or output_rasters or resample_point_layer:
            threedigrid_to_ogr(threedigrid_src=cells,
                               tgt_ds=tgt_ds,
                               attributes=attributes,
                               attr_data_types=attr_data_types
                               )

        # rasters
        if output_rasters or resample_point_layer:
            cell_layer = tgt_ds.GetLayerByName('cell')
            if cell_layer.GetFeatureCount() > 0:
                first_pass_rasters = True
                if (resolution is None or resolution == 0):
                    resolution = gr.grid.dx[0]
                column_names = []
                band_nr = 0
                for da in demanded_aggregations:
                    if da.variable.short_name in AGGREGATION_VARIABLES.short_names(var_types=[VT_NODE, VT_NODE_HYBRID]):
                        col = da.as_column_name()
                        band_nr += 1
                        out_rasters[col] = rasterize_cell_layer(cell_layer=cell_layer,
                                                                column_name=col,
                                                                pixel_size=resolution,
                                                                interpolation_method=interpolation_method,
                                                                pre_resample_method=da.variable.pre_resample_method)
                        column_names.append(col)
                        if first_pass_rasters:
                            first_pass_rasters = False
                            tmp_drv = gdal.GetDriverByName('MEM')
                            tmp_ds = tmp_drv.CreateCopy('multiband', out_rasters[col])

                            # create resampled nodes output target_node_layer
                            if resample_point_layer:
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
                            if resample_point_layer:
                                field = ogr.FieldDefn(col, ogr.OFTReal)
                                points_resampled_lyr.CreateField(field)

                if resample_point_layer:
                    tmp_points_resampled = pixels_to_geoms(raster=tmp_ds,
                                                           column_names=column_names,
                                                           output_geom_type=ogr.wkbPoint,
                                                           output_layer_name='unimportant name')
                    tmp_points_resampled_lyr = tmp_points_resampled.GetLayer(0)
                    for feat in tmp_points_resampled_lyr:
                        points_resampled_lyr.CreateFeature(feat)
                        feat = None

    # flowline target_node_layer
    if len(line_results) > 0 and output_flowlines:
        attributes = line_results
        attr_data_types = {}
        for attr, vals in line_results.items():
            try:
                attr_data_types[attr] = NP_OGR_DTYPES[vals.dtype]
            except KeyError:
                attr_data_types[attr] = ogr.OFTString
        threedigrid_to_ogr(threedigrid_src=lines, tgt_ds=tgt_ds, attributes=attributes, attr_data_types=attr_data_types)

    if not output_rasters:
        out_rasters = {}
    if (not output_cells) and (resample_point_layer or output_rasters):
        tgt_ds.DeleteLayer('cell')
    return tgt_ds, out_rasters


def get_parser():
    """ Return argument parser. """
    parser = argparse.ArgumentParser(
        description=__doc__
    )
    parser.add_argument(metavar='GRIDADMIN', dest='GridAdminH5', help='gridadmin.h5 file name')
    parser.add_argument(metavar='RESULTSNETCDF', dest='Results3DiNetCDF', help='results_3di.nc file name')
    parser.add_argument(metavar='OUTPUT_LAYER', dest='tgtLayer', help='Output target_node_layer name')
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
