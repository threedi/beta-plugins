# -*- coding: utf-8 -*-

from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from PyQt5.QtGui import QIcon
from PyQt5 import QtGui
from PyQt5.QtWidgets import QAction,QFileDialog
from qgis.utils import iface
from qgis.core import *

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .build2Dmodel_dialog import build2DmodelDialog
import os.path
import requests
import json
import os, sys
import logging
import numpy as np
from osgeo import gdal
import csv
import sqlite3
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
MESSAGE_CATEGORY = 'backgroundprocessing'

class backgroundprocessing(QgsTask):
    def __init__(self, description,included_rasters,pixelSize,target_extent,
                 sourceSrs,targetSrs,rasterDirectory,headers,soil_raster,
                 landuse_raster,elevation_raster,soil_conversion_table,
                 landuse_conversion_table,elevation,friction,infiltration):
        super().__init__(description,QgsTask.CanCancel)
        self.included_rasters = included_rasters
        self.pixelSize = pixelSize
        self.target_extent = target_extent
        self.sourceSrs = sourceSrs
        self.targetSrs = targetSrs
        self.rasterDirectory = rasterDirectory
        self.headers = headers
        self.soil_raster = soil_raster
        self.landuse_raster = landuse_raster
        self.elevation_raster = elevation_raster
        self.soil_conversion_table = soil_conversion_table
        self.landuse_conversion_table = landuse_conversion_table
        self.elevation = elevation
        self.friction = friction
        self.infiltration = infiltration
        self.exception = None

    @staticmethod
    def download_file(url,folder,headers):
        """Downloads rasters from Lizard based on task URL and target folder
        also writes time indication. Sometimes this causes misbehaviour when
        there is a connection problem with Lizard"""
        if not os.path.exists(folder):
            os.makedirs(folder)
        file_name = os.path.join(folder,url.split('/')[-1])
        with open(file_name, "wb") as f:
            #print('Downloading {}'.format(file_name))
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

    @staticmethod
    def download_rasters(raster,pixelSize,target_extent,
                         sourceSrs,targetSrs,headers):
        """Defines a task URL in lizard and prepares the rasters for export. 
        A maximum time of 500 seconds per raster is allowed. The last rule
        of the function calls download_file which actually downloads the 
        rasters"""
        createTiffTaskUrl = 'https://demo.lizard.net/api/v3/rasters/{}/data/?async=true&cellsize={}&format=geotiff&geom={}&srs={}&target_srs={}'.format(raster,pixelSize,target_extent,sourceSrs,targetSrs)
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

    @staticmethod
    def load_soil_raster(soil_raster):
        gdal.UseExceptions()
        driver = gdal.GetDriverByName('GTiff')

        # load soil raster file
        soil_gfile = gdal.Open(soil_raster)
        soil_band = soil_gfile.GetRasterBand(1)
        soil_list = soil_band.ReadAsArray()
        soil_arr = np.asarray(soil_list)
        return soil_gfile, soil_band, soil_list, soil_arr

    @staticmethod
    def change_elevation_nodata_value(elevation_raster,rasterDirectory):
        gdal.UseExceptions()
        driver = gdal.GetDriverByName('GTiff')

        # load soil raster file
        elevation_gfile = gdal.Open(elevation_raster)
        elevation_band = elevation_gfile.GetRasterBand(1)
        elevation_list = elevation_band.ReadAsArray()
        elevation_arr = np.asarray(elevation_list)
        
        nodata = elevation_band.GetNoDataValue()
        nodatamask = elevation_list == nodata
        
        elevation_list[nodatamask] = -9999

        proj = elevation_gfile.GetProjection()
        georef = elevation_gfile.GetGeoTransform()

        fileUrl = os.path.join(rasterDirectory,r'dem.tif')
        elevation_gfile = driver.Create(fileUrl, elevation_gfile.RasterXSize, 
                                       elevation_gfile.RasterYSize, 1, 
                                       gdal.GDT_Float32,
                                       options = [ 'COMPRESS=DEFLATE' ])
        elevation_gfile.GetRasterBand(1).WriteArray(elevation_list)
        elevation_gfile.GetRasterBand(1).SetNoDataValue(-9999.0)
        elevation_gfile.SetProjection(proj)
        elevation_gfile.SetGeoTransform(georef)
        elevation_gfile.FlushCache()
        elevation_gfile = None

        return True

    @staticmethod
    def load_landuse_raster(landuse_raster):
        landuse_gfile = gdal.Open(landuse_raster)
        landuse_band = landuse_gfile.GetRasterBand(1)
        landuse_list = landuse_band.ReadAsArray()
        landuse_arr = np.asarray(landuse_list)

        # get meta data based on landuse
        proj = landuse_gfile.GetProjection()
        georef = landuse_gfile.GetGeoTransform()
        
        nodata = landuse_band.GetNoDataValue()
        nodatamask = landuse_list == nodata
        return landuse_gfile,landuse_band,landuse_list,landuse_arr,proj,georef,nodatamask

    @staticmethod
    def load_landuse_table(landuse_conversion_table):
        with open(landuse_conversion_table) as csvfile:
            readCSV = csv.reader(csvfile, delimiter=';')
            next(readCSV, None)  # skip the headers
            landusetype_list = []
            frictiontype_list = []
            permeability_list = []    # 
            for row in readCSV:
                # read lines
                landusetype = row[0]
                friction = row[2]
                permeability = row[3]
                # append to list
                landusetype_list.append(float(landusetype))
                frictiontype_list.append(float(friction))
                permeability_list.append(float(permeability))
        # landuse friction/infiltration relationship
        landuse_rel = np.asarray([landusetype_list,frictiontype_list,
                                  permeability_list])
        return landuse_rel

    @staticmethod
    def load_soil_table(soil_conversion_table):
        with open(soil_conversion_table) as csvfile:
            readCSV = csv.reader(csvfile, delimiter=';')
            next(readCSV, None)  # skip the headers
            soiltype_list = []
            infiltration_list = [] # 
            for row in readCSV:
                # read lines
                soiltype = row[0]
                infiltration = row[2]
                # append to list
                soiltype_list.append(float(soiltype))
                infiltration_list.append(float(infiltration))
      
        infiltration_rel = np.asarray([soiltype_list,infiltration_list])
        return infiltration_rel

    @staticmethod
    def create_friction_raster(landuse_list,landuse_arr,landuse_rel,
                               landuse_gfile,proj,georef,rasterDirectory,nodatamask):
        # compute friction
        driver = gdal.GetDriverByName('GTiff')
        friction_list = landuse_list.copy()
        friction_list = np.interp(landuse_arr,landuse_rel[0],landuse_rel[1])
        friction_list[nodatamask] = -9999
        ##store friction raster
        fileUrl = os.path.join(rasterDirectory,r'friction.tif')
        friction_gfile = driver.Create(fileUrl, landuse_gfile.RasterXSize, 
                                       landuse_gfile.RasterYSize, 1, 
                                       gdal.GDT_Float32,
                                       options = [ 'COMPRESS=DEFLATE' ])
        friction_gfile.GetRasterBand(1).WriteArray(friction_list)
        friction_gfile.GetRasterBand(1).SetNoDataValue(-9999.0)
        friction_gfile.SetProjection(proj)
        friction_gfile.SetGeoTransform(georef)
        friction_gfile.FlushCache()
        friction_gfile = None
        return True

    @staticmethod
    def create_infiltration_raster(landuse_list,landuse_arr,landuse_rel,
                                   soil_list,soil_arr,infiltration_rel,
                                   landuse_gfile,proj,georef,rasterDirectory,
                                   nodatamask):
        #### infiltration
        #compute permeability
        driver = gdal.GetDriverByName('GTiff')
        permeability_list = landuse_list.copy()
        permeability_list = np.interp(landuse_arr,landuse_rel[0],landuse_rel[2])

        # compute infiltration 
        infiltration_list = soil_list.copy()
        infiltration_list = np.interp(soil_arr,infiltration_rel[0],
                                      infiltration_rel[1])

        infiltration_list = infiltration_list * permeability_list
        infiltration_list[nodatamask] = -9999
        fileUrl = os.path.join(rasterDirectory,r'infiltration.tif')
        infiltration_gfile = driver.Create(fileUrl, landuse_gfile.RasterXSize,
                                           landuse_gfile.RasterYSize, 1,
                                           gdal.GDT_Float32,
                                           options = [ 'COMPRESS=DEFLATE' ] )
        infiltration_gfile.GetRasterBand(1).WriteArray(infiltration_list)
        infiltration_gfile.GetRasterBand(1).SetNoDataValue(-9999.0)
        infiltration_gfile.SetProjection(proj)
        infiltration_gfile.SetGeoTransform(georef)
        infiltration_gfile.FlushCache()
        infiltration_gfile = None
        return True

    def run(self):
        QgsMessageLog.logMessage('Started task "{}"'.format(self.description()), 
                                  MESSAGE_CATEGORY, Qgis.Info)

        for raster in self.included_rasters:
            tiff_download_url = self.download_rasters(raster,self.pixelSize,
                              self.target_extent,self.sourceSrs,self.targetSrs,self.headers)
            self.download_file(tiff_download_url,self.rasterDirectory,self.headers)
            if self.isCanceled():
                return False

        if self.elevation == True:
            result = self.change_elevation_nodata_value(self.elevation_raster,self.rasterDirectory)

        if self.infiltration == True:
            soil_gfile, soil_band, soil_list, soil_arr = self.load_soil_raster(self.soil_raster)
            landuse_gfile,landuse_band,landuse_list,landuse_arr,proj,georef,nodatamask = self.load_landuse_raster(self.landuse_raster)
            landuse_rel = self.load_landuse_table(self.landuse_conversion_table)
            infiltration_rel = self.load_soil_table(self.soil_conversion_table)
            result = self.create_infiltration_raster(landuse_list,landuse_arr,landuse_rel,
                                            soil_list,soil_arr,infiltration_rel,
                                            landuse_gfile,proj,georef,self.rasterDirectory,
                                            nodatamask)

        if self.friction == True and self.infiltration == True:
            result = self.create_friction_raster(landuse_list,landuse_arr,landuse_rel,
                                        landuse_gfile,proj,georef,self.rasterDirectory,
                                        nodatamask)

        if self.friction == True and self.infiltration == False:
            landuse_gfile, landuse_band, landuse_list, landuse_arr, proj, georef,nodatamask = self.load_landuse_raster(self.landuse_raster)
            landuse_rel = self.load_landuse_table(self.landuse_conversion_table)
            result = self.create_friction_raster(landuse_list,landuse_arr,landuse_rel,
                                        landuse_gfile,proj,georef,self.rasterDirectory,
                                        nodatamask)
        return True

    def finished(self, result):
        if result:
            QgsMessageLog.logMessage('Task "{name}" comleted'.format(name=self.description()))
            if self.elevation == True:
                iface.addRasterLayer(os.path.join(self.rasterDirectory,r'hoogte.tif'),"Elevation")
            if self.infiltration == True:
                iface.addRasterLayer(os.path.join(self.rasterDirectory,r'infiltration.tif'),"Infiltration")
            if self.friction == True:
                iface.addRasterLayer(os.path.join(self.rasterDirectory,r'friction.tif'),"Friction")
        else:
            if self.exception is None:
                QgsMessageLog.logMessage(
                    'Task "{name}" not successful but without '\
                    'exception (probably the task was manually '\
                    'canceled by the user)'.format(
                        name=self.description()),
                    MESSAGE_CATEGORY, Qgis.Warning)
            else:
                QgsMessageLog.logMessage(
                    'Task "{name}" Exception: {exception}'.format(
                        name=self.description(),
                        exception=self.exception),
                    MESSAGE_CATEGORY, Qgis.Critical)
                raise self.exception

    def cancel(self):
        QgsMessageLog.logMessage(
            'Task "{name}" was canceled'.format(
                name=self.description()),
            MESSAGE_CATEGORY, Qgis.Info)
        super().cancel()

class build2Dmodel:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'build2Dmodel_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&build2Dmodel')
        
        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('build2Dmodel', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/build2Dmodel/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Generate 2D model'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&build2Dmodel'),
                action)
            self.iface.removeToolBarIcon(action)

    def getSpatialiteFromUserSelection(self):
        """Gets a spatliate through the QFileDialog and inserts it. """
        file_name = QFileDialog.getOpenFileName(None, "select spatialite")[0]
        self.dlg.spatialiteFile.setText(str(file_name))
        return None
        
    def run(self):
        """Run method that performs all the real work"""
        # variables
        dem = '1d65a4e'
        soil = '773c4a0'
        landuse = 'e037e7a'
        included_rasters = []
        supported_projections = ['EPSG:28992','EPSG:27700']
        dirname = os.path.dirname(os.path.abspath(__file__))
        sqlfile2D = os.path.join(dirname, r'fill_2d_settings.sql')

        # Create the dialog with elements and keep reference
        # Only create GUI ONCE in callback
        if self.first_start == True:
            self.first_start = False
            self.dlg = build2DmodelDialog()
            self.dlg.targetSrs.addItems(supported_projections)
            self.dlg.passWord.setEchoMode(QtGui.QLineEdit.Password)
            
        dirname = os.path.dirname(os.path.abspath(__file__))
        landuse_conversion_table = os.path.join(dirname, r'landuse_conversion_table.csv')
        soil_conversion_table = os.path.join(dirname, 
                                                 r'soil_conversion_table.csv')

        self.dlg.spatialiteButton.clicked.connect(self.getSpatialiteFromUserSelection)

        layers = [layer for layer in QgsProject.instance().mapLayers().values()]
        layer_list = []
        for layer in layers:
            if layer.type() == QgsMapLayer.VectorLayer: 
                if layer.wkbType() == 6 or layer.wkbType == 3:
                    layer_list.append(layer.name())
        self.dlg.modelExtent.clear()
        self.dlg.modelExtent.addItems(layer_list)

        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            userName = self.dlg.userName.text()
            passWord = self.dlg.passWord.text()
            headers = {
            "username": '{}'.format(userName),
            "password": '{}'.format(passWord),
            "Content-Type": "application/json"
            }        

            pixelSize = float(self.dlg.pixelSize.text())
            spatialiteFile = self.dlg.spatialiteFile.text()
            selectedLayerIndex = self.dlg.targetSrs.currentIndex()
            targetSrs = supported_projections[selectedLayerIndex]
            if self.dlg.demCheckbox.checkState() == 2:
                elevation = True
                included_rasters.append(dem)
            else:
                elevation = False
            if self.dlg.infiltrationCheckbox.checkState() == 2:
                included_rasters.append(soil)
                included_rasters.append(landuse)
                infiltration = True
            else:
                infiltration = False
            if self.dlg.frictionCheckbox.checkState() == 2:
                friction = True
            else:
                friction = False
            if friction == True and 'e037e7a' not in included_rasters:
                included_rasters.append(landuse)

            spatialiteDirectory = os.path.dirname(spatialiteFile)
            if not os.path.exists(os.path.join(spatialiteDirectory,r'rasters')):
                os.makedirs(os.path.join(spatialiteDirectory,r'rasters'))
            rasterDirectory = os.path.join(spatialiteDirectory,r'rasters')

            soil_raster = os.path.join(rasterDirectory,r'bodem-3di.tif')
            landuse_raster = os.path.join(rasterDirectory,r'fysiek-voorkomen.tif')
            elevation_raster = os.path.join(rasterDirectory,r'hoogte.tif')

            selectedLayerIndex = self.dlg.modelExtent.currentIndex()
            extent_layer_name = layer_list[selectedLayerIndex]
            extent_layers = QgsProject.instance().mapLayersByName(extent_layer_name)[0]
            sourceSrs = extent_layers.crs().authid()
            target_extent=[]
            extent_features = extent_layers.getFeatures(QgsFeatureRequest())
            for f in extent_features:
                f_geom = f.geometry()
                target_extent = f_geom.asWkt().replace('MultiPolygon','Polygon')

            target_extent = target_extent.replace('(((','((')
            target_extent = target_extent.replace(')))','))')
            getRasters = backgroundprocessing('download 3Di rasters',included_rasters,
                                            pixelSize,target_extent,sourceSrs,
                                            targetSrs,rasterDirectory,headers,
                                            soil_raster,landuse_raster,elevation_raster,
                                            soil_conversion_table,
                                            landuse_conversion_table, elevation,
                                            friction, infiltration)
            QgsApplication.taskManager().addTask(getRasters)

            query = open(sqlfile2D, 'r').read()
            conn = sqlite3.connect(spatialiteFile)
            c = conn.cursor()
            c.executescript(query)
            if infiltration == False:
                c.execute("update v2_simple_infiltration set infiltration_rate_file = NULL")
            if friction == False:
                c.execute("update v2_global_settings set frict_coef_file = NULL")
            conn.commit()
            c.close()
            conn.close()
