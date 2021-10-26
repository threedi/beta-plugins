# (c) Nelen & Schuurmans, see LICENSE.rst.
# -*- coding: utf-8 -*-

import logging

from osgeo import gdal
from osgeo import gdal_array
from osgeo import ogr
from osgeo import osr
import numpy as np

import datasets
import utils

logger = logging.getLogger(__name__)


class Meta(object):
    def __init__(self, dataset):
        band = dataset.GetRasterBand(1)
        data_type = band.DataType
        numpy_type = gdal_array.GDALTypeCodeToNumericTypeCode(data_type)

        # compared
        self.width = dataset.RasterXSize
        self.height = dataset.RasterYSize
        self.data_type = data_type
        self.projection = dataset.GetProjection()
        self.geo_transform = dataset.GetGeoTransform()

        # not compared
        self.dtype = np.dtype(numpy_type)
        no_data_value = band.GetNoDataValue()
        self.no_data_value = numpy_type(no_data_value)

    def __eq__(self, other):
        return (self.width == other.width
                and self.height == other.height
                and self.data_type == other.data_type
                and self.projection == other.projection
                and self.geo_transform == other.geo_transform)


class Group(object):
    """
    A group of gdal rasters, automatically merges, and has a more pythonic
    interface.
    """
    def __init__(self, *datasets):
        metas = [Meta(dataset) for dataset in datasets]
        meta = metas[0]
        if not all([meta == m for m in metas]):
            raise ValueError('Incompatible rasters.')

        self.dtype = meta.dtype
        self.width = meta.width
        self.height = meta.height
        self.projection = meta.projection
        self.no_data_value = meta.no_data_value
        self.geo_transform = utils.GeoTransform(meta.geo_transform)

        self.no_data_values = [m.no_data_value for m in metas]
        self.datasets = datasets

    def read(self, bounds, inflate=False):
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
            x1, y1, x2, y2 = self.geo_transform.get_indices(bounds,
                                                            inflate=inflate)
        else:
            x1, y1, x2, y2 = bounds

        # overlapping bounds
        w, h = self.width, self.height
        p1 = min(w, max(0, x1))
        q1 = min(h, max(0, y1))
        p2 = min(w, max(0, x2))
        q2 = min(h, max(0, y2))

        # result array plus a view for what's actually inside datasets
        array = np.full((y2 - y1, x2 - x1), self.no_data_value, self.dtype)
        view = array[q1 - y1: q2 - y1, p1 - x1: p2 - x1]

        kwargs = {'xoff': p1, 'yoff': q1, 'xsize': p2 - p1, 'ysize': q2 - q1}
        for dataset, no_data_value in zip(self.datasets, self.no_data_values):
            data = dataset.ReadAsArray(**kwargs)
            index = data != no_data_value
            view[index] = data[index]

        return array


class RGBWrapper(object):
    """
    A wrapper around GDAL RGB datasets for pythonic querying.
    """
    def __init__(self, dataset):
        self.dataset = dataset

        self.width = dataset.RasterXSize
        self.height = dataset.RasterYSize
        self.projection = dataset.GetProjection()
        self.geo_transform = utils.GeoTransform(dataset.GetGeoTransform())

    def get_mask(self, geometry, shape):

        # create an ogr datasource
        driver = ogr.GetDriverByName('Memory')
        source = driver.CreateDataSource('')
        sr = osr.SpatialReference(self.projection)
        layer = source.CreateLayer('', sr)
        defn = layer.GetLayerDefn()
        feature = ogr.Feature(defn)
        feature.SetGeometry(geometry)
        layer.CreateFeature(feature)

        # burn where data should be
        mask = np.zeros(shape, dtype='u1')
        geo_transform = self.geo_transform.shifted(geometry)
        kwargs = {'geo_transform': geo_transform,
                  'projection': self.projection}
        with datasets.Dataset(mask, **kwargs) as dataset:
            gdal.RasterizeLayer(dataset, (1,), layer, burn_values=(1,))

        return mask.astype('b1').repeat(3, axis=0)

    def read(self, geometry):
        """
        Return numpy array.

        bounds: x1, y1, x2, y2 pixel window specifcation, or an ogr geometry

        If the bounds fall outside the dataset, the result is padded
        with no data values.
        """
        # find indices
        x1, y1, x2, y2 = self.geo_transform.get_indices(geometry)

        # overlapping bounds
        w, h = self.width, self.height
        p1 = min(w, max(0, x1))
        q1 = min(h, max(0, y1))
        p2 = min(w, max(0, x2))
        q2 = min(h, max(0, y2))

        # result array plus a view for what's actually inside datasets
        data = np.full((3, y2 - y1, x2 - x1), 0, 'u1')
        view = data[:, q1 - y1: q2 - y1, p1 - x1: p2 - x1]

        # query the data and put it in the view
        kwargs = {'xoff': p1, 'yoff': q1, 'xsize': p2 - p1, 'ysize': q2 - q1}
        view[:] = self.dataset.ReadAsArray(**kwargs)

        # create a mask
        shape = (1,) + data.shape[1:]
        mask = self.get_mask(geometry=geometry, shape=shape)

        return data, mask
