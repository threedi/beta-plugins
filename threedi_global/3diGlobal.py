# -*- coding: utf-8 -*-
"""
Created on Tue Jan 24 13:52:30 2023

@author: joost.vandijk

3Di Global is a service from Nelen & Schuurmans to automatically generate hydrodynamic 2D models.
This service (available on https://3diwatermanagement.com/global) allows organizations to almost 
instantly request and generate a hydrodynamic 2D model
"""

from main import create_threedimodel
from threedi_api.constants import ORGANISATION_UUID, THREEDIGLOBAL
from login import get_login_details_threedi, get_login_details_lizard
from geopackage import get_geopackage_layer
import argparse

#get API credentials from login.ini file
THREEDI_API_KEY = get_login_details_threedi(option='password_threedi')
LIZARD_API_KEY  = get_login_details_lizard(option='api_key_lizard')
ORGANISATION_UUID = ORGANISATION_UUID                                  #Fill in organisation_uuid (Default is to 3Di Global)
LOCAL_DIR = "C:/Temp/3Di Global"                                       #set a standard local directory where all the models are stored
PIXEL_SIZE = 30                                                        #Pixel size [m]
NR_CELLS = 20000                                                       #Desired approx. nr. of cells (defaults to 50.000)
DEM_RASTER_UUID = "eae92c48-cd68-4820-9d82-f86f763b4186"               #DEM raster UUID or "eae92c48-cd68-4820-9d82-f86f763b4186" (SRTM)

def create_threedimodel_by_catchment(HYBAS_ID: int):
    schematisation_name = str("CatchmentID_{}_{}").format(HYBAS_ID, THREEDIGLOBAL)
    extent_filename = get_geopackage_layer(HYBAS_ID)   #path to geopackage of the area of interest
    
    #Generate a threedimodel
    create_threedimodel(
        threedi_api_key = THREEDI_API_KEY,
        lizard_api_key = LIZARD_API_KEY,
        organisation_uuid = ORGANISATION_UUID,
        local_dir= LOCAL_DIR,
        schematisation_name=schematisation_name,
        extent_filename=extent_filename,
        #extent_layer_name=extent_layer_name,
        pixel_size= PIXEL_SIZE,
        nr_cells= NR_CELLS,
        dem_raster_uuid=DEM_RASTER_UUID
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Fill in requested Catchment ID (HYBAS_ID) by organisation to automatically generate a 2D model')
    parser.add_argument('HYBAS_ID', type=int, help='The HYBAS_ID requested by the organisation.')
    args = parser.parse_args()
    create_threedimodel_by_catchment(args.HYBAS_ID)
