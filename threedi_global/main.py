# -*- coding: utf-8 -*-
"""
Created on Fri Apr  8 12:01:52 2022

Tooltje Ivar: https://github.com/threedi/beta-plugins/tree/master/build2dmodel (World DEM ipv AHN, nieuwste spatialite)
Citybuilder (downloaden uitsnede raster obv polygoon): https://github.com/nens/citybuilder_plugin
Aanmaken schematisation & revision & threedimodel: G:\Projecten W (2021)\W0273 - Klimaatstresstesten en kansen Provinciale infrastructuur Utrecht\Gegevens\Bewerking\Scripts\01. 3Di\05. Simulatie

@author: Kizje.marif

This script creates a 3Di model for an area defined by a polygon.


Step 1: Define area by polygon
Step 2: Download required data
Step 3: Make tables
Step 4: Create and upload sqlite
    
"""
from math import sqrt
from typing import Union, Tuple
import time
from pathlib import Path

import sqlite3
import requests
from osgeo import ogr
import shutil
from threedi_api.upload import upload_and_process
from login import get_login_details
from epsg import utm_zone_epsg_for_polygon

HEADERS = {
    "username": "__key__",
    "password": get_login_details(section="lizard", option="api_key"),
    "Content-Type": "application/json",
}
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
    feature = layer.GetFeature(0)
    geom = feature.GetGeometryRef()
    utm_zone_epsg = utm_zone_epsg_for_polygon(geom=geom, srs=srs)
    geom_wkt = geom.ExportToWkt()
    geom_area = geom.GetArea()
    return geom_wkt, epsg_code, utm_zone_epsg, geom_area


def download_rasters(
        raster_uuid: str,
        pixel_size: float,
        extent_wkt: str,
        extent_srs,
        target_srs,
        headers,
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
    print(create_tiff_task_url)
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
            total_length = int(total_length)
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
    conn = sqlite3.connect(sqlite_filename)
    c = conn.cursor()
    sql = """UPDATE v2_global_settings SET epsg_code = {epsg_code}, grid_space = {grid_space};"""
    c.execute(sql)
    return


def create_temp_dir(local_dir: [Path, str], schematisation_name: str):
    local_dir = Path(local_dir)
    schematisation_dir = local_dir / schematisation_name
    rasters_dir = schematisation_dir / "rasters"
    rasters_dir.mkdir(parents=True, exist_ok=True)


def download_dem(local_dir: [Path, str], schematisation_name: str, uuid, extent_filename: [Path, str], pixel_size):
    extent_filename = Path(extent_filename)
    geom_extent, extent_epsg_code, utm_zone_epsg, area = read_geom(extent_filename)
    dem_download_url = download_rasters(
        uuid,
        pixel_size=pixel_size,
        extent_wkt=geom_extent,
        extent_srs=f"EPSG:{extent_epsg_code}",
        target_srs=f"EPSG:{utm_zone_epsg}",
        headers=HEADERS
    )
    print("Downloading DEM...")
    dem_path = Path(local_dir) / schematisation_name / "rasters" / "dem.tif"
    download_file(url=dem_download_url, output_path=dem_path, headers=HEADERS)


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
        dem_raster_uuid: str = "eae92c48-cd68-4820-9d82-f86f763b4186"
):
    print("Creating local (temp) folder structure...")
    create_temp_dir(local_dir=local_dir, schematisation_name=schematisation_name)
    print("Requesting DEM download link from Lizard...")
    download_dem(
        local_dir=local_dir,
        schematisation_name=schematisation_name,
        extent_filename=extent_filename,
        pixel_size=pixel_size,
        uuid=dem_raster_uuid
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
        schematisation_name=schematisation_name,
        sqlite_path=Path(local_dir) / schematisation_name / f"{schematisation_name}.sqlite",
        raster_names={"dem_file": "dem"}
    )
    print(f"Created 3Di Model with ID {threedimodel_id}: https://management.3di.live/schematisations/{schematisation_id}")
