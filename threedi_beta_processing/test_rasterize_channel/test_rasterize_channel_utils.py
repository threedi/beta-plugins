from pathlib import Path

from osgeo import gdal

try:
    from rasterize_channel_utils import merge_rasters
except ImportError:
    from threedi_beta_processing.rasterize_channel_utils import merge_rasters

TEST_DATA_DIR = Path(__file__).parent


def test_merge_rasters():
    rasters = [gdal.Open(str(TEST_DATA_DIR / f"raster{i}.tif")) for i in range(1,5)]
    output_filename = TEST_DATA_DIR / 'merged.tif'
    print(f"output_filename: {output_filename}")
    merge_rasters(
        rasters,
        tile_size=50,
        aggregation_method='min',
        output_filename=output_filename
    )


test_merge_rasters()