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

DEM_UUID = "eae92c48-cd68-4820-9d82-f86f763b4186"
HEADERS = {
    "username": "__key__",
    "password": get_login_details(section="lizard", option="api_key"),
    "Content-Type": "application/json",
}
SQL_DIR = Path(__file__).parent / "sql"
DATA_DIR = Path(__file__).parent / "data"
SPATIALITE_TEMPLATE_PATH = DATA_DIR / "leeg.sqlite"


def read_geom(filename: Union[Path, str]) -> Tuple[str, int, int]:
    """
    Returns:
        - the geometry in WKT format of the first feature of the first layer of an OGR compatible vector dataset
        - the EPSG code of the layer that was read
        - the EPSG code of the UTM Zone the centroid of the geometry is in
    """
    datasource = ogr.Open(str(filename))
    layer = datasource.GetLayer(0)
    srs = layer.GetSpatialRef()
    epsg_code = srs.GetAuthorityCode(None)
    feature = layer.GetFeature(0)
    geom = feature.GetGeometryRef()
    utm_zone_epsg = utm_zone_epsg_for_polygon(geom=geom, srs=srs)
    geom_wkt = geom.ExportToWkt()
    return geom_wkt, epsg_code, utm_zone_epsg


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


def fill_settings(sqlite_filename, epsg_code):
    """
    This functions takes an empty 3Di spatialite and updates the numerical and global settings
    #TODO: Check of er nog andere instellingen gedaan moeten worden.
    """
    # Path to spatialite
    sql_fn = str(SQL_DIR / 'fill_2d_settings.sql')
    with open(sql_fn, 'r') as sql_file:
        query = sql_file.read()
        formatted_query = query.format(epsg_code=epsg_code)
    conn = sqlite3.connect(sqlite_filename)
    c = conn.cursor()
    c.executescript(formatted_query)
    return


def create_threedimodel(
        local_dir: Union[Path, str],
        extent_filename: Union[Path, str],
        name_model: str,
        pixel_size
):
    """
    This function is the main framework to create a 2D 3Di model
    This is done by excecuting the following steps
    
    1. Create folder structure
        folder 
        rasters
    
    2. Download files
    3. Create and update sqlite
    4. Upload to 3Di via schematisation etc

    """

    # 1. Create folder structue
    print("Creating local (temp) folder structure...")
    local_dir = Path(local_dir)
    extent_filename = Path(extent_filename)
    schematisation_dir = local_dir / name_model
    rasters_dir = schematisation_dir / "rasters"
    rasters_dir.mkdir(parents=True, exist_ok=True)

    # 2. Download raster (Only DEM in this case)
    print("Requesting DEM download link from Lizard...")
    geom_extent, extent_epsg_code, utm_zone_epsg = read_geom(extent_filename)
    dem_download_url = download_rasters(
        DEM_UUID,
        pixel_size=pixel_size,
        extent_wkt=geom_extent,
        extent_srs=f"EPSG:{extent_epsg_code}",
        target_srs=f"EPSG:{utm_zone_epsg}",
        headers=HEADERS
    )
    print("Downloading DEM...")
    dem_path = rasters_dir / "dem.tif"
    download_file(url=dem_download_url, output_path=dem_path, headers=HEADERS)

    # 3. Create and update sqlite (3Di model) plus zip the file
    print("Creating Sqlite...")
    spatialite_dst_path = schematisation_dir / f"{name_model}.sqlite"
    shutil.copyfile(SPATIALITE_TEMPLATE_PATH, spatialite_dst_path)
    fill_settings(spatialite_dst_path, utm_zone_epsg)

    # 4. Make revision and schematisation
    print("Create schematisation revision...")
    raster_names = {"dem_file": "dem"}
    tags = ["W0176", "Global", "demomodel"]
    schematisation_name = name_model
    threedimodel_id, schematisation_id = upload_and_process(
        schematisation_name=schematisation_name,
        sqlite_path=spatialite_dst_path,
        raster_names=raster_names,
        schematisation_create_tags=tags
    )
    print(f"Created 3Di Model with ID {threedimodel_id}: https://management.3di.live/schematisations/{schematisation_id}")
