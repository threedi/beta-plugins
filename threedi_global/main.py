# -*- coding: utf-8 -*-
"""
Created on Fri Apr  8 12:01:52 2022

@author: Kizje.marif; Leendert van Wolfswinkel

Creates a 3Di model for an area defined by a polygon.
"""
from math import sqrt
import requests
import shutil
from typing import Union, Tuple
import time
from pathlib import Path

import sqlite3
from osgeo import ogr
from threedi_api_client.api import ThreediApi

from threedi_api.constants import THREEDI_API_HOST, ORGANISATION_UUID
from threedi_api.upload import upload_and_process

from epsg import utm_zone_epsg_for_polygon

VERSION = "0.1"

SQL_DIR = Path(__file__).parent / "sql"
DATA_DIR = Path(__file__).parent / "data"
SPATIALITE_TEMPLATE_PATH = DATA_DIR / "template.sqlite"
NR_CELLS = 50000


def read_geom(filename: Union[Path, str]) -> Tuple[str, int, int, float]:
    """
    Returns:
        - the geometry in WKT format of the first feature of the first layer of an OGR compatible vector dataset
        - the EPSG code of the layer that was read
        - the EPSG code of the UTM Zone the centroid of the geometry is in
        - area (in units of the input polygon's CRS)
    """
    datasource = ogr.Open(str(filename))
    layer = datasource.GetLayer(0)
    srs = layer.GetSpatialRef()
    if not srs.IsProjected():
        raise ValueError("Input polygon does not have a Projected CRS. Cannot calculate its area in meters.")
    epsg_code = srs.GetAuthorityCode(None)
    layer.ResetReading()
    feature = layer.GetNextFeature()
    geom = feature.GetGeometryRef()
    utm_zone_epsg = utm_zone_epsg_for_polygon(geom=geom, srs=srs)
    geom_wkt = geom.ExportToWkt()
    geom_area = geom.GetArea()
    return geom_wkt, epsg_code, utm_zone_epsg, geom_area


def get_headers(api_key: str):
    return {
        "username": "__key__",
        "password": api_key,
        "Content-Type": "application/json",
    }


def download_rasters(
        raster_uuid: str,
        pixel_size: float,
        extent_wkt: str,
        extent_srs,
        target_srs,
        api_key: str,
        max_attempts=100,
        wait_time=5
):
    """
    Defines a task URL in lizard and prepares the rasters for export.
    A maximum time of `max_attempts`*`wait_time` [s] per raster is allowed.
    """
    create_tiff_task_url = f"https://demo.lizard.net/api/v3/rasters/{raster_uuid}/data/?" \
                           f"async=true&" \
                           f"cellsize={pixel_size}&" \
                           f"format=geotiff&" \
                           f"geom={extent_wkt}&" \
                           f"srs={extent_srs}&" \
                           f"target_srs={target_srs}"
    headers = get_headers(api_key)
    r = requests.get(create_tiff_task_url, headers=headers).json()
    progress_url = r["url"]
    task_status = ""
    tiff_download_url = ""
    attempts = 0
    while task_status != "SUCCESS" and attempts < max_attempts:
        result = requests.get(progress_url, headers=headers).json()
        task_status = result["task_status"]
        if task_status == "SUCCESS":
            tiff_download_url = result["result_url"]
            break
        elif task_status != "SUCCESS" and attempts == max_attempts:
            print('connecion timed out')
        attempts += 1
        time.sleep(wait_time)
    return tiff_download_url


def download_file(url, output_path: Union[Path, str], headers):
    """Downloads rasters from Lizard based on task URL and target folder
    also writes time indication. Sometimes this causes misbehaviour when
    there is a connection problem with Lizard"""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(str(output_path), "wb") as f:
        print(f"Downloading {output_path}")
        response = requests.get(url, headers=headers, stream=True)
        total_length = response.headers.get('content-length')
        if total_length is None:  # no content length header
            f.write(response.content)
        else:
            dl = 0
            for data in response.iter_content(chunk_size=4096):
                dl += len(data)
                f.write(data)
    return


def optimal_grid_space(model_area: float, pixel_size: float, nr_cells: int = 50000):
    # model_area = 1000000
    # pixel_size = 0.25
    # nr_cells = 50.000
    # should return 4.5
    raw_answer = sqrt(model_area/nr_cells)
    double_pixel_size = 2*pixel_size
    multiple_of_double_pixel_size = max(double_pixel_size, double_pixel_size * round(raw_answer/double_pixel_size))
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
        uuid,
        extent_filename: [Path, str],
        pixel_size: float,
        api_key: str
):
    extent_filename = Path(extent_filename)
    geom_extent, extent_epsg_code, utm_zone_epsg, area = read_geom(extent_filename)
    dem_download_url = download_rasters(
        uuid,
        pixel_size=pixel_size,
        extent_wkt=geom_extent,
        extent_srs=f"EPSG:{extent_epsg_code}",
        target_srs=f"EPSG:{utm_zone_epsg}",
        api_key=api_key
    )
    print("Downloading DEM...")
    dem_path = Path(local_dir) / schematisation_name / "rasters" / "dem.tif"
    download_file(url=dem_download_url, output_path=dem_path, headers=get_headers(api_key))


def prepare_spatialite(
        local_dir: [Path, str],
        schematisation_name: str,
        extent_filename: [Path, str],
        pixel_size: float,
        nr_cells
):
    spatialite_dst_path = Path(local_dir) / schematisation_name / f"{schematisation_name}.sqlite"
    shutil.copyfile(SPATIALITE_TEMPLATE_PATH, spatialite_dst_path)
    geom_extent, extent_epsg_code, utm_zone_epsg, area = read_geom(extent_filename)
    grid_space = optimal_grid_space(model_area=area, pixel_size=pixel_size, nr_cells=nr_cells)
    fill_settings(spatialite_dst_path, epsg_code=utm_zone_epsg, grid_space=grid_space)


def create_threedimodel(
        local_dir: Union[Path, str],
        schematisation_name: str,
        extent_filename: Union[Path, str],
        pixel_size,
        nr_cells,
        lizard_api_key: str,
        threedi_api_key: str,
        dem_raster_uuid: str = "eae92c48-cd68-4820-9d82-f86f763b4186"
):
    print(f"Version: {VERSION}")
    config = {
        "THREEDI_API_HOST": THREEDI_API_HOST,
        "THREEDI_API_PERSONAL_API_TOKEN": threedi_api_key
    }
    threedi_api = ThreediApi(config=config, version='v3-beta')

    print("Creating local (temp) folder structure...")
    create_temp_dir(local_dir=local_dir, schematisation_name=schematisation_name)
    print("Requesting DEM download link from Lizard...")
    download_dem(
        local_dir=local_dir,
        schematisation_name=schematisation_name,
        extent_filename=extent_filename,
        pixel_size=pixel_size,
        uuid=dem_raster_uuid,
        api_key=lizard_api_key
    )
    print("Preparing sqlite...")
    prepare_spatialite(
        local_dir=local_dir,
        schematisation_name=schematisation_name,
        extent_filename=extent_filename,
        pixel_size=pixel_size,
        nr_cells=nr_cells
    )
    print("Uploading...")
    threedimodel_id, schematisation_id = upload_and_process(
        threedi_api=threedi_api,
        organisation_uuid=ORGANISATION_UUID,
        schematisation_name=schematisation_name,
        sqlite_path=Path(local_dir) / schematisation_name / f"{schematisation_name}.sqlite",
        raster_names={"dem_file": "dem"}
    )
    print(
        f"Created 3Di Model with ID {threedimodel_id}: https://management.3di.live/schematisations/{schematisation_id}"
    )
