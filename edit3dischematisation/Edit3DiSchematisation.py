# -*- coding: utf-8 -*-
from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QMessageBox
from qgis.utils import iface
from .view_triggers import ViewTriggers
from .project_manager import *
from qgis.core import (
    QgsProject,
    QgsDataSourceUri,
    QgsMapLayer,
    QgsEditorWidgetSetup,
    QgsDefaultValue,
    QgsRelation,
)

# Initialize Qt resources from file resources.py
from .resources import *

# Import the code for the dialog
from .Edit3DiSchematisation_dialog import Edit3DiSchematisationDialog
import os.path
import sqlite3


class Edit3DiSchematisation:
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
        locale = QSettings().value("locale/userLocale")[0:2]
        locale_path = os.path.join(
            self.plugin_dir, "i18n", "Edit3DiSchematisation_{}.qm".format(locale)
        )

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > "4.3.3":
                QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u"&Edit3DiSchematisation")

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
        return QCoreApplication.translate("Edit3DiSchematisation", message)

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
        parent=None,
    ):
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
        action.toggled.connect(callback)
        action.setCheckable(True)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(self.menu, action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ":/plugins/Edit3DiSchematisation/edit_icon.png"
        self.add_action(
            icon_path,
            text=self.tr(u"Edit 3Di schematisation"),
            callback=self.run,
            parent=self.iface.mainWindow(),
        )
        # will be set False in run()
        self.first_start = True

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(self.tr(u"&Edit3DiSchematisation"), action)
            self.iface.removeToolBarIcon(action)

    def run(self,checked):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback
        if self.first_start == True:
            self.first_start = False
            self.dlg = Edit3DiSchematisationDialog()

        if checked:
        # run sql file to add triggers to views
            try:
                v2_global_settings = QgsProject.instance().mapLayersByName(
                    "v2_global_settings"
                )[0]
            except:
                QMessageBox.information(
                None,
                "Warning",
                "No model found"
                )
                return

            sqlite_dir = (
            v2_global_settings.dataProvider()
            .dataSourceUri()
            .split(" table")[0]
            .replace("dbname=", "")
            .replace("'", "")
            )
            view_connection = ViewTriggers({"db_path": sqlite_dir})
            view_connection.add_triggers()
            QSettings().setValue('/Map/identifyAutoFeatureForm','true')
            configure_snapping_settings()
            
            oned_layers = [
            "v2_connection_nodes",
            "v2_manhole_view",
            "v2_cross_section_location_view",
            "v2_cross_section_location",
            "v2_pumpstation_view",
            "v2_pumpstation_point_view",
            "v2_weir_view",
            "v2_culvert_view",
            "v2_orifice_view",
            "v2_pipe_view",
            "v2_culvert",  # yes.. this table has its own geom
            "v2_channel",
            ]
            
            boundary_condition_layers = [
            "v2_1d_boundary_conditions_view",
            "v2_2d_boundary_conditions"]
            
            lateral_layers = ["v2_1d_lateral_view", "v2_2d_lateral"]
            
            qgs_signals(oned_layers)
            qgs_signals(boundary_condition_layers)
            qgs_signals(lateral_layers)
            set_relations()
            configure_open_file_button()

            for layer in iface.mapCanvas().layers():
                if layer.type() == QgsMapLayer.VectorLayer:
                    layer.setDataSource(layer.source(), layer.name(), layer.providerType())
                    layer.startEditing()
            
            tables_to_editmode = ['v2_numerical_settings',
            'v2_simple_infiltration','v2_cross_section_definition',
            'v2_aggregation_settings','v2_groundwater','v2_interflow']
            for table in tables_to_editmode:
                qgs_table = QgsProject.instance().mapLayersByName(table)[0]
                qgs_table.setDataSource(qgs_table.source(), qgs_table.name(), qgs_table.providerType())
                qgs_table.startEditing()
            
        else:
            for layer in iface.mapCanvas().layers():
                if layer.isEditable():
                    if layer.isModified():
                        layer.commitChanges()
                        iface.vectorLayerTools().stopEditing(layer,False)
                    else: 
                        iface.vectorLayerTools().stopEditing(layer,False)
            tables_to_editmode = ['v2_numerical_settings',
            'v2_simple_infiltration','v2_cross_section_definition',
            'v2_aggregation_settings','v2_groundwater','v2_interflow']
            for table in tables_to_editmode:
                qgs_table = QgsProject.instance().mapLayersByName(table)[0]
                if qgs_table.isModified():
                    qgs_table.commitChanges()
                    iface.vectorLayerTools().stopEditing(qgs_table,False)
                else:
                    iface.vectorLayerTools().stopEditing(qgs_table,False)
