from pathlib import Path
from typing import List

from osgeo import ogr, osr, gdal
from shapely.geometry import LineString
import sqlite3


class TabulatedCrossSection:
    def __init__(self, reference_level: float, bank_level: float, widths: List[float], heights: List[float]):
        pass


class Channel:
    def __init__(self, geometry: LineString, srs: osr.SpatialReference):
        self.geometry = geometry
        self.srs = srs

    @classmethod
    def from_spatialite(cls, spatialite: ogr.DataSource, channel_id):
        pass

    @classmethod
    def from_geopackage(cls, geopackage: ogr.DataSource, channel_id):
        pass

    def add_cross_section(self, cross_section):
        pass

    def as_raster(self) -> gdal.Dataset:
        pass



