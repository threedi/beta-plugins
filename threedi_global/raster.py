from pathlib import Path
from shutil import copyfile

from osgeo import gdal
from osgeo import ogr
from osgeo import gdalconst


gdal.UseExceptions()
ogr.UseExceptions()


def clip(raster: gdal.Dataset, vector: gdal.Dataset, layer_name: str = None):
    source_band = raster.GetRasterBand(1)
    nodatavalue = source_band.GetNoDataValue()
    if vector.GetLayerCount() > 1:
        if not layer_name:
            raise ValueError(
                "Vector dataset has more than 1 layer, but layer_name is not provided"
            )
        options = gdal.RasterizeOptions(
            layers=layer_name,
            bands=[1],
            burnValues=[nodatavalue],
            inverse=True,
        )
    else:
        options = gdal.RasterizeOptions(
            bands=[1],
            burnValues=[nodatavalue],
            inverse=True
        )
    gdal.Rasterize(raster, srcDS=vector, options=options)


if __name__ == "__main__":
    raster_original_fn = (
        Path(__file__).parent / "test" / "data" / "test_raster_original.tif"
    )
    raster_fn = Path(__file__).parent / "test" / "data" / "test_raster.tif"
    copyfile(raster_original_fn, raster_fn)
    vector_fn = Path(__file__).parent / "test" / "data" / "aoi.shp"
    raster = gdal.Open(str(raster_fn), gdal.GA_Update)
    vector = gdal.OpenEx(str(vector_fn), gdalconst.OF_VECTOR)
    layer = vector.GetLayer(0)
    clip(raster, vector)
