# Plugin to easily extract/create basic 3Di rasters (dem, friction, infiltration). 

Requires Lizard subscription!

This plugin calls the Lizard API and extracts landuse, soil and elevation data based on a shapefile with the model extent. The landuse and soil are converted into friction and infiltration rasters based on SOBEK conversion tables. These rasters are all written to a raster folder. Afterwards the spatialite has its global and numerical settings updated to "basic" 2D settings. 

You should always check these settings carefully, as they differ based on the purpose of the model!! 
