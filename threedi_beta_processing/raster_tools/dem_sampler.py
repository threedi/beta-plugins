# -*- coding: utf-8 -*-
# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
"""
Convert a shapefile containing 2D linestrings to a shapefile with embedded
elevation from an elevation map.

Target shapefile can have two layouts: A 'point' layout where the elevation is
stored in the third coordinate of a 3D linestring, and a 'line' layout where a
separate feature is created in the target shapefile for each segment of each
feature in the source shapefile, with two extra attributes compared to the
original shapefile, one to store the elevation, and another to store an
arbitrary feature id referring to the source feature in the source shapefile.
"""

import argparse
import logging
import math
import os
import sys

from osgeo import gdal, gdal_array
from osgeo import ogr
from scipy import ndimage
import numpy as np

from . import utils
from . import vectors

logger = logging.getLogger(__name__)

LAYOUT_POINT = 'point'
LAYOUT_LINE = 'line'

DRIVER = ogr.GetDriverByName('ESRI Shapefile')
LINESTRINGS = ogr.wkbLineString, ogr.wkbLineString25D
MULTILINESTRINGS = ogr.wkbMultiLineString, ogr.wkbMultiLineString25D


def get_carpet(parameterized_line, distance, step, left=True, right=True):
    """
    Return M x N x 2 numpy array.

    It contains the centers of the ParameterizedLine, but perpendicularly
    repeated by step along the normals to the segments of the
    ParameterizedLine, until distance is reached.
    """
    # length must be uneven, and no less than 2 * distance / step + 1
    steps = math.ceil(distance / step)

    if left:
        range_start = -steps
    else:
        range_start = 0
    if right:
        range_end = steps
    else:
        range_end = 0
    offsets_1d = step * np.arange(range_start, range_end + 1)

    # normalize and rotate the vectors of the linesegments
    rvectors = vectors.rotate(parameterized_line.vectors, 270)
    nvectors = vectors.normalize(rvectors)

    offsets_2d = nvectors.reshape(-1, 1, 2) * offsets_1d.reshape(1, -1, 1)
    points = offsets_2d + parameterized_line.centers.reshape(-1, 1, 2)

    return points


def average_result(amount, inverse, lines, centers, values):
    """
    Return dictionary of numpy arrays.

    Centers and values are averaged in groups of amount, but lines are
    converted per group to a line from the start point of the first line
    in the group to the end point of the last line in the group.
    """
    # limit amount to sample size
    sample = values.size
    if amount > sample:
        amount = sample

    # determine the number of groups
    groups = -(-sample // amount)

    # determine indices to pick the result lines from the original lines
    indices = (
        (np.arange(0,
                   sample,
                   amount).reshape(-1, 1) + [0, amount - 1]).ravel(),
        (np.zeros((groups, 2), 'i8') + [0, 1]).ravel(),
    )
    indices[0][-1] = sample - 1  # last group may not be totally filled

    # calculate centers by averaging
    ma_centers = np.ma.masked_all((amount * groups, 2), dtype=centers.dtype)
    ma_centers[:sample] = centers
    print(groups, amount, 2)
    ma_centers.shape = groups, amount, 2

    # calculate values by chosen aggregation minimum or maximum (if inverse)
    extremum = np.max if inverse else np.min
    ma_values = np.ma.masked_all(amount * groups, dtype=values.dtype)
    ma_values[:sample] = values
    ma_values.shape = groups, amount

    result = {'values': extremum(ma_values, 1),
              'centers': ma_centers.mean(1).data,
              'lines': lines[indices].reshape(groups, 2, 2)}

    return result


class BaseProcessor(object):
    """ Base class for common processor methods. """
    def __init__(
            self,
            raster: gdal.Dataset,
            width: float,
            distance: float,
            inverse: bool = False,
            modify: bool = False,
            average: int = None,
            filter_value: float = None
    ):
        self.raster = raster
        self.width = width
        self.average = average
        self.inverse = inverse
        self.modify = modify
        self.distance = distance
        self.filter_value = filter_value

        self.no_data_value = raster.GetRasterBand(1).GetNoDataValue()

        if modify and not distance:
            logger.warning('Warning: modify option used with zero distance.')

    def read_raster(self, bounds, inflate=False):
        """
        Return numpy array.

        :param bounds: x1, y1, x2, y2 window in pixels, or an ogr geometry
        :param inflate: inflate envelope to grid, to make sure that
            the entire geometry is contained in resulting indices.

        If the bounds fall outside the dataset, the result is padded
        with no data values.
        """
        # find indices
        if isinstance(bounds, ogr.Geometry):
            x1, y1, x2, y2 = self.raster.GetGeoTransform().get_indices(bounds,
                                                            inflate=inflate)
        else:
            x1, y1, x2, y2 = bounds

        # overlapping bounds
        w, h = self.raster.RasterXSize, self.raster.RasterYSize
        p1 = min(w, max(0, x1))
        q1 = min(h, max(0, y1))
        p2 = min(w, max(0, x2))
        q2 = min(h, max(0, y2))

        # result array plus a view for what's actually inside datasets
        gdal_type = self.raster.GetRasterBand(1).DataType
        numpy_type = gdal_array.GDALTypeCodeToNumericTypeCode(gdal_type)
        array = np.full((y2 - y1, x2 - x1), self.no_data_value, numpy_type)
        view = array[q1 - y1: q2 - y1, p1 - x1: p2 - x1]

        kwargs = {'xoff': p1, 'yoff': q1, 'xsize': p2 - p1, 'ysize': q2 - q1}
        # for dataset, no_data_value in zip(self.datasets, self.no_data_values):
        data = self.raster.ReadAsArray(**kwargs)
        index = data != self.no_data_value
        view[index] = data[index]

        return array

    def _modify(self, parameterized_line, points, values, step):
        """ Return dictionary of numpy arrays. """
        # first a minimum or maximum filter with requested width
        filtersize = round(self.width / step)
        if filtersize > 0:
            # choices based on inverse or not
            cval = values.max() if self.inverse else values.min()
            if self.inverse:
                extremum_filter = ndimage.maximum_filter
            else:
                extremum_filter = ndimage.minimum_filter
            # filtering
            fpoints = ndimage.convolve(
                points, np.ones((1, filtersize, 1)) / filtersize,
            )  # moving average for the points
            fvalues = extremum_filter(
                values, size=(1, filtersize), mode='constant', cval=cval,
            )  # moving extremum for the values
        else:
            fpoints = points
            fvalues = values

        if self.inverse:
            # find the minimum per filtered line
            index = (np.arange(len(fvalues)), fvalues.argmin(axis=1))
        else:
            # find the maximum per filtered line
            index = (np.arange(len(fvalues)), fvalues.argmax(axis=1))
        mpoints = fpoints[index]
        mvalues = fvalues[index]

        # sorting points and values according to projection on mline
        parameters = parameterized_line.project(mpoints)
        ordering = parameters.argsort()
        spoints = mpoints[ordering]
        svalues = mvalues[ordering]

        # quick 'n dirty way of getting to result dict
        rlines = np.array([spoints[:-1], spoints[1:]]).transpose(1, 0, 2)
        rcenters = spoints[1:]
        rvalues = svalues[1:]

        return {'lines': rlines, 'values': rvalues, 'centers': rcenters}

    def _calculate(self, wkb_line_string, left=True, right=True, distance_override: float = None):
        """ Return lines, points, values tuple of numpy arrays. """
        # determine the point and values carpets
        geo_transform = self.raster.GetGeoTransform()

        # determine the points
        nodes = np.array(wkb_line_string.GetPoints())     # original nodes
        pline1 = vectors.ParameterizedLine(nodes[:, :2])  # parameterization
        pline2 = pline1.pixelize(geo_transform)           # add pixel edges

        # expand points when necessary
        search_distance = distance_override if distance_override else self.distance
        if search_distance:
            step = geo_transform[1]
            points = get_carpet(step=step,
                                distance=search_distance,
                                parameterized_line=pline2,
                                left=left,
                                right=right
                                )
        else:
            points = pline2.centers.reshape(-1, 1, 2)

        # determine float indices
        x, y = points.transpose()
        p, a, b, q, c, d = geo_transform
        e, f, g, h = utils.get_inverse(a, b, c, d)

        # cast to integer indices
        j = np.int64(e * (x - p) + f * (y - q))
        i = np.int64(g * (x - p) + h * (y - q))

        # read corresponding values from raster
        bounds = (int(j.min()),
                  int(i.min()),
                  int(j.max()) + 1,
                  int(i.max()) + 1)
        array = self.read_raster(bounds)
        values = array[i - bounds[1], j - bounds[0]].transpose()

        # set nodatavalues to NaN
        values[values == self.no_data_value] = np.nan
        
        # set filter value to NaN
        if self.filter_value is not None:
            margin = 0.001
            lower_bound = self.filter_value - margin
            upper_bound = self.filter_value + margin
        
            values[(values >= lower_bound) & (values <= upper_bound)] = np.nan

        # return lines, centers, values
        if self.modify:
            step = geo_transform[1]
            result = self._modify(step=step,
                                  points=points,
                                  values=values,
                                  parameterized_line=pline1)
        else:
            extremum = np.nanmin if self.inverse else np.nanmax
            result = {'lines': pline2.lines,
                      'centers': pline2.centers,
                      'values': extremum(values, 1)}

        if self.average:
            return average_result(amount=self.average,
                                  inverse=self.inverse, **result)
        else:
            return result


class CoordinateProcessor(BaseProcessor):
    """ Writes a shapefile with height in z coordinate. """
    def _convert_wkb_line_string(self, source_wkb_line_string):
        """ Return a wkb line string. """
        result = self._calculate(wkb_line_string=source_wkb_line_string)
        target_wkb_line_string = ogr.Geometry(ogr.wkbLineString)

        # add the first point of the first line
        result = self._calculate(wkb_line_string=source_wkb_line_string)
        (x, y), z = result['lines'][0, 0], result['values'][0]
        target_wkb_line_string.AddPoint(float(x), float(y), float(z))

        # add the centers (x, y) and values (z)
        for (x, y), z in zip(result['centers'], result['values']):
            target_wkb_line_string.AddPoint(float(x), float(y), float(z))

        # add the last point of the last line
        (x, y), z = result['lines'][-1, 1], result['values'][-1]
        target_wkb_line_string.AddPoint(float(x), float(y), float(z))

        return target_wkb_line_string

    def process(self, source_geometry):
        """
        Return converted linestring or multiline.
        """
        geometry_type = source_geometry.GetGeometryType()
        if geometry_type in LINESTRINGS:
            return self._convert_wkb_line_string(source_geometry)
        if geometry_type in MULTILINESTRINGS:
            target_geometry = ogr.Geometry(source_geometry.GetGeometryType())
            for source_wkb_line_string in source_geometry:
                target_geometry.AddGeometry(
                    self._convert_wkb_line_string(source_wkb_line_string),
                )
            return target_geometry
        raise ValueError('Unexpected geometry type: {}'.format(
            source_geometry.GetGeometryName(),
        ))


class AttributeProcessor(BaseProcessor):
    """ Writes a shapefile with height in z attribute. """
    def process(self, source_geometry, left=True, right=True, distance_override: float = None):
        """
        Return generator of (geometry, height) tuples.
        """
        geometry_type = source_geometry.GetGeometryType()
        if geometry_type in LINESTRINGS:
            source_wkb_line_strings = [source_geometry]
        elif geometry_type in MULTILINESTRINGS:
            source_wkb_line_strings = [line for line in source_geometry]
        else:
            raise ValueError('Unexpected geometry type: {}'.format(
                source_geometry.GetGeometryName(),
            ))
        for source_wkb_line_string in source_wkb_line_strings:
            result = self._calculate(wkb_line_string=source_wkb_line_string, left=left, right=right, distance_override=distance_override)
            weighted_sum_of_heights = 0
            lines = []
            for line, value in zip(result['lines'], result['values']):
                geom = vectors.line2geometry(line)
                lines.append(geom)
                weighted_sum_of_heights += value*geom.Length()
            merged_line = vectors.linemerge(lines)
            weighted_averge_height = weighted_sum_of_heights/merged_line.Length()
            yield [merged_line, weighted_averge_height]
