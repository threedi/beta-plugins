# Plugin to easily extract/create basic 3Di rasters (dem, friction, infiltration). 

Requires Lizard subscription!

This plugin calls the Lizard API and extracts landuse, soil and elevation data based on a shapefile with the model extent. The landuse and soil are converted into friction and infiltration rasters based on SOBEK conversion tables (see conversion tables in plugin folder). These rasters are all written to a raster folder. Afterwards the spatialite has its global and numerical settings updated to "basic" 2D settings. 

To use the plugin, the shapefile should be loaded inside the QGIS environment before opening the plugin. The Username and Password are Lizard credentials. You can use any grid cell size (pixel size) as long as it fits an even number of times into 10 meter (i.e. 0.5, 1, 2, 5 are okay while 0.4, 3 etc are not).

You should always check the numerical and global settings carefully, as they differ based on the purpose of the model!! 
