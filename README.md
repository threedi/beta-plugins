# beta-plugins
Beta plugins for use of 3Di in the modeler interface

These plugins have been developed to test certain functionality and are not part of the official 3Di stack. Support for these plugins can be found by contacting the plugin authors. 

The plugins are developed for QGIS to aid in the modelling with 3Di. They are tested on QGIS 3.4.5. Most likely the plugins will function on newer QGIS versions as well, but this is not tested. The plugins are not compatible with QGIS 2 versions. 

To use the plugin you can download the zip:
https://github.com/threedi/beta-plugins/archive/master.zip

Extract the zip file and paste the plugin folder (i.e. apiconsole3di) in:
C:\Users\YOUR_USER_NAME\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins

For some of the plugins, a separate ZIP is available under 'Releases'. To install using this ZIP file in QGIS: Plugins > Manage and Install Plugins > Install From ZIP

Afterwards you should open QGIS, go to plugin manager, installed plugins, and activate the new plugins.

- build2dmodel: Extracts elevation, landuse and soil rasters from lizard and converts them to proper 3Di rasters
- custom statistics: calculate custom aggregations (e.g. sum, max, min, first, last, etc) for flow variables (waterlevel, volume, velocity, discharge, etc.)
- edit3dischematisation: alters 1D views to make them editable. Requires loading the model through the threediPlugin
- import_hydx: imports a GWSW Hydx dataset to a 3Di model.
- pipelevelcalculator: Calculate pipe levels based on a design and DEM.
- resultsdownloader: Searches for 3Di simulation results and facilitates downloading/visualising these
- threediresultstyler: Adds functionality like adding a styled DEM, areal photo's, saving/loading settings in the Layer menu (visibility, expanded groups and filters) and showing Courant numbers of the calculated results.
