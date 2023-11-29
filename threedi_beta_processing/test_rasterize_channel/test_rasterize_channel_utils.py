from pathlib import Path

from osgeo import gdal

from ..rasterize_channel_utils import merge_rasters


TEST_DATA_DIR = Path(__file__).parent


def test_merge_rasters():
    rasters = [gdal.Open(str(TEST_DATA_DIR / f"raster{i}.tif")) for i in range(1, 5)]
    output_filename = TEST_DATA_DIR / "merged.tif"
    merge_rasters(
        rasters,
        tile_size=50,
        aggregation_method="min",
        output_filename=output_filename,
        output_nodatavalue=-9999,
    )


# def test_align_extent():
#     assert align_extent((10.3, 99.8, 20.3, 199.8), xres=0.5, yres=0.5) == (10.0, 99.5, 20.5, 200.0)

test_merge_rasters()
# test_align_extent()
