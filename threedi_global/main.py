# -*- coding: utf-8 -*-
"""
Created on Fri Apr  8 12:01:52 2022

@author: Kizje.marif; Leendert van Wolfswinkel

Creates a 3Di model for an area defined by a polygon.
"""
from math import sqrt
import shutil
from typing import Union, List
from pathlib import Path
import numpy as np
import sqlite3
from osgeo import gdal, ogr
from threedi_api_client.api import ThreediApi

from epsg import find_utm_zone_epsg, xy_to_wgs84_lat_lon, transform_bounding_box, transform_layer
from lizard import download_raster
from raster import clip
from threedi_api.constants import THREEDI_API_HOST, ORGANISATION_UUID
from threedi_api.upload import upload_and_process


gdal.UseExceptions()
ogr.UseExceptions()


VERSION = "0.2"

SQL_DIR = Path(__file__).parent / "sql"
DATA_DIR = Path(__file__).parent / "data"
SPATIALITE_TEMPLATE_PATH = DATA_DIR / "template.sqlite"
NR_CELLS = 50000
MEMORY_DRIVER = ogr.GetDriverByName("Memory")
GEOPACKAGE_DRIVER = ogr.GetDriverByName("GPKG")


def utm_zone_from_layer(layer: ogr.Layer) -> int:
    minx, maxx, miny, maxy = layer.GetExtent()
    srs = layer.GetSpatialRef()
    if layer.GetSpatialRef().GetAuthorityCode(None) != '4326':
        lat, lon = xy_to_wgs84_lat_lon(x=minx + maxx / 2, y=miny + maxy / 2, srs=srs)
        utm_zone_epsg = find_utm_zone_epsg(latitude=lat, longitude=lon)
    else:
        lon = np.mean([minx, maxx]); lat = np.mean([miny, maxy])
        utm_zone_epsg = find_utm_zone_epsg(latitude=lat, longitude=lon)
    return utm_zone_epsg


def estimate_area(layer: ogr.Layer) -> float:
    """
    Returns the sum of the area of all polygons in the layer (in units of the input polygon's CRS)
    """
    layer.ResetReading()
    area = 0
    for feature in layer:
        geom = feature.GetGeometryRef()
        area += geom.GetArea()
    return area


def optimal_grid_space(model_area: float, pixel_size: float, nr_cells: int = 50000):
    # model_area = 1000000
    # pixel_size = 0.25
    # nr_cells = 50.000
    # should return 4.5
    raw_answer = sqrt(model_area / nr_cells)
    double_pixel_size = 2 * pixel_size
    multiple_of_double_pixel_size = max(
        double_pixel_size, double_pixel_size * round(raw_answer / double_pixel_size)
    )
    return multiple_of_double_pixel_size


def fill_settings(sqlite_filename, epsg_code, grid_space):
    """
    This functions takes an empty 3Di spatialite and updates the numerical and global settings
    """
    # Path to spatialite
    print(f"grid_space: {grid_space}")
    print(f"epsg_code: {epsg_code}")
    conn = sqlite3.connect(sqlite_filename)
    c = conn.cursor()
    sql = f"""UPDATE v2_global_settings SET epsg_code = {epsg_code}, grid_space = {grid_space};"""
    c.execute(sql)
    conn.commit()
    return


def create_temp_dir(local_dir: [Path, str], schematisation_name: str):
    local_dir = Path(local_dir)
    schematisation_dir = local_dir / schematisation_name
    rasters_dir = schematisation_dir / "rasters"
    rasters_dir.mkdir(parents=True, exist_ok=True)


def download_dem(
    local_dir: [Path, str],
    schematisation_name: str,
    uuid: str,
    extent_filename: [Path, str],
    pixel_size: float,
    api_key: str,
    extent_layer_name: str = None,
):
    extent_filename = str(extent_filename)
    extent_datasource = ogr.Open(extent_filename)
    if not extent_datasource:
        raise FileNotFoundError(
            f"Could not open {extent_filename}. The file does not exists or is not an OGR-compatible vector file"
    )
    extent_layer = (
        extent_datasource.GetLayerByName(extent_layer_name)
        if extent_layer_name
        else extent_datasource.GetLayer(0)
    )
    src_epsg_code = extent_layer.GetSpatialRef().GetAuthorityCode(None)
    utm_zone_epsg = utm_zone_from_layer(layer=extent_layer)
    vsi_filename = "/vsimem/extent_datasource_transformed.gpkg"
    extent_datasource_transformed = GEOPACKAGE_DRIVER.CreateDataSource(vsi_filename)
    transform_layer(
        layer=extent_layer,
        dest_datasource=extent_datasource_transformed,
        dest_layer_name=extent_layer_name or "",
        source_epsg=src_epsg_code,
        dest_epsg=utm_zone_epsg
    )
    extent_datasource_transformed.FlushCache()
    extent_layer_transformed = extent_datasource_transformed.GetLayer(0)
    minx, maxx, miny, maxy = extent_layer_transformed.GetExtent()
    if src_epsg_code != '4326':
        bounding_box = [minx, miny, maxx, maxy]  # Lizard API bounding box sequence differs from ogr GetExtent() sequence
    else:
        bounding_box = [miny, minx, maxy, maxx]  # Lizard API bounding box sequence differs from ogr GetExtent() sequence
    dem_path = Path(local_dir) / schematisation_name / "rasters" / "dem.tif"
    download_raster(
        api_key=api_key,
        raster_uuid=uuid,
        bounding_box=bounding_box,
        epsg_code=utm_zone_epsg,
        pixel_size=pixel_size,
        nodata=-9999,
        output_path=dem_path,
    )
    raster = gdal.Open(str(dem_path), gdal.GA_Update)
    extent_dataset_transformed = gdal.OpenEx(vsi_filename)
    clip(raster=raster, vector=extent_dataset_transformed, layer_name=extent_layer_name)
    gdal.Unlink(vsi_filename)


def prepare_spatialite(
    local_dir: [Path, str],
    schematisation_name: str,
    extent_filename: [Path, str],
    pixel_size: float,
    nr_cells: int,
    extent_layer_name: str = None,
):
    spatialite_dst_path = (
        Path(local_dir) / schematisation_name / f"{schematisation_name}.sqlite"
    )
    shutil.copyfile(SPATIALITE_TEMPLATE_PATH, spatialite_dst_path)

    extent_datasource = ogr.Open(extent_filename)
    extent_layer = (
        extent_datasource.GetLayerByName(extent_layer_name)
        if extent_layer_name
        else extent_datasource.GetLayer(0)
    )
    area = estimate_area(layer=extent_layer)
    grid_space = optimal_grid_space(
        model_area=area, pixel_size=pixel_size, nr_cells=nr_cells
    )

    utm_zone_epsg = utm_zone_from_layer(layer=extent_layer)

    fill_settings(spatialite_dst_path, epsg_code=utm_zone_epsg, grid_space=grid_space)


def create_threedimodel(
    local_dir: Union[Path, str],
    schematisation_name: str,
    extent_filename: Union[Path, str],
    pixel_size,
    nr_cells,
    lizard_api_key: str,
    threedi_api_key: str,
    organisation_uuid: str,
    extent_layer_name: str = None,
    dem_raster_uuid: str = "eae92c48-cd68-4820-9d82-f86f763b4186",
):
    print(f"Version: {VERSION}")
    config = {
        "THREEDI_API_HOST": THREEDI_API_HOST,
        "THREEDI_API_PERSONAL_API_TOKEN": threedi_api_key,
    }
    threedi_api = ThreediApi(config=config, version="v3-beta")

    print("Creating local (temp) folder structure...")
    create_temp_dir(local_dir=local_dir, schematisation_name=schematisation_name)
    print("Downloading DEM...")
    download_dem(
        local_dir=local_dir,
        schematisation_name=schematisation_name,
        extent_filename=extent_filename,
        extent_layer_name=extent_layer_name,
        pixel_size=pixel_size,
        uuid=dem_raster_uuid,
        api_key=lizard_api_key,
    )
    print("Preparing sqlite...")
    prepare_spatialite(
        local_dir=local_dir,
        schematisation_name=schematisation_name,
        extent_filename=extent_filename,
        extent_layer_name=extent_layer_name,
        pixel_size=pixel_size,
        nr_cells=nr_cells,
    )
    print("Uploading...")
    threedimodel_id, schematisation_id = upload_and_process(
        threedi_api=threedi_api,
        organisation_uuid=organisation_uuid,
        schematisation_name=schematisation_name,
        sqlite_path=Path(local_dir)
        / schematisation_name
        / f"{schematisation_name}.sqlite",
        raster_names={"dem_file": "dem"},
    )
    print(
        f"Created 3Di Model with ID {threedimodel_id}: https://management.3di.live/schematisations/{schematisation_id}"
    )
