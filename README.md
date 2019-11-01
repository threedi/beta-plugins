# beta-plugins

In this repository you will find beta plugins for use of 3Di in the modeler interface. These are experiments to test new functionalities and might not fully work. They have been developed by advisors from different companies. For support or use of these plugins please correspond with the author of the plugin.

If there is a plugin that you like to have implemented in the 3Di stack let us know via servicedesk@nelen-schuurmans.nl 

These are Plugins developed for QGIS to aid in the modelling with 3Di. They are tested on QGIS 3.4.5. Most likely the plugins will function on newer QGIS versions as well, but this is not tested. The plugins are not compatible with QGIS 2 versions. 

To use the plugin you can download the zip:
https://github.com/threedi/beta-plugins/archive/master.zip

Extract the zip file and paste the plugin folder (i.e. apiconsole3di) in:
C:\Users\YOUR_USER_NAME\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins

Afterwards you should open QGIS, go to plugin manager, installed plugins, and activate the new plugins.

- apiconsole3di: starts a 3Di simulation through the API.
- edit3dischematisation: alters 1D views to make them editable. Requires loading the model through the threediPlugin
- build2dmodel: Extracts elevation, landuse and soil rasters from lizard and converts them to proper 3Di rasters
- resultsdownloader: Searches for 3Di simulation results and facilitates downloading/visualising these
- threediresultstyler: Adds functionality like adding a styled DEM, areal photo's, saving/loading settings in the Layer menu (visibility, expanded groups and filters) and showing Courant numbers of the calculated results.