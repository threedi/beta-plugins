from pathlib import Path
from typing import Union, List, Tuple

from osgeo import gdal, osr
import numpy as np
from shapely.geometry import MultiPolygon, Polygon, box


def read_as_array(
        raster: gdal.Dataset,
        bbox: Union[List, Tuple],
        band_nr: int = 1,
        pad: bool = False,
        decimals: int = 5
) -> np.ndarray:
    """
    Read part of raster that intersects with bounding box in geo coordinates as array
    :param band_nr: band number
    :param raster: input raster dataset
    :param bbox: Bounding box corner coordinates in the input rasters crs: [x0, y0, x1, y1]
    :param pad: pad with nodata value if partially out of extent. alternatively, return only the part of input raster
    that intersects with the bbox
    :param decimals: precision for deciding which pixels are within bounding box

    """
    band = raster.GetRasterBand(band_nr)
    gt = raster.GetGeoTransform()
    inv_gt = gdal.InvGeoTransform(gt)
    x0, y0 = (round(val, decimals) for val in gdal.ApplyGeoTransform(inv_gt, float(bbox[0]), float(bbox[1])))
    x1, y1 = (round(val, decimals) for val in gdal.ApplyGeoTransform(inv_gt, float(bbox[2]), float(bbox[3])))
    xmin, ymin = min(x0, x1), min(y0, y1)
    xmax, ymax = max(x0, x1), max(y0, y1)
    if xmin > raster.RasterXSize or ymin > raster.RasterYSize or xmax < 0 or ymax < 0:
        raise ValueError('bbox does not intersect with raster')

    intersection_xmin, intersection_ymin = max(xmin, 0), max(ymin, 0)
    intersection_xmax, intersection_ymax = min(xmax, raster.RasterXSize), min(ymax, raster.RasterYSize)
    arr = band.ReadAsArray(
        int(intersection_xmin),
        int(intersection_ymin),
        int(intersection_xmax - intersection_xmin),
        int(intersection_ymax - intersection_ymin)
    )
    if pad:
        ndv = band.GetNoDataValue()
        arr_pad = np.pad(
            arr,
            ((int(intersection_ymin - ymin), int(ymax - intersection_ymax)),
             (int(intersection_xmin - xmin), int(xmax - intersection_xmax))),
            'constant',
            constant_values=((ndv, ndv), (ndv, ndv))
        )
        return arr_pad
    else:
        return arr


def write_raster(
        output_filename: Path,
        geotransform: Tuple,
        srs: osr.SpatialReference,
        data: np.array,
        output_format="GTiff",
        datatype=gdal.GDT_Float32,
        nodatavalue=-9999,
        dataset_creation_options=["COMPRESS=DEFLATE"]
):
    """
    write a numpy array to a gdal raster
    """
    (y, x) = data.shape
    driver = gdal.GetDriverByName(output_format)
    dst_ds = driver.Create(
        str(output_filename),
        xsize=x,
        ysize=y,
        bands=1,
        eType=datatype,
        options=dataset_creation_options,
    )
    dst_ds.GetRasterBand(1).WriteArray(data)
    dst_ds.SetGeoTransform(geotransform)
    dst_ds.SetProjection(srs)
    dst_ds.GetRasterBand(1).SetNoDataValue(nodatavalue)
    return


def bounding_box(raster: gdal.Dataset) -> Polygon:
    ulx, xres, xskew, uly, yskew, yres = raster.GetGeoTransform()
    lrx = ulx + (raster.RasterXSize * xres)
    lry = uly + (raster.RasterYSize * yres)
    return box(lrx, lry, ulx, uly)


def tile_aggregate(rasters: List[gdal.Dataset], bbox: Tuple[float, float, float, float],
                   aggregation_method: str) -> np.array:
    assert len(rasters) > 0
    methods = {
        'min': np.nanmin,
        'max': np.nanmax
    }
    method = methods[aggregation_method]
    arrays = [read_as_array(raster=raster, bbox=bbox, pad=True) for raster in rasters]
    result = method(np.array(arrays), axis=0)
    return result


def merge_rasters(rasters: List[gdal.Dataset], tile_size: int, aggregation_method: str, output_filename: Path):
    """Assumes that all input rasters have the same SRS, resolution, skew, and pixels are
    aligned (as in gdal.Warp's targetAlignedPixels)

    tile_size in pixels
    """
    # GeoTransform: (ulx, xres, xskew, uly, yskew, yres)
    ulx, xres, xskew, uly, yskew, yres = rasters[0].GetGeoTransform()
    nodatavalue = rasters[0].GetRasterBand(1).GetNoDataValue()
    bboxes = [bounding_box(raster) for raster in rasters]
    minx, miny, maxx, maxy = MultiPolygon(bboxes).bounds
    ncols = int(np.ceil((maxx - minx) / tile_size))
    nrows = int(np.ceil((maxy - miny) / tile_size))
    geo_tile_size_x = (tile_size * abs(xres))
    geo_tile_size_y = (tile_size * abs(yres))
    rows = []
    for tile_row in range(nrows):
        print(f"tile_row: {tile_row}")
        tiles = []
        tile_miny = miny + tile_row * geo_tile_size_y
        for tile_col in range(ncols):
            print(f"    tile_col: {tile_col}")
            tile_minx = minx + tile_col * geo_tile_size_x
            tile_polygon = box(
                tile_minx,
                tile_miny,
                tile_minx + geo_tile_size_x,
                tile_miny + geo_tile_size_y
            )
            print(f"    tile_polygon.bounds: {tile_polygon.bounds}")
            intersecting_rasters = [raster for i, raster in enumerate(rasters) if tile_polygon.intersects(bboxes[i])]
            if len(intersecting_rasters) == 0:
                tile = np.full((tile_size, tile_size), nodatavalue)
            else:
                tile = tile_aggregate(
                    rasters=intersecting_rasters,
                    bbox=tile_polygon.bounds,
                    aggregation_method=aggregation_method
                )
            tiles.append(tile)
            print(f"    tile.shape: {tile.shape}")
        row = np.hstack(tiles)
        rows.append(row)
    result_array = np.vstack(rows)

    geotransform = (minx, xres, xskew, maxy, yskew, yres)
    srs = rasters[0].GetProjection()
    write_raster(
        output_filename=output_filename,
        geotransform=geotransform,
        srs=srs,
        data=result_array
    )

