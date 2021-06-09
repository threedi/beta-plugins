# 3Di Beta Plugins
Beta plugins for use of 3Di in the modeler interface

## Disclaimer
These plugins have been developed by 3Di users to test certain functionality and are not part of the official 3Di stack. Support for these plugins can be found by contacting the plugin authors. 

The plugins are developed for QGIS to aid in the modelling with 3Di. They are tested on QGIS 3.4.5. Most likely the plugins will function on newer QGIS versions as well, but this is not tested. The plugins are not compatible with QGIS 2 versions. 

## Installation
* Download this zip file: https://github.com/threedi/beta-plugins/archive/master.zip Please note: *this zip cannot be used for the 'Install from ZIP' option in QGIS*
* Extract the downloaded zip file
* The extract contains a folder 'beta-plugins-master. Copy the contents of this folder (not the folder itself) to the QGIS plugins folder. You can find the QGIS plugins folder from the QGIS Main Menu: Settings > User Profiles > Open Active Profile Folder > browse further to \python\plugins. A common location of this folder is C:\Users\YOUR_USER_NAME\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins.

* Alternatively, if you are only interested in one specific plugin (e.g. the Import HydX plugin), you can also copy just that folder (e.g. the folder 'import_hydx') to the the plugins folder.
* (re)start QGIS
* Open the plugin manager (QGIS Main Menu > Plugins > Manage and Install Plugins)
* Activate the newly installed plugins by ticking the box to the left of the plugin's name.

*TIP* For some of the plugins, a separate ZIP is available under 'Releases'. To install using this ZIP file in QGIS: Plugins > Manage and Install Plugins > Install From ZIP

## Overview of available beta plugins
Below the currently available beta plugins are listed. Most plugins have some documentation of their own. Click on the plugin's folder in the overview above to view these.

* apiconsole3di: starts a 3Di simulation through the (deprecated but still operational) API v1. Made by Ivar Lokhorst (Nelen & Schuurmans).
* build2dmodel: Extracts elevation, landuse and soil rasters from lizard and converts them to proper 3Di rasters. Made by Ivar Lokhorst (Nelen & Schuurmans).
* edit3dischematisation: alters 1D views to make them editable. Requires loading the model through the threediPlugin. Made by Ivar Lokhorst (Nelen & Schuurmans).
* import_hydx: imports a GWSW Hydx dataset to a 3Di model. Made by Arnold van 't Veld (Nelen & Schuurmans).
* pipelevelcalculator: Calculate pipe levels based on a design and DEM. Made by Emile de Badts (Nelen & Schuurmans).
* resultsdownloader: Searches for 3Di simulation results and facilitates downloading/visualising these. Made by Ivar Lokhorst / Emiel Verstegen (Nelen & Schuurmans).
* threedi_custom_stats: 3Di Custom Statistics. Calculate custom aggregations (e.g. sum, max, min, first, last, etc) for flow variables (waterlevel, volume, velocity, discharge, etc.). Made by Leendert van Wolfswinkel (Nelen & Schuurmans).
* threediresultstyler: Adds functionality like adding a styled DEM, areal photo's, saving/loading settings in the Layer menu (visibility, expanded groups and filters) and showing Courant numbers of the calculated results. Made by Emiel Verstegen (Nelen & Schuurmans).

## Contribute
You are welcome to contribute by filing bugs or feature requests, add your own plugin, improve existing plugins (please make a pull request tagging the original author) or in any other way you see fit.
