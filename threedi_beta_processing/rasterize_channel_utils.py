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
    decimals: int = 5,
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
    x0, y0 = (
        round(val, decimals)
        for val in gdal.ApplyGeoTransform(inv_gt, float(bbox[0]), float(bbox[1]))
    )
    x1, y1 = (
        round(val, decimals)
        for val in gdal.ApplyGeoTransform(inv_gt, float(bbox[2]), float(bbox[3]))
    )
    xmin, ymin = min(x0, x1), min(y0, y1)
    xmax, ymax = max(x0, x1), max(y0, y1)
    if xmin > raster.RasterXSize or ymin > raster.RasterYSize or xmax < 0 or ymax < 0:
        raise ValueError("bbox does not intersect with raster")

    intersection_xmin, intersection_ymin = max(xmin, 0), max(ymin, 0)
    intersection_xmax, intersection_ymax = min(xmax, raster.RasterXSize), min(
        ymax, raster.RasterYSize
    )
    arr = band.ReadAsArray(
        int(round(intersection_xmin)),
        int(round(intersection_ymin)),
        int(round(intersection_xmax - intersection_xmin)),
        int(round(intersection_ymax - intersection_ymin)),
    )
    if pad:
        ndv = band.GetNoDataValue()
        arr_pad = np.pad(
            arr,
            (
                (int(round(intersection_ymin - ymin)), int(round(ymax - intersection_ymax))),
                (int(round(intersection_xmin - xmin)), int(round(xmax - intersection_xmax))),
            ),
            "constant",
            constant_values=((ndv, ndv), (ndv, ndv)),
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
    dataset_creation_options=["COMPRESS=DEFLATE"],
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


def tile_aggregate(
    rasters: List[gdal.Dataset],
    bbox: Tuple[float, float, float, float],
    aggregation_method: str,
    output_nodatavalue: float,
) -> np.array:
    assert len(rasters) > 0
    methods = {"min": np.nanmin, "max": np.nanmax}
    method = methods[aggregation_method]
    arrays = []
    for raster in rasters:
        raster_array = read_as_array(raster=raster, bbox=bbox, pad=True)
        ndv = raster.GetRasterBand(1).GetNoDataValue()
        raster_array[raster_array == ndv] = np.nan
        arrays.append(raster_array)
    result = method(np.array(arrays), axis=0)
    result[np.isnan(result)] = output_nodatavalue
    return result


def merge_rasters(
    rasters: List[gdal.Dataset],
    tile_size: int,
    aggregation_method: str,
    output_filename: Path,
    output_pixel_size: float,
    output_nodatavalue: float,
    feedback=None,
):
    """Assumes that all input rasters have the same SRS, resolution, skew, and pixels are
    aligned (as in gdal.Warp's targetAlignedPixels)

    tile_size in pixels
    """
    # resample rasters if their pixel size is different from output_pixel_size (tiny difference is allowed)
    resampled_rasters = []
    for i, raster in enumerate(rasters):
        # GeoTransform: (ulx, xres, xskew, uly, yskew, yres)
        _, xres, _, _, _, yres = raster.GetGeoTransform()
        if abs(abs(xres) - abs(output_pixel_size)) > 1/(1000*tile_size) or \
                abs(abs(yres) - abs(output_pixel_size)) > 1/(1000*tile_size):
            print("Resampling...")
            resampled_raster_file_name = f"/vsimem/resampled_raster_{i}.tif"
            options = gdal.WarpOptions(xRes=output_pixel_size, yRes=output_pixel_size, resampleAlg="near")
            resampled_raster = gdal.Warp(resampled_raster_file_name, raster, options=options)
            resampled_rasters.append(resampled_raster)
        else:
            resampled_rasters.append(raster)
    bboxes = [bounding_box(raster) for raster in resampled_rasters]
    minx, miny, maxx, maxy = MultiPolygon(bboxes).bounds
    ncols = int(np.ceil(((maxx - minx) / abs(output_pixel_size)) / tile_size))
    nrows = int(np.ceil(((maxy - miny) / abs(output_pixel_size)) / tile_size))
    ntiles = ncols * nrows
    geo_tile_size_x = tile_size * abs(output_pixel_size)
    geo_tile_size_y = tile_size * abs(output_pixel_size)
    rows = []
    for tile_row in range(nrows):
        # print(f"tile_row: {tile_row}")
        tiles = []
        tile_maxy = maxy - tile_row * geo_tile_size_y
        for tile_col in range(ncols):
            # print(f"    tile_col: {tile_col}")
            tile_minx = minx + tile_col * geo_tile_size_x
            tile_polygon = box(
                tile_minx,
                tile_maxy - geo_tile_size_y,
                tile_minx + geo_tile_size_x,
                tile_maxy,
            )
            # print(f"    tile_polygon.bounds: {tile_polygon.bounds}")
            intersecting_rasters = [
                raster
                for i, raster in enumerate(resampled_rasters)
                if tile_polygon.intersects(bboxes[i])
            ]
            if len(intersecting_rasters) == 0:
                tile = np.full((tile_size, tile_size), output_nodatavalue)
            else:
                tile = tile_aggregate(
                    rasters=intersecting_rasters,
                    bbox=tile_polygon.bounds,
                    aggregation_method=aggregation_method,
                    output_nodatavalue=output_nodatavalue,
                )
            tiles.append(tile)
            # print(f"    tile.shape: {tile.shape}")
            if feedback:
                feedback.setProgress((tile_row * ncols + tile_col + 1) / ntiles * 100)
        row = np.hstack(tiles)
        rows.append(row)
    result_array = np.vstack(rows)

    # GeoTransform: (ulx, xres, xskew, uly, yskew, yres)
    _, _, xskew, _, yskew, _ = resampled_rasters[0].GetGeoTransform()
    geotransform = (minx, output_pixel_size, xskew, maxy, yskew, -1*output_pixel_size)
    srs = resampled_rasters[0].GetProjection()
    write_raster(
        output_filename=output_filename,
        geotransform=geotransform,
        srs=srs,
        data=result_array,
    )
    for i, raster in enumerate(rasters):
        try:
            gdal.Unlink(f"/vsimem/resampled_raster_{i}.tif")
        except RuntimeError:
            # VSI file does not exist
            continue
