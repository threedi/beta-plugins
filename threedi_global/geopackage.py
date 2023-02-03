# -*- coding: utf-8 -*-
"""
Created on Wed Jan 25 10:39:56 2023

@author: joost.vandijk
"""

from osgeo import gdal, ogr
import argparse

#Set constant values
GPKG_PATH = r"C:/Users/joost.vandijk/Documents/Projecten/W0176_3DiGlobal/hydrosheds/Global_hydrosheds.gpkg"
EXCLUDE_LAYER = "layer_styles"
COLUMN = "HYBAS_ID"

def get_geopackage_layer(HYBAS_ID: int):
    
    geopackage = gdal.OpenEx(GPKG_PATH, gdal.OF_VECTOR)
    # Iterate through each layer in the geopackage
    for i in range(geopackage.GetLayerCount()):
        layer = geopackage.GetLayerByIndex(i)
        layer_name = layer.GetName()
        if layer_name == EXCLUDE_LAYER:
            continue
        layer.SetAttributeFilter("{} = '{}'".format(COLUMN, HYBAS_ID))
        # Iterate through the features in the layer
        for feature in layer:
            # Check if the HYBAS_ID in the column matches the desired HYBAS_ID
            if feature.GetField(COLUMN) == HYBAS_ID:
                fid = feature.GetFID()
                layer_name_var = layer.GetName()
                # Print the feature ID
                print("Feature ID:", fid)
                print("Layer name:", layer_name_var)
                                
    # Select appurtenant layer and feature from HYBAS_ID
    src_lyr = geopackage.GetLayer(layer_name_var)
    src_lyr.SetAttributeFilter("FID={}".format(fid))
    
    path_output = "C:/Users/joost.vandijk/Documents/Projecten/W0176_3DiGlobal/hydrosheds/threediglobal/{}.gpkg".format(HYBAS_ID)
    
    # Create a new geopackage with the exported feature
    driver = ogr.GetDriverByName("GPKG")
    dst_ds = driver.CreateDataSource(path_output)
    dst_lyr = dst_ds.CopyLayer(src_lyr, "{}".format(HYBAS_ID))
    print("New geopackage layer created: {}".format(path_output), dst_lyr)
    
    geopackage = None
    dst_ds = None
    
    return path_output
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Find HYBAS_ID in specific layer and makes new geopackage')
    parser.add_argument('HYBAS_ID', type=int, help='The HYBAS_ID requested by the organisation.')
    args = parser.parse_args()
    get_geopackage_layer(args.HYBAS_ID)
    
 