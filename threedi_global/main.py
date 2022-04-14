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


import gdal
import sqlite3
import geopandas as gpd
import shapely
import requests
from osgeo import ogr
import json
import os
from geomet import wkt
from modules import *
import shutil

dem_uuid =  "eae92c48-cd68-4820-9d82-f86f763b4186"
headers = {
    "username": 'kizje.marif',
    "password": '@Northgo93',
    "Content-Type": "application/json",
}

#%%

def read_geom(area_path: str):
    
    """
    This function reads an shapefile and returns the geomtry
    in WKT format 
    
    Parameters
    ----------
    area_path : str
        The path to shapefile cotaining the project area.

    Returns
    -------
    geom : TYPE
        DESCRIPTION.

    """
    file = ogr.Open(area_path)
    shape = file.GetLayer(0)
    #first feature of the shapefile
    feature = shape.GetFeature(0)
    first = feature.ExportToJson()
    file = eval(first)
    geom_ = file['geometry']
    geom = wkt.dumps(geom_, decimals =4 )
    return geom

def download_rasters(raster: str ,pixelSize: float ,target_extent: str,
                         sourceSrs,targetSrs,headers):
        """Defines a task URL in lizard and prepares the rasters for export. 
        A maximum time of 500 seconds per raster is allowed. The last rule
        of the function calls download_file which actually downloads the 
        rasters
        
        :param raster: uuid of the raster to be downloaden
        :param pixelsize:
        
        """
        createTiffTaskUrl = 'https://demo.lizard.net/api/v3/rasters/{}/data/?async=true&cellsize={}&format=geotiff&geom={}&srs={}&target_srs={}'.format(raster,pixelSize,target_extent,sourceSrs,targetSrs)
        print(createTiffTaskUrl)
        r = requests.get(createTiffTaskUrl, headers=headers).json()
        taskid = r["task_id"]
        progressUrl = r["url"]
        taskStatus = ""
        tiff_download_url = ""
        count = 0
        while taskStatus!= "SUCCESS" and count < 100:
            result = requests.get(progressUrl,headers=headers).json()
            taskStatus = result["task_status"]
            #print(taskStatus)
            if taskStatus=="SUCCESS":
                tiff_download_url = result["result_url"]
                break
                count+=1
                time.sleep(5)
            elif taskStatus!= "SUCCES" and count == 100:
               print('connecion timed out')
        return tiff_download_url


def download_file(url,folder,headers):
    """Downloads rasters from Lizard based on task URL and target folder
    also writes time indication. Sometimes this causes misbehaviour when
    there is a connection problem with Lizard"""

    if not os.path.exists(folder):
        os.makedirs(folder)
    file_name = os.path.join(folder,url.split('/')[-1])
    #file_name = 'new.tif'
    with open(file_name, "wb") as f:
        print('Downloading {}'.format(file_name))
        response = requests.get(url, headers=headers, stream=True)

        total_length = response.headers.get('content-length')

        if total_length is None: # no content length header
            f.write(response.content)
        else:
            dl = 0
            total_length = int(total_length)
            for data in response.iter_content(chunk_size=4096):
                dl += len(data)
                f.write(data)
    return


def create_spatiallite():
    return

def update_spatialite(spatialiteFile):
    """
    This functions takes an empty 3Di model and updates the numerical and global settings
    To do: Check of er nog andere instellingen gedaan moeten worden. 
    """
    #Path to spatialite
    sqlfile2D = os.path.join(dirname, r'fill_2d_settings.sql')
    query = open(sqlfile2D, 'r').read()
    spatialiteFile = r'C:\Users\kizje.marif\Documents\3Di goes global\leeg.sqlite'
    conn = sqlite3.connect(spatialiteFile)
    c = conn.cursor()
    c.executescript(query)
    return




#%%

def main(dir_Home: str, shape_path: str, name_model: str):
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
    dir_model = os.path.join(dir_home, name_model)
    schem_dir = os.path.join(dir_model, "rasters")
    if not os.path.exists(schem_dir):
        os.makedirs(schem_dir)

    # 2. Download raster (Only elevation in this case)
    geom_extent = read_geom(shape_path)
    dem = download_rasters(dem_uuid,pixelSize=10,target_extent=geom_extent),
                         sourceSrs='EPSG:3857',targetSrs='EPSG:3857',headers=headers)
    
    download_file(url=dem,folder=schem_dir,headers=headers)

    #3. Create and update sqlite (3Di model) plus zip the file
    
    spatialiteFile_src = f'{dir_home}\leeg.sqlite'
    spatialiteFile_dst = f'{dir_model}\{name_model}.sqlite'
    shutil.copyfile(spatialiteFile_src, spatialiteFile_dst)
    update_spatialite(spatialiteFile_dst):
    
    #Let op update ook de naam van het raster vo
    
    #4. Make revision and schematisation
    
    
