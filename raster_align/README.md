# Plugin to align rasters for use in Threedi

Threedi requires for some rasters that they should be aligned in multiple ways: extent, pixels and data/nodata locations. This plugin alignes a given raster on a template.

Options:
1. Align nodata values: if checked it aligns the data/nodata pixels within a raster.
2. Nodata fill value: If the raster is too large compared to the template, it will set the raster which exceeds the extent to nodata.
   For cases in which nodata is present in the 'to be aligned' raster, but it is filled in the template raster with values, it has fill up using a certain value.
   This value is filled in this field.
3. Write statistics: If checked, writes a json with statistics of the raster to check for a correct alignment.
   

