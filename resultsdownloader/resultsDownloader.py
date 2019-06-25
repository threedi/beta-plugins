# -*- coding: utf-8 -*-

from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from PyQt5.QtGui import QIcon
from PyQt5 import QtGui
from PyQt5.QtWidgets import QAction,QFileDialog,QMessageBox
from qgis.core import *

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .resultsDownloader_dialog import resultsDownloaderDialog
from .downloader import *
import os.path
from datetime import datetime
from urllib.parse import urlparse
from time import sleep
import logging
import os
import requests
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
MESSAGE_CATEGORY = 'downloadtask'

LIZARD_URL = "https://demo.lizard.net/api/v3/"
RESULT_LIMIT = 10

log = logging.getLogger()

SCENARIO_FILTERS = {
    "name": "name__icontains",
    "uuid": "uuid",
    "id": "id",
    "model_revision": "model_revision",
    "model_name": "model_name__icontains",
    "organisation": "organisation__icontains",
    "username": "username__icontains",
}

class downloadtask(QgsTask):
    def __init__(self,description,scenarioUUID,rasters,downloadProjection,cellSize,rasterDirectory,REQUESTS_HEADERS):
        super().__init__(description,QgsTask.CanCancel)
        self.scenarioUUID = scenarioUUID
        self.rasters = rasters
        self.downloadProjection = downloadProjection
        self.cellSize = cellSize
        self.rasterDirectory = rasterDirectory
        self.REQUESTS_HEADERS = REQUESTS_HEADERS
        self.exception = None

    @staticmethod
    def get_raster(scenario_uuid, raster_code,REQUESTS_HEADERS):
        """return json of raster based on scenario uuid and raster type"""
        r = requests.get(
            url="{}scenarios/{}".format(LIZARD_URL, scenario_uuid), headers=REQUESTS_HEADERS
        )
        r.raise_for_status()
        for result in r.json()["result_set"]:
            if result["result_type"]["code"] == raster_code:
                return result["raster"]

    @staticmethod
    def create_raster_task(raster, target_srs, resolution, REQUESTS_HEADERS, bounds=None, time=None):
        """create Lizard raster task"""

        if bounds == None:
            bounds = raster["spatial_bounds"]

        e = bounds["east"]
        w = bounds["west"]
        n = bounds["north"]
        s = bounds["south"]

        source_srs = "EPSG:4326"

        bbox = "POLYGON(({} {},{} {},{} {},{} {},{} {}))".format(
            w, n, e, n, e, s, w, s, w, n
        )

        url = "{}rasters/{}/data/".format(LIZARD_URL, raster["uuid"])
        if time is None:
            # non temporal raster
            payload = {
                "cellsize": resolution,
                "geom": bbox,
                "srs": source_srs,
                "target_srs": target_srs,
                "format": "geotiff",
                "async": "true",
            }
        else:
            # temporal rasters
            payload = {
                "cellsize": resolution,
                "geom": bbox,
                "srs": source_srs,
                "target_srs": target_srs,
                "time": time,
                "format": "geotiff",
                "async": "true",
            }
        r = requests.get(url=url, headers=REQUESTS_HEADERS, params=payload)
        r.raise_for_status()
        return r.json()

    @staticmethod
    def get_task_status(task_uuid,REQUESTS_HEADERS):
        """return status of task"""
        url = "{}tasks/{}/".format(LIZARD_URL, task_uuid)
        r = requests.get(url=url, headers=REQUESTS_HEADERS)
        r.raise_for_status()
        return r.json()["task_status"]

    @staticmethod
    def get_task_download_url(task_uuid,REQUESTS_HEADERS):
        """return url of successful task"""
        url = "{}tasks/{}/".format(LIZARD_URL, task_uuid)
        r = requests.get(url=url, headers=REQUESTS_HEADERS)
        r.raise_for_status()
        return r.json()["result_url"]

    @staticmethod
    def download_file(url, path,REQUESTS_HEADERS):
        """download url to specified path"""
        print(path)
        logging.debug("Start downloading file: {}".format(url))
        r = requests.get(url, auth=(REQUESTS_HEADERS["username"], REQUESTS_HEADERS["password"]))
        r.raise_for_status()
        with open(path, "wb") as file:
            for chunk in r.iter_content(100000):
                file.write(chunk)

    def run(self):
        QgsMessageLog.logMessage('Started task "{}"'.format(self.description()), 
                                  MESSAGE_CATEGORY, Qgis.Info)
        for raster_code in self.rasters:
            raster = self.get_raster(self.scenarioUUID, raster_code,self.REQUESTS_HEADERS)
            task = self.create_raster_task(raster, self.downloadProjection, self.cellSize, self.REQUESTS_HEADERS, None, None)
            task_uuid = task["task_id"]
            log.debug("Start waiting for task {} to finish".format(task_uuid))
            while self.get_task_status(task_uuid,REQUESTS_HEADERS) == "PENDING":
                sleep(5)
                log.debug("Still waiting for task {}".format(task_uuid))

            if self.get_task_status(task_uuid,REQUESTS_HEADERS) == "SUCCESS":
                # task is a succes, return download url
                log.debug(
                    "Task succeeded, start downloading url: {}".format(
                        self.get_task_download_url(task_uuid,REQUESTS_HEADERS)
                    )
                )
                download_url = self.get_task_download_url(task_uuid,REQUESTS_HEADERS)
                print(download_url)
                self.download_file(download_url, os.path.join(self.rasterDirectory,raster_code+'.tif'),self.REQUESTS_HEADERS)
            else:
                log.debug("Task failed")
            if self.isCanceled():
                    return False
        return True

    def finished(self, result):
        if result:
            QgsMessageLog.logMessage('Task "{name}" completed'.format(name=self.description()))
            QMessageBox.information(
            None,
            "Results downloader",
            "Results successfully downloaded."
            )
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

class resultsDownloader:
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
        self.tm = QgsApplication.taskManager()
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'resultsDownloader_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&resultsDownloader')

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
        return QCoreApplication.translate('resultsDownloader', message)


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

        icon_path = ':/plugins/resultsDownloader/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Download threedi results'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&resultsDownloader'),
                action)
            self.iface.removeToolBarIcon(action)

    def on_scenarioName_changed(self):
        value = self.dlg.scenarioName.text()
        found_scenarios = find_scenarios_by_name(value)
        self.dlg.scenarios.clear()
        self.scenario_mapping = []
        for scenario in found_scenarios:
            self.dlg.scenarios.addItems([scenario["name"]])
            self.scenario_mapping.append([scenario["name"],scenario["uuid"]])

        return self.scenario_mapping

    def on_scenario_selected(self):
        scenarioIndex = self.dlg.scenarios.currentIndex()
        self.scenarioUUID = self.scenario_mapping[scenarioIndex][1]
        r = requests.get(
        url="{}scenarios/{}".format(LIZARD_URL, self.scenarioUUID), headers=get_headers())
        scenarioJson = r.json()
        static_rasters, temporal_rasters = rasters_in_scenario(scenarioJson)
        self.raster_dict = {}
        self.dlg.rasterList.clear()

        for i in range(len(static_rasters)):
            key = static_rasters[i]["name_3di"]
            value = static_rasters[i]["code_3di"]
            self.raster_dict[key]=value
        raster_names = []
        for key in self.raster_dict:
            raster_names.append(key)
        self.dlg.rasterList.addItems(raster_names)
        return 

    def on_userName_changed(self):
        userName = self.dlg.userName.text()
        passWord = self.dlg.passWord.text()
        set_headers(userName, passWord)

    def on_passWord_changed(self):
        userName = self.dlg.userName.text()
        passWord = self.dlg.passWord.text()
        set_headers(userName, passWord)

    def on_download_toggled(self):
        if self.dlg.downloadBox.checkState() == 2:
            self.dlg.projection.setEnabled(1)
            self.dlg.cellSize.setEnabled(1)
            self.dlg.downloadDirectory.setEnabled(1)
        else:
            self.dlg.projection.setDisabled(1)
            self.dlg.cellSize.setDisabled(1)
            self.dlg.downloadDirectory.setDisabled(1)

    def getDirectoryFromUserSelection(self):
        """Gets a spatliate through the QFileDialog and inserts it. """
        directory_name = QFileDialog.getExistingDirectory(None, "select directory")
        self.dlg.downloadDirectory.setText(str(directory_name))
        return None

    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        supported_projections = ['EPSG:28992','EPSG:4326','EPSG:3857']
        if self.first_start == True:
            self.first_start = False
            self.dlg = resultsDownloaderDialog()
            self.dlg.passWord.setEchoMode(QtGui.QLineEdit.Password)
            self.dlg.rasterList.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
            self.dlg.projection.addItems(supported_projections)
            self.dlg.projection.setDisabled(1)
            self.dlg.cellSize.setDisabled(1)
            self.dlg.downloadDirectory.setDisabled(1)

        self.dlg.downloadBox.clicked.connect(self.on_download_toggled)
        self.dlg.scenarioName.editingFinished.connect(self.on_scenarioName_changed)
        self.dlg.userName.editingFinished.connect(self.on_userName_changed)
        self.dlg.passWord.editingFinished.connect(self.on_passWord_changed)
        self.dlg.directoryButton.clicked.connect(self.getDirectoryFromUserSelection)
        self.dlg.scenarios.activated.connect(self.on_scenario_selected)

        userName = self.dlg.userName.text()
        passWord = self.dlg.passWord.text()
        set_headers(userName,passWord)

        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            items = self.dlg.rasterList.selectedItems()
            selectedRasters = []
            for i in range(len(items)):
                selectedRasters.append(str(self.dlg.rasterList.selectedItems()[i].text()))
            raster_code_list=[]
            for raster in selectedRasters:
                raster_code_list.append(self.raster_dict.get(raster))
            if self.dlg.downloadBox.checkState() == 2:
                downloadDirectory = self.dlg.downloadDirectory.text()
                projectionIndex = self.dlg.projection.currentIndex()
                downloadProjection = supported_projections[projectionIndex]
                cellSize = self.dlg.cellSize.text()
                rasterTask = downloadtask('Download results',self.scenarioUUID,raster_code_list,downloadProjection,cellSize,downloadDirectory,REQUESTS_HEADERS)
                self.tm.addTask(rasterTask)
