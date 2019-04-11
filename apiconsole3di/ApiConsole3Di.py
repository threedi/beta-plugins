# -*- coding: utf-8 -*-
from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from PyQt5.QtGui import QIcon
from PyQt5 import QtGui
from PyQt5.QtWidgets import QAction, QMessageBox
from PyQt5 import QtWidgets
from PyQt5.QtCore import QSettings

# Initialize Qt resources from file resources.py
from .resources import *

# Import the code for the dialog
from .ApiConsole3Di_dialog import ApiConsole3DiDialog
import os.path
import requests
import json
import logging

logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


class ApiConsole3Di:
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
            self.plugin_dir, "i18n", "ApiConsole3Di_{}.qm".format(locale)
        )

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > "4.3.3":
                QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u"&ApiConsole3Di")

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
        return QCoreApplication.translate("ApiConsole3Di", message)

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
            self.iface.addPluginToMenu(self.menu, action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ":/plugins/ApiConsole3Di/icon.png"
        self.add_action(
            icon_path,
            text=self.tr(u"Start 3Di simulation"),
            callback=self.run,
            parent=self.iface.mainWindow(),
        )

        # will be set False in run()
        self.first_start = True

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(self.tr(u"&ApiConsole3Di"), action)
            self.iface.removeToolBarIcon(action)

    @staticmethod
    def uuid_information(
        organisationID,
        ModelSlug,
        simStartTime_string,
        simEndTime_string,
        ScenarioName,
        eMail,
    ):
        basic_info_parameters = {
            "organisation_uuid": organisationID,
            "model_slug": ModelSlug,
            "start": simStartTime_string,
            "end": simEndTime_string,
            "scenario_name": ScenarioName,
            "email": eMail,
        }
        return basic_info_parameters

    @staticmethod
    def constant_rain_information(
        rainIntensity, rainStartTime_string, rainEndTime_string
    ):
        constant_rain_parameters = {
            "rain_events": [
                {
                    "type": "constant",
                    "intensity": rainIntensity,
                    "active_from": rainStartTime_string,
                    "active_till": rainEndTime_string,
                }
            ]
        }
        return constant_rain_parameters

    @staticmethod
    def design_rain_information(rainevent, rainStartTime_string, rainEndTime_string):
        design_rain_parameters = {
            "rain_events": [
                {
                    "type": "design",
                    "number": rainevent + 3,
                    "active_from": rainStartTime_string,
                    "active_till": rainEndTime_string,
                }
            ]
        }
        return design_rain_parameters

    @staticmethod
    def radar_rain_information(
        radarMultiplier, rainStartTime_string, rainEndTime_string, radarStartTime
    ):
        radar_rain_parameters = {
            "rain_events": [
                {
                    "type": "radar",
                    "multiplier": radarMultiplier,
                    "active_from": rainStartTime_string,
                    "active_till": rainEndTime_string,
                    "start": radarStartTime,
                    "layer": "d6c2347d-7bd1-4d9d-a1f6-b342c865516f",
                }
            ]
        }
        return radar_rain_parameters

    @staticmethod
    def store_basic_results(proces_basic_results):
        basic_results_parameters = {
            "store_results": {"process_basic_results": proces_basic_results}
        }
        return basic_results_parameters

    @staticmethod
    def store_damage(
        proces_basic_results,
        Cost_type,
        flood_month,
        inundation_time,
        repair_time_infra,
        repair_time_buildings,
    ):
        damage_results_parameters = {
            "store_results": {
                "process_basic_results": proces_basic_results,
                "damage_estimation": {
                    "cost_type": Cost_type + 1,
                    "flood_month": flood_month + 1,
                    "inundation_period": inundation_time,
                    "repair_time_infrastructure": repair_time_infra,
                    "repair_time_buildings": repair_time_buildings,
                },
            }
        }
        return damage_results_parameters

    def on_damagebox_changed(self, value):
        # Enable fields for damage estimation when applied

        if value == "True":
            for field_name in ["inundationPeriod", "repairTimeBuildings", 
                               "repairTimeInfra", "costType", "floodMonth"]:
                field = getattr(self.dlg, field_name)
                field.setEnabled(1)

        # Disable fields for damage estimation when applied
        if value == "False":
            for field_name in ["inundationPeriod", "repairTimeBuildings", 
                               "repairTimeInfra", "costType", "floodMonth"]:
                field = getattr(self.dlg, field_name)
                field.setDisabled(1)

    def on_raintype_changed(self, value):
        # disable radar and design rain fields when constant rain
        if value == "constant":
            self.dlg.rainIntensity.setEnabled(1)
            self.dlg.rainEvent.setDisabled(1)
            self.dlg.radarMultiplier.setDisabled(1)
            self.dlg.radarStartTime.setDisabled(1)

        # disable radar and constant rain fields when design rain
        if value == "design":
            self.dlg.rainIntensity.setDisabled(1)
            self.dlg.rainEvent.setEnabled(1)
            self.dlg.radarMultiplier.setDisabled(1)
            self.dlg.radarStartTime.setDisabled(1)

        # disable design and constant rain fields when using radar rain
        if value == "radar":
            self.dlg.rainIntensity.setDisabled(1)
            self.dlg.rainEvent.setDisabled(1)
            self.dlg.radarMultiplier.setEnabled(1)
            self.dlg.radarStartTime.setEnabled(1)

    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback
        # specify design rains and rain types
        design_rain = [
            "rainevent 3",
            "rainevent 4",
            "rainevent 5",
            "rainevent 6",
            "rainevent 7",
            "rainevent 8",
            "rainevent 9",
            "rainevent 10",
            "t100 kort",
            "t250 kort",
            "t1000 kort",
            "t100 lang",
            "t250 lang",
            "t1000 lang",
        ]
        rain_options = ["constant", "design", "radar"]

        # specification of results processing options
        proces_basic_results_options = ["True", "False"]
        proces_damage_options = ["False", "True"] 
        cost_types = ["minimum", "average", "maximum"]
        months = [
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ]

        # specification of the API connection
        url = "https://3di.lizard.net/api/v1/calculation/start/"
        headers = {"content-type": "application/json"}

        # specification of the qsettings object
        settings = QSettings("3di", "api")
        # initialize gui
        if self.first_start == True:
            self.first_start = False
            self.dlg = ApiConsole3DiDialog()
            self.dlg.rainEvent.addItems(design_rain)
            self.dlg.processResults.addItems(proces_basic_results_options)
            self.dlg.damageEstimation.addItems(proces_damage_options)
            self.dlg.costType.addItems(cost_types)
            self.dlg.floodMonth.addItems(months)
            self.dlg.password.setEchoMode(QtGui.QLineEdit.Password)
            self.dlg.rainType.addItems(rain_options)
            self.dlg.inundationPeriod.setDisabled(1)
            self.dlg.repairTimeBuildings.setDisabled(1)
            self.dlg.repairTimeInfra.setDisabled(1)
            self.dlg.costType.setDisabled(1)
            self.dlg.floodMonth.setDisabled(1)
            self.dlg.rainEvent.setDisabled(1)
            self.dlg.radarMultiplier.setDisabled(1)
            self.dlg.radarStartTime.setDisabled(1)
            self.dlg.organisationID.setText(settings.value("uuid"))
            self.dlg.modelSlug.setText(settings.value("slug"))
            self.dlg.eMail.setText(settings.value("email"))
            self.dlg.userName.setText(settings.value("username"))

        # alter field activity based on other fields
        self.dlg.damageEstimation.currentTextChanged.connect(self.on_damagebox_changed)
        self.dlg.rainType.currentTextChanged.connect(self.on_raintype_changed)
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        if not result:
            # Cancel was pressed
            return

        # load standard variables:
        organisationID = self.dlg.organisationID.text()
        ModelSlug = self.dlg.modelSlug.text()
        ScenarioName = self.dlg.scenarioName.text()

        # load rain variables:
        selectedLayerIndex = self.dlg.rainType.currentIndex()
        rain_type = rain_options[selectedLayerIndex]
        if rain_type == "constant":
            rainIntensity = float(self.dlg.rainIntensity.text())
        if rain_type == "design":
            rainevent = self.dlg.rainEvent.currentIndex()
        if rain_type == "radar":
            radarMultiplier = int(self.dlg.radarMultiplier.text())
            radarStartTime = self.dlg.radarStartTime.dateTime().toString(
                "yyyy-MM-ddThh:mm"
            )

        # load rain and simulation start/end time
        simStartTime_string = self.dlg.simStartTime.dateTime().toString(
            "yyyy-MM-ddThh:mm"
        )
        simEndTime_string = self.dlg.simEndTime.dateTime().toString("yyyy-MM-ddThh:mm")
        rainStartTime_string = self.dlg.rainStartTime.dateTime().toString(
            "yyyy-MM-ddThh:mm"
        )
        rainEndTime_string = self.dlg.rainEndTime.dateTime().toString(
            "yyyy-MM-ddThh:mm"
        )

        # determine whether to process basic results
        selectedLayerIndex = self.dlg.processResults.currentIndex()
        proces_basic_results = proces_basic_results_options[selectedLayerIndex]

        # characterize damage estimation (if toggled)
        selectedLayerIndex = self.dlg.damageEstimation.currentIndex()
        proces_damage = proces_damage_options[selectedLayerIndex]
        if proces_damage == "True":
            Cost_type = self.dlg.costType.currentIndex()
            flood_month = self.dlg.floodMonth.currentIndex()
            inundation_time = int(self.dlg.inundationPeriod.text())
            repair_time_infra = int(self.dlg.repairTimeInfra.text())
            repair_time_buildings = int(self.dlg.repairTimeBuildings.text())

        # get authorization credentials
        eMail = self.dlg.eMail.text()
        username = self.dlg.userName.text()
        password = self.dlg.password.text()

        # store variables in Qsettings object
        settings.setValue("uuid", organisationID)
        settings.setValue("slug", ModelSlug)
        settings.setValue("email", eMail)
        settings.setValue("username", username)

        # Create api-calls:
        basic_info_parameters = self.uuid_information(
            organisationID,
            ModelSlug,
            simStartTime_string,
            simEndTime_string,
            ScenarioName,
            eMail,
        )

        if rain_type == "constant":
            rain_parameters = self.constant_rain_information(
                rainIntensity, rainStartTime_string, rainEndTime_string
            )
        elif rain_type == "design":
            rain_parameters = self.design_rain_information(
                rainevent, rainStartTime_string, rainEndTime_string
            )
        elif rain_type == "radar":
            rain_parameters = self.radar_rain_information(
                radarMultiplier,
                rainStartTime_string,
                rainEndTime_string,
                radarStartTime,
            )

        if proces_basic_results == "False":
            processing_parameters = {}
        elif proces_basic_results == "True" and proces_damage == "False":
            processing_parameters = self.store_basic_results(proces_basic_results)
        elif proces_basic_results == "True" and proces_damage == "True":
            processing_parameters = self.store_damage(
                proces_basic_results,
                Cost_type,
                flood_month,
                inundation_time,
                repair_time_infra,
                repair_time_buildings,
            )

        api_parameters = json.dumps({**basic_info_parameters, **rain_parameters, **processing_parameters})
        api_parameters = api_parameters.replace('"true"', "true")

        # Perform api call:
        response = requests.post(url, api_parameters, auth=(username, password), headers=headers)
        QMessageBox.information(
            None,
            "status of api-call:",
            "received response: "
            + str(response.json())
            + "\n\nperformed api-call: "
            + str(api_parameters),
        )
