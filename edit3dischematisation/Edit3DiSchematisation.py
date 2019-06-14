# -*- coding: utf-8 -*-
from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QMessageBox
from qgis.utils import iface
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

    def configure_pipe_form(self):
        v2_pipe_view = QgsProject.instance().mapLayersByName("v2_pipe_view")[0]
        idx = v2_pipe_view.fields().indexFromName("pipe_calculation_type")
        editor_widget_setup = QgsEditorWidgetSetup(
            "ValueMap", {"map": {u"isolated": u"1", u"connected": u"2"}}
        )
        v2_pipe_view.setEditorWidgetSetup(idx, editor_widget_setup)

        idx = v2_pipe_view.fields().indexFromName("pipe_friction_type")
        editor_widget_setup = QgsEditorWidgetSetup(
            "ValueMap", {"map": {u"Chezy": u"1", u"Manning": u"2"}}
        )
        v2_pipe_view.setEditorWidgetSetup(idx, editor_widget_setup)

        idx = v2_pipe_view.fields().indexFromName("pipe_material")
        editor_widget_setup = QgsEditorWidgetSetup(
            "ValueMap",
            {
                "map": {
                    u"concrete": u"0",
                    u"Pvc": u"1",
                    u"gres": u"2",
                    u"cast iron": u"3",
                    u"brickwork": u"4",
                    u"HPE": u"5",
                }
            },
        )
        v2_pipe_view.setEditorWidgetSetup(idx, editor_widget_setup)

        idx = v2_pipe_view.fields().indexFromName("pipe_sewerage_type")
        editor_widget_setup = QgsEditorWidgetSetup(
            "ValueMap",
            {
                "map": {
                    u"Mixed": u"0",
                    u"Storm water": u"1",
                    u"Dry weather flow": u"2",
                    u"Transport": u"3",
                    u"Spillway": u"4",
                    u"zinker": u"5",
                }
            },
        )
        v2_pipe_view.setEditorWidgetSetup(idx, editor_widget_setup)

        idx = v2_pipe_view.fields().indexFromName("pipe_zoom_category")
        editor_widget_setup = QgsEditorWidgetSetup(
            "ValueMap",
            {
                "map": {
                    u"0": u"0",
                    u"1": u"1",
                    u"2": u"2",
                    u"3": u"3",
                    u"4": u"4",
                    u"5": u"5",
                }
            },
        )
        v2_pipe_view.setEditorWidgetSetup(idx, editor_widget_setup)

    def configure_manhole_form(self):
        v2_manhole_view = QgsProject.instance().mapLayersByName("v2_manhole_view")[0]
        idx = v2_manhole_view.fields().indexFromName("manh_shape")
        editor_widget_setup = QgsEditorWidgetSetup(
            "ValueMap",
            {"map": {u"square": u"00", u"round": u"01", u"rectangle": u"02"}},
        )
        v2_manhole_view.setEditorWidgetSetup(idx, editor_widget_setup)

        idx = v2_manhole_view.fields().indexFromName("manh_manhole_indicator")
        editor_widget_setup = QgsEditorWidgetSetup(
            "ValueMap", {"map": {u"Inspection": u"0", u"Outlet": u"1", u"Pump": u"2"}}
        )
        v2_manhole_view.setEditorWidgetSetup(idx, editor_widget_setup)

        idx = v2_manhole_view.fields().indexFromName("manh_calculation_type")
        editor_widget_setup = QgsEditorWidgetSetup(
            "ValueMap",
            {"map": {u"Embedded": u"0", u"Isolated": u"1", u"Connected": u"2"}},
        )
        v2_manhole_view.setEditorWidgetSetup(idx, editor_widget_setup)

        idx = v2_manhole_view.fields().indexFromName("manh_zoom_category")
        editor_widget_setup = QgsEditorWidgetSetup(
            "ValueMap",
            {
                "map": {
                    u"0": u"0",
                    u"1": u"1",
                    u"2": u"2",
                    u"3": u"3",
                    u"4": u"4",
                    u"5": u"5",
                }
            },
        )
        v2_manhole_view.setEditorWidgetSetup(idx, editor_widget_setup)

    def configure_orifice_form(self):
        v2_orifice_view = QgsProject.instance().mapLayersByName("v2_orifice_view")[0]
        idx = v2_orifice_view.fields().indexFromName("orf_sewerage")
        editor_widget_setup = QgsEditorWidgetSetup(
            "ValueMap", {"map": {u"False": u"0", u"True": u"1"}}
        )
        v2_orifice_view.setEditorWidgetSetup(idx, editor_widget_setup)

        idx = v2_orifice_view.fields().indexFromName("orf_friction_type")
        editor_widget_setup = QgsEditorWidgetSetup(
            "ValueMap", {"map": {u"Chezy": u"1", u"Manning": u"2"}}
        )
        v2_orifice_view.setEditorWidgetSetup(idx, editor_widget_setup)

        idx = v2_orifice_view.fields().indexFromName("orf_zoom_category")
        editor_widget_setup = QgsEditorWidgetSetup(
            "ValueMap",
            {
                "map": {
                    u"0": u"0",
                    u"1": u"1",
                    u"2": u"2",
                    u"3": u"3",
                    u"4": u"4",
                    u"5": u"5",
                }
            },
        )
        v2_orifice_view.setEditorWidgetSetup(idx, editor_widget_setup)

        idx = v2_orifice_view.fields().indexFromName("orf_crest_type")
        editor_widget_setup = QgsEditorWidgetSetup(
            "ValueMap", {"map": {u"Broad crested": u"3", u"Short crested": u"4"}}
        )
        v2_orifice_view.setEditorWidgetSetup(idx, editor_widget_setup)

    def configure_weir_form(self):
        v2_weir_view = QgsProject.instance().mapLayersByName("v2_weir_view")[0]
        idx = v2_weir_view.fields().indexFromName("weir_crest_type")
        editor_widget_setup = QgsEditorWidgetSetup(
            "ValueMap", {"map": {u"Broad crested": u"3", u"Short crested": u"4"}}
        )
        v2_weir_view.setEditorWidgetSetup(idx, editor_widget_setup)

        idx = v2_weir_view.fields().indexFromName("weir_sewerage")
        editor_widget_setup = QgsEditorWidgetSetup(
            "ValueMap", {"map": {u"False": u"0", u"True": u"1"}}
        )
        v2_weir_view.setEditorWidgetSetup(idx, editor_widget_setup)

        idx = v2_weir_view.fields().indexFromName("weir_friction_type")
        editor_widget_setup = QgsEditorWidgetSetup(
            "ValueMap", {"map": {u"Chezy": u"1", u"Manning": u"2"}}
        )
        v2_weir_view.setEditorWidgetSetup(idx, editor_widget_setup)

        idx = v2_weir_view.fields().indexFromName("weir_zoom_category")
        editor_widget_setup = QgsEditorWidgetSetup(
            "ValueMap",
            {
                "map": {
                    u"0": u"0",
                    u"1": u"1",
                    u"2": u"2",
                    u"3": u"3",
                    u"4": u"4",
                    u"5": u"5",
                }
            },
        )
        v2_weir_view.setEditorWidgetSetup(idx, editor_widget_setup)

    def configure_pumpstation_form(self):
        v2_pumpstation_view = QgsProject.instance().mapLayersByName(
            "v2_pumpstation_view"
        )[0]
        idx = v2_pumpstation_view.fields().indexFromName("pump_type")
        editor_widget_setup = QgsEditorWidgetSetup(
            "ValueMap",
            {
                "map": {
                    u"Responds on suction side": u"1",
                    u"Responds on delivery side": u"2",
                }
            },
        )
        v2_pumpstation_view.setEditorWidgetSetup(idx, editor_widget_setup)

        idx = v2_pumpstation_view.fields().indexFromName("pump_sewerage")
        editor_widget_setup = QgsEditorWidgetSetup(
            "ValueMap", {"map": {u"False": u"0", u"True": u"1"}}
        )
        v2_pumpstation_view.setEditorWidgetSetup(idx, editor_widget_setup)

    def configure_culvert_form(self):
        v2_culvert_view = QgsProject.instance().mapLayersByName("v2_culvert_view")[0]
        idx = v2_culvert_view.fields().indexFromName("cul_calculation_type")
        editor_widget_setup = QgsEditorWidgetSetup(
            "ValueMap",
            {
                "map": {
                    u"Embedded": u"100",
                    u"Isolated": u"101",
                    u"Connected": u"102",
                    u"Double connected": u"105",
                }
            },
        )
        v2_culvert_view.setEditorWidgetSetup(idx, editor_widget_setup)

        idx = v2_culvert_view.fields().indexFromName("cul_friction_type")
        editor_widget_setup = QgsEditorWidgetSetup(
            "ValueMap", {"map": {u"Chezy": u"1", u"Manning": u"2"}}
        )
        v2_culvert_view.setEditorWidgetSetup(idx, editor_widget_setup)

        idx = v2_culvert_view.fields().indexFromName("cul_zoom_category")
        editor_widget_setup = QgsEditorWidgetSetup(
            "ValueMap",
            {
                "map": {
                    u"0": u"0",
                    u"1": u"1",
                    u"2": u"2",
                    u"3": u"3",
                    u"4": u"4",
                    u"5": u"5",
                }
            },
        )
        v2_culvert_view.setEditorWidgetSetup(idx, editor_widget_setup)

    def configure_channel_form(self):
        v2_channel = QgsProject.instance().mapLayersByName("v2_channel")[0]
        idx = v2_channel.fields().indexFromName("calculation_type")
        editor_widget_setup = QgsEditorWidgetSetup(
            "ValueMap",
            {
                "map": {
                    u"Embedded": u"100",
                    u"Isolated": u"101",
                    u"Connected": u"102",
                    u"Double connected": u"105",
                }
            },
        )
        v2_channel.setEditorWidgetSetup(idx, editor_widget_setup)

    def configure_1d_bound_form(self):
        v2_1d_boundary_view = QgsProject.instance().mapLayersByName(
            "v2_1d_boundary_view"
        )[0]
        idx = v2_1d_boundary_view.fields().indexFromName("bound_boundary_type")
        editor_widget_setup = QgsEditorWidgetSetup(
            "ValueMap",
            {
                "map": {
                    u"Waterlevel": u"1",
                    u"Velocity": u"2",
                    u"Discharge": u"3",
                    u"Sommerfeld": u"5",
                }
            },
        )
        v2_1d_boundary_view.setEditorWidgetSetup(idx, editor_widget_setup)

        idx = v2_1d_boundary_view.fields().indexFromName("bound_timeseries")
        setup = QgsEditorWidgetSetup("TextEdit", {"IsMultiline": "True"})
        v2_1d_boundary_view.setEditorWidgetSetup(idx, setup)

    def set_default_values(self):
        v2_pipe_view = QgsProject.instance().mapLayersByName("v2_pipe_view")[0]
        v2_manhole_view = QgsProject.instance().mapLayersByName("v2_manhole_view")[0]
        v2_weir_view = QgsProject.instance().mapLayersByName("v2_weir_view")[0]
        v2_orifice_view = QgsProject.instance().mapLayersByName("v2_orifice_view")[0]
        v2_pumpstation_view = QgsProject.instance().mapLayersByName(
            "v2_pumpstation_view"
        )[0]
        v2_culvert_view = QgsProject.instance().mapLayersByName("v2_culvert_view")[0]
        v2_channel = QgsProject.instance().mapLayersByName("v2_channel")[0]
        v2_1d_boundary_view = QgsProject.instance().mapLayersByName(
            "v2_1d_boundary_view"
        )[0]

        default_settings = [[v2_pipe_view, "pipe_sewerage_type", "0"],
                            [v2_pipe_view, "pipe_dist_calc_points","1000"],
                            [v2_pipe_view, "pipe_material","0"],
                            [v2_pipe_view, "pipe_zoom_category","2"],
                            [v2_pipe_view, "pipe_display_name", "'New'"],
                            [v2_pipe_view, "pipe_code", "'New'"],
                            [v2_pipe_view, "pipe_friction_value","0.0145"],
                            [v2_pipe_view, "pipe_friction_type","2"],
                            [v2_pipe_view, "pipe_calculation_type","1"],
                            [v2_manhole_view, "manh_display_name","'New'"],
                            [v2_manhole_view, "manh_shape","'00'"],
                            [v2_manhole_view, "manh_width","0.8"],
                            [v2_manhole_view, "manh_length","0.8"],
                            [v2_manhole_view, "manh_manhole_indicator","0"],
                            [v2_manhole_view, "manh_calculation_type","2"],
                            [v2_manhole_view, "manh_zoom_category","2"],
                            [v2_manhole_view, "manh_code", "'New'"],
                            [v2_manhole_view, "node_storage_area","0.64"],
                            [v2_manhole_view, "node_code","'New'"],
                            [v2_weir_view, "weir_display_name", "'New'"],
                            [v2_weir_view, "weir_code","'New'"],
                            [v2_weir_view, "weir_crest_type", "3"],
                            [v2_weir_view, "weir_sewerage", "0"],
                            [v2_weir_view, "weir_discharge_coefficient_positive","0.85"],
                            [v2_weir_view, "weir_discharge_coefficient_negative","0.85"],
                            [v2_weir_view, "weir_zoom_category","3"],
                            [v2_weir_view, "weir_friction_value", "0.02"],
                            [v2_weir_view, "weir_friction_type", "2"],
                            [v2_orifice_view,"orf_display_name","'New'"],
                            [v2_orifice_view, "orf_code","'New'"],
                            [v2_orifice_view, "orf_sewerage", "0"],
                            [v2_orifice_view, "orf_friction_value","0.0133"],
                            [v2_orifice_view, "orf_friction_type","2"],
                            [v2_orifice_view, "orf_discharge_coefficient_positive","0.85"],
                            [v2_orifice_view, "orf_discharge_coefficient_negative","0.85"],
                            [v2_orifice_view, "orf_zoom_category","3"],
                            [v2_orifice_view, "orf_crest_type","3"],
                            [v2_pumpstation_view, "pump_display_name","'New'"],
                            [v2_pumpstation_view, "pump_code", "'New'"],
                            [v2_pumpstation_view, "pump_type", "1"],
                            [v2_pumpstation_view, "pump_sewerage","1"],
                            [v2_pumpstation_view, "pump_zoom_category","2"],
                            [v2_culvert_view, "cul_display_name","'New'"],
                            [v2_culvert_view, "cul_code", "'New'"],
                            [v2_culvert_view, "cul_calculation_type", "101"],
                            [v2_culvert_view, "cul_friction_type","2"],
                            [v2_culvert_view, "cul_friction_value","0.02"],
                            [v2_culvert_view, "cul_dist_calc_points","50"],
                            [v2_culvert_view, "cul_zoom_category","4"],
                            [v2_culvert_view, "cul_discharge_coefficient_positive", "0.8"],
                            [v2_culvert_view, "cul_discharge_coefficient_negative","0.8"],
                            [v2_channel, "display_name","'New'"],
                            [v2_channel, "code","'New'"],
                            [v2_channel, "dist_calc_points","50"],
                            [v2_channel, "zoom_category","5"],
                            [v2_channel, "calculation_type", "102"],
                            [v2_1d_boundary_view, "bound_boundary_type","1"],
                            [v2_1d_boundary_view, "node_storage_area","0.1"],
                            [v2_1d_boundary_view, "node_code","'New'"]]

        for view, name, default in default_settings:
            idx = view.fields().indexFromName(name)
            view.setDefaultValueDefinition(idx, QgsDefaultValue(default))

    def hide_fields(self):
        v2_pipe_view = QgsProject.instance().mapLayersByName("v2_pipe_view")[0]
        v2_manhole_view = QgsProject.instance().mapLayersByName("v2_manhole_view")[0]
        v2_orifice_view = QgsProject.instance().mapLayersByName("v2_orifice_view")[0]
        v2_weir_view = QgsProject.instance().mapLayersByName("v2_weir_view")[0]
        v2_pumpstation_view = QgsProject.instance().mapLayersByName(
            "v2_pumpstation_view"
        )[0]
        v2_culvert_view = QgsProject.instance().mapLayersByName("v2_culvert_view")[0]
        v2_1d_boundary_view = QgsProject.instance().mapLayersByName(
            "v2_1d_boundary_view"
        )[0]

        fields_list = [[v2_pipe_view,"pipe_connection_node_start_id"],
                       [v2_pipe_view,"pipe_connection_node_end_id"],
                       [v2_pipe_view,"pipe_profile_num"],
                       [v2_pipe_view,"def_id"],
                       [v2_pipe_view,"ROWID"],
                       [v2_pipe_view,"pipe_pipe_quality"],
                       [v2_manhole_view,"ROWID"],
                       [v2_manhole_view,"node_the_geom_linestring"],
                       [v2_manhole_view,"manh_sediment_level"],
                       [v2_manhole_view,"manh_connection_node_id"],
                       [v2_orifice_view,"ROWID"],
                       [v2_orifice_view,"def_id"],
                       [v2_orifice_view,"orf_connection_node_start_id"],
                       [v2_orifice_view,"orf_connection_node_end_id"],
                       [v2_orifice_view,"orf_max_capacity"],
                       [v2_weir_view,"ROWID"],
                       [v2_weir_view,"def_id"],
                       [v2_weir_view,"weir_connection_node_start_id"],
                       [v2_weir_view,"weir_connection_node_end_id"],
                       [v2_weir_view,"weir_external"],
                       [v2_pumpstation_view,"ROWID"],
                       [v2_pumpstation_view,"def_id"],
                       [v2_pumpstation_view,"pump_connection_node_start_id"],
                       [v2_pumpstation_view,"pump_connection_node_end_id"],
                       [v2_pumpstation_view,"pump_classification"],
                       [v2_culvert_view,"ROWID"],
                       [v2_culvert_view,"def_id"],
                       [v2_culvert_view,"cul_connection_node_start_id"],
                       [v2_culvert_view,"cul_connection_node_end_id"],
                       [v2_1d_boundary_view,"ROWID"],
                       [v2_1d_boundary_view,"bound_connection_node_id"],
                       [v2_1d_boundary_view,"node_the_geom_linestring"]]
                       

        setup = QgsEditorWidgetSetup("Hidden", {})
        for view,field in fields_list:
            idx = view.fields().indexFromName(field)
            view.setEditorWidgetSetup(idx, setup)

    def remove_field_config(self):
        v2_manhole_view = QgsProject.instance().mapLayersByName("v2_manhole_view")[0]
        v2_weir_view = QgsProject.instance().mapLayersByName("v2_weir_view")[0]
        v2_pipe_view = QgsProject.instance().mapLayersByName("v2_pipe_view")[0]
        v2_orifice_view = QgsProject.instance().mapLayersByName("v2_orifice_view")[0]
        v2_culvert_view = QgsProject.instance().mapLayersByName("v2_culvert_view")[0]
        v2_pumpstation_view = QgsProject.instance().mapLayersByName(
            "v2_pumpstation_view"
        )[0]
        v2_1d_boundary_view = QgsProject.instance().mapLayersByName(
            "v2_1d_boundary_view"
        )[0]
        v2_channel = QgsProject.instance().mapLayersByName("v2_channel")[0]

        view_list = [v2_manhole_view,v2_weir_view,v2_pipe_view,v2_orifice_view,
                     v2_culvert_view,v2_pumpstation_view,v2_1d_boundary_view,
                     v2_channel]
                     
        setup = QgsEditorWidgetSetup("TextEdit", {"IsMultiline": "False"})

        for view in view_list:
            for idx,val in enumerate(view.fields()):
                view.setEditorWidgetSetup(idx, setup)

    def set_xsec_relations(self):
        v2_pipe_view = QgsProject.instance().mapLayersByName("v2_pipe_view")[0]
        v2_pipe_id = v2_pipe_view.id()
        pipe_idx = v2_pipe_view.fields().indexFromName("pipe_cross_section_definition_id")

        v2_orifice_view = QgsProject.instance().mapLayersByName("v2_orifice_view")[0]
        v2_orifice_id = v2_orifice_view.id()
        orf_idx = v2_orifice_view.fields().indexFromName("orf_cross_section_definition_id")
        
        v2_weir_view = QgsProject.instance().mapLayersByName("v2_weir_view")[0]
        v2_weir_id = v2_weir_view.id()
        weir_idx = v2_weir_view.fields().indexFromName("weir_cross_section_definition_id")
        
        v2_culvert_view = QgsProject.instance().mapLayersByName("v2_culvert_view")[0]
        v2_culvert_id = v2_culvert_view.id()
        cul_idx = v2_culvert_view.fields().indexFromName("cul_cross_section_definition_id")

        v2_cross_section_definition = QgsProject.instance().mapLayersByName(
            "v2_cross_section_definition"
        )[0]
        v2_cross_section_definition_id = v2_cross_section_definition.id()

        cross_section_relations = [["1","pipe_xsec",0,v2_pipe_id,v2_cross_section_definition_id,"pipe_cross_section_definition_id"],
        ["2","weir_xsec",0,v2_weir_id,v2_cross_section_definition_id,"weir_cross_section_definition_id"],
        ["3","orf_xsec",0,v2_orifice_id,v2_cross_section_definition_id,"orf_cross_section_definition_id"],
        ["4","cul_xsec",0,v2_culvert_id,v2_cross_section_definition_id,"cul_cross_section_definition_id"]]
        
        for id, name, strength, referencing_layer,referenced_layer,referencing_field in cross_section_relations:
            rel = QgsRelation()
            rel.setReferencingLayer(referencing_layer)
            rel.setReferencedLayer(referenced_layer)
            rel.addFieldPair(referencing_field, "id")
            rel.setId(id)
            rel.setName(name)
            rel.setStrength(strength)
            QgsProject.instance().relationManager().addRelation(rel)

        cfg = dict()
        cfg["OrderByValue"] = True
        cfg["AllowNULL"] = False
        cfg["ShowOpenFormButton"] = False
        cfg["AllowAddFeatures"] = True
        cfg["ShowForm"] = False
        cfg["FilterFields"] = ["shape", "width", "height"]
        cfg["ChainFilters"] = False
        setup = QgsEditorWidgetSetup("RelationReference", cfg)
        
        fields_list = [[v2_weir_view, weir_idx],
                       [v2_pipe_view, pipe_idx],
                       [v2_culvert_view, cul_idx],
                       [v2_orifice_view, orf_idx]]

        for view, idx in fields_list:
            view.setEditorWidgetSetup(idx, setup)

        expression = " id || ' code: ' || code "
        v2_cross_section_definition.setDisplayExpression(expression)

    def manhole_xsec_commit(self):
        v2_manhole_view = QgsProject.instance().mapLayersByName("v2_manhole_view")[0]
        if v2_manhole_view.isEditable() and v2_manhole_view.isModified():
            v2_manhole_view.commitChanges()
            v2_manhole_view.startEditing()

        v2_cross_section_definition = QgsProject.instance().mapLayersByName(
            "v2_cross_section_definition"
        )[0]
        if (
            v2_cross_section_definition.isEditable()
            and v2_cross_section_definition.isModified()
        ):
            v2_cross_section_definition.commitChanges()
            v2_cross_section_definition.startEditing()

    def reactivate_snapping(self):
        connodes_point_locator = iface.mapCanvas().snappingUtils().clearAllLocators()

    def run(self,checked):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback
        if self.first_start == True:
            self.first_start = False
            self.dlg = Edit3DiSchematisationDialog()

        dirname = os.path.dirname(os.path.abspath(__file__))
        sqlfile = os.path.join(dirname, r"efficient_1d_bewerken_sqlite.sql")
        uri = QgsDataSourceUri()
        # show the dialog
        #self.dlg.show()
        # Run the dialog event loop
        #result = self.dlg.exec_()
        if checked:
        # run sql file to add triggers to views
            print('komt hij hier?')
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
            query = open(sqlfile, "r").read()
            conn = sqlite3.connect(sqlite_dir)
            c = conn.cursor()
            c.executescript(query)
            conn.commit()
            c.close()
            conn.close()
        # check if the v2_manhole table is present (not on first load)
            present_layers = []
            for layer in iface.mapCanvas().layers():
                present_layers.append(layer.name())
            if not any("v2_manhole_view" in s for s in present_layers):
                uri.setDataSource("", "v2_manhole_view", "the_geom")
                vlayer = iface.addVectorLayer(uri.uri(), "v2_manhole_view", "spatialite")
                vlayer.startEditing()
            # load v2_1d_boundary_view (which doesnt load by default)
            if not any("v2_1d_boundary_view" in s for s in present_layers):
                uri.setDatabase(sqlite_dir)
                uri.setDataSource("", "v2_1d_boundary_view", "the_geom")
                vlayer = iface.addVectorLayer(
                    uri.uri(), "v2_1d_boundary_view", "spatialite"
                )
                vlayer.startEditing()
            for layer in iface.mapCanvas().layers():
                if layer.type() == QgsMapLayer.VectorLayer:
                    layer.setDataSource(layer.source(), layer.name(), layer.providerType())
                    layer.startEditing()
            iface.mapCanvas().snappingUtils().toggleEnabled()
            self.configure_pipe_form()
            self.configure_manhole_form()
            self.configure_weir_form()
            self.configure_orifice_form()
            self.configure_pumpstation_form()
            self.configure_culvert_form()
            self.configure_1d_bound_form()
            self.configure_channel_form()
    
            self.set_default_values()
            self.set_xsec_relations()
            self.hide_fields()
    
            v2_pipe_view = QgsProject.instance().mapLayersByName("v2_pipe_view")[0]
            v2_orifice_view = QgsProject.instance().mapLayersByName("v2_orifice_view")[0]
            v2_culvert_view = QgsProject.instance().mapLayersByName("v2_culvert_view")[0]
            v2_weir_view = QgsProject.instance().mapLayersByName("v2_weir_view")[0]
            v2_pumpstation_view = QgsProject.instance().mapLayersByName(
                "v2_pumpstation_view"
            )[0]
            v2_1d_boundary_view = QgsProject.instance().mapLayersByName(
                "v2_1d_boundary_view"
            )[0]
            v2_channel = QgsProject.instance().mapLayersByName("v2_channel")[0]
    
            table_list = [v2_pipe_view,v2_orifice_view,v2_culvert_view,v2_weir_view,
                          v2_pumpstation_view,v2_1d_boundary_view,v2_channel]
    
            for table in table_list:
                table.beforeCommitChanges.connect(self.manhole_xsec_commit)
                table.featureAdded.connect(self.reactivate_snapping)
    
            v2_manhole_view = QgsProject.instance().mapLayersByName("v2_manhole_view")[0]
            v2_manhole_view.featureAdded.connect(self.reactivate_snapping)
    
            v2_xsec_def = QgsProject.instance().mapLayersByName(
                "v2_cross_section_definition"
            )[0]
            v2_xsec_def.startEditing()
        else:
            self.remove_field_config()
            for layer in iface.mapCanvas().layers():
                if layer.isEditable():
                    if layer.isModified():
                        layer.commitChanges()
                        iface.vectorLayerTools().stopEditing(layer,False)
                    else: 
                        iface.vectorLayerTools().stopEditing(layer,False)
            v2_xsec_def = QgsProject.instance().mapLayersByName(
                "v2_cross_section_definition"
            )[0]
            iface.vectorLayerTools().stopEditing(v2_xsec_def,False)
