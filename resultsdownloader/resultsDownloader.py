# -*- coding: utf-8 -*-

from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from PyQt5.QtGui import QIcon
from PyQt5 import QtGui
from PyQt5.QtWidgets import QAction,QFileDialog

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .resultsDownloader_dialog import resultsDownloaderDialog
from .downloader import *
import os.path


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
        print(self.raster_dict)
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
                for raster in raster_code_list:
                    filename = raster + '.tif'
                    download_raster(self.scenarioUUID,raster,downloadProjection,cellSize,pathname=os.path.join(downloadDirectory,filename))
