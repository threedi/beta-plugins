# -*- coding: utf-8 -*-
import logging
from collections import OrderedDict

from import_hydx.hydxlib.sql_models.constants import Constants
from import_hydx.hydxlib.hydx import Profile


logger = logging.getLogger(__name__)

MANHOLE_SHAPE_MAPPING = {
    "RND": Constants.MANHOLE_SHAPE_ROUND,
    "RHK": Constants.MANHOLE_SHAPE_RECTANGLE,
}

# for now assuming "VRL" to be connected
CALCULATION_TYPE_MAPPING = {
    "KNV": Constants.CALCULATION_TYPE_ISOLATED,
    "RES": Constants.CALCULATION_TYPE_CONNECTED,
    "VRL": Constants.CALCULATION_TYPE_CONNECTED,
}

MATERIAL_MAPPING = {
    "BET": Constants.MATERIAL_TYPE_CONCRETE,
    "PVC": Constants.MATERIAL_TYPE_PVC,
    "GRE": Constants.MATERIAL_TYPE_STONEWARE,
    "GIJ": Constants.MATERIAL_TYPE_CAST_IRON,
    "MSW": Constants.MATERIAL_TYPE_BRICKWORK,
    "HPE": Constants.MATERIAL_TYPE_HPE,
    "PIJ": Constants.MATERIAL_TYPE_SHEET_IRON,
    "STL": Constants.MATERIAL_TYPE_STEEL,
}
# NVT temporary (?) on transport
SEWERAGE_TYPE_MAPPING = {
    "GMD": Constants.SEWERAGE_TYPE_COMBINED,
    "HWA": Constants.SEWERAGE_TYPE_STORMWATER,
    "DWA": Constants.SEWERAGE_TYPE_WASTEWATER,
    "NVT": Constants.SEWERAGE_TYPE_TRANSPORT,
}

# for now ignoring CMP and ITP
MANHOLE_INDICATOR_MAPPING = {
    "INS": Constants.MANHOLE_INDICATOR_MANHOLE,
    "UIT": Constants.MANHOLE_INDICATOR_OUTLET,
}

# for now skipping "MVR", "HEU"
SHAPE_MAPPING = {
    "RND": Constants.SHAPE_ROUND,
    "EIV": Constants.SHAPE_EGG,
    "RHK": Constants.SHAPE_RECTANGLE,
    "TAB": Constants.SHAPE_TABULATED_RECTANGLE,
    "TPZ": Constants.SHAPE_TABULATED_TRAPEZIUM,
}

DISCHARGE_COEFFICIENT_MAPPING = {
    "OVS": "afvoercoefficientoverstortdrempel",
    "DRL": "contractiecoefficientdoorlaatprofiel",
}

SURFACE_CLASS_MAPPING = {
    "GVH": Constants.SURFACE_CLASS_GESLOTEN_VERHARDING,
    "OVH": Constants.SURFACE_CLASS_OPEN_VERHARDING,
    "ONV": Constants.SURFACE_CLASS_ONVERHARD,
    "DAK": Constants.SURFACE_CLASS_PAND,
}

SURFACE_INCLINATION_MAPPING = {
    "HEL": Constants.SURFACE_INCLINATION_HELLEND,
    "VLA": Constants.SURFACE_INCLINATION_VLAK,
    "VLU": Constants.SURFACE_INCLINATION_UITGESTREKT,
}


class Threedi:
    def __init__(self):
        pass

    def import_hydx(self, hydx):
        self.connection_nodes = []
        self.manholes = []
        self.connections = []
        self.pumpstations = []
        self.weirs = []
        self.orifices = []
        self.cross_sections = []
        self.pipes = []
        self.impervious_surfaces = []
        self.impervious_surface_maps = []
        self.outlets = []

        for connection_node in hydx.connection_nodes:
            check_if_element_is_created_with_same_code(
                connection_node.identificatieknooppuntofverbinding,
                self.connection_nodes,
                "Connection node",
            )
            self.add_connection_node(connection_node)

        for connection in hydx.connections:
            check_if_element_is_created_with_same_code(
                connection.identificatieknooppuntofverbinding,
                self.connections,
                "Connection",
            )

            linkedprofile = None
            if connection.typeverbinding in ["GSL", "OPL", "ITR", "DRL"]:
                linkedprofiles = [
                    profile
                    for profile in hydx.profiles
                    if profile.identificatieprofieldefinitie
                    == connection.identificatieprofieldefinitie
                ]

                if len(linkedprofiles) > 1:
                    logging.error(
                        "Only first profile is used to create a profile %r for connection %r",
                        connection.identificatieprofieldefinitie,
                        connection.identificatieknooppuntofverbinding,
                    )

                if len(linkedprofiles) == 0:
                    logging.error(
                        "Profile %r does not exist for connection %r",
                        connection.identificatieprofieldefinitie,
                        connection.identificatieknooppuntofverbinding,
                    )
                else:
                    linkedprofile = linkedprofiles[0]

            if connection.typeverbinding in ["GSL", "OPL", "ITR"]:
                if linkedprofile is None:
                    linkedprofile = get_hydx_default_profile()
                    self.add_pipe(connection, linkedprofile)
                else:
                    self.add_pipe(connection, linkedprofile)
            elif connection.typeverbinding in ["PMP", "OVS", "DRL"]:
                linkedstructures = [
                    structure
                    for structure in hydx.structures
                    if structure.identificatieknooppuntofverbinding
                    == connection.identificatieknooppuntofverbinding
                ]

                if len(linkedstructures) > 1:
                    logging.error(
                        "Only first structure information is used to create a structure for connection %r",
                        connection.identificatieknooppuntofverbinding,
                    )

                if len(linkedstructures) == 0:
                    logging.error(
                        "Structure does not exist for connection %r",
                        connection.identificatieknooppuntofverbinding,
                    )
                else:
                    self.add_structure(connection, linkedstructures[0], linkedprofile)
            else:
                logger.warning(
                    'The following "typeverbinding" is not recognized by 3Di exporter: %s',
                    connection.typeverbinding,
                )

        self.generate_cross_sections()

        surface_nr = 1
        for surface in hydx.surfaces:
            self.add_impervious_surface_from_surface(surface, surface_nr)
            surface_nr = surface_nr + 1

        for discharge in hydx.discharges:
            linkedvariations = None
            linkedvariations = [
                variation
                for variation in hydx.variations
                if variation.verloopidentificatie == discharge.verloopidentificatie
            ]
            if len(linkedvariations) == 0 and discharge.afvoerendoppervlak is None:
                logger.warning(
                    "The following discharge object misses information to be used by 3Di exporter: %s",
                    discharge.identificatieknooppuntofverbinding,
                )
            else:
                self.add_impervious_surface_from_discharge(
                    discharge, surface_nr, linkedvariations
                )
                surface_nr = surface_nr + 1

        for structure in hydx.structures:
            if structure.typekunstwerk == "UIT":
                self.add_1d_boundary(structure)

    def add_connection_node(self, hydx_connection_node):
        """Add hydx.connection_node into threedi.connection_node and threedi.manhole"""

        # get connection_nodes attributes
        connection_node = {
            "code": hydx_connection_node.identificatieknooppuntofverbinding,
            "initial_waterlevel": hydx_connection_node.initielewaterstand,
            "geom": point(
                hydx_connection_node.x_coordinaat,
                hydx_connection_node.y_coordinaat,
                28992,
            ),
        }

        self.connection_nodes.append(connection_node)

        # get manhole attributes
        manhole = {
            "code": hydx_connection_node.identificatieknooppuntofverbinding,
            "display_name": hydx_connection_node.identificatierioolput,
            "surface_level": hydx_connection_node.niveaumaaiveld,
            "width": hydx_connection_node.breedte_diameterputbodem,
            "length": hydx_connection_node.lengteputbodem,
            "shape": self.get_mapping_value(
                MANHOLE_SHAPE_MAPPING,
                hydx_connection_node.vormput,
                hydx_connection_node.identificatierioolput,
                name_for_logging="manhole shape",
            ),
            "bottom_level": hydx_connection_node.niveaubinnenonderkantput,
            "calculation_type": self.get_mapping_value(
                CALCULATION_TYPE_MAPPING,
                hydx_connection_node.maaiveldschematisering,
                hydx_connection_node.identificatierioolput,
                name_for_logging="manhole surface schematization",
            ),
            "manhole_indicator": self.get_mapping_value(
                MANHOLE_INDICATOR_MAPPING,
                hydx_connection_node.typeknooppunt,
                hydx_connection_node.identificatierioolput,
                name_for_logging="manhole indicator",
            ),
        }

        self.manholes.append(manhole)

    def add_pipe(self, hydx_connection, hydx_profile=None):
        self.check_if_nodes_of_connection_exists(hydx_connection)
        combined_display_name_string = self.get_connection_display_names_from_manholes(
            hydx_connection
        )
        if hydx_profile.vormprofiel in ('EIV', 'RND', 'RHK'):
            breedte_diameterprofiel = transform_unit_mm_to_m(
                hydx_profile.breedte_diameterprofiel
            )
            hoogteprofiel = transform_unit_mm_to_m(hydx_profile.hoogteprofiel)
        else:
            breedte_diameterprofiel = hydx_profile.tabulatedbreedte
            hoogteprofiel = hydx_profile.tabulatedhoogte

        pipe = {
            "code": hydx_connection.identificatieknooppuntofverbinding,
            "display_name": combined_display_name_string,
            "start_node.code": hydx_connection.identificatieknooppunt1,
            "end_node.code": hydx_connection.identificatieknooppunt2,
            "cross_section_details": {
                "shape": self.get_mapping_value(
                    SHAPE_MAPPING,
                    hydx_profile.vormprofiel,
                    hydx_connection.identificatieprofieldefinitie,
                    name_for_logging="shape of pipe",
                ),
                "width": breedte_diameterprofiel,
                "height": hoogteprofiel,
            },
            "invert_level_start_point": hydx_connection.bobknooppunt1,
            "invert_level_end_point": hydx_connection.bobknooppunt2,
            "original_length": hydx_connection.lengteverbinding,
            "material": self.get_mapping_value(
                MATERIAL_MAPPING,
                hydx_profile.materiaal,
                combined_display_name_string,
                name_for_logging="pipe material",
            ),
            "sewerage_type": self.get_mapping_value(
                SEWERAGE_TYPE_MAPPING,
                hydx_connection.typeinzameling,
                combined_display_name_string,
                name_for_logging="pipe sewer type",
            ),
            "calculation_type": 1,
        }
        self.pipes.append(pipe)

    def add_structure(self, hydx_connection, hydx_structure, hydx_profile=None):
        """Add hydx.structure and hydx.connection into threedi.pumpstation"""
        self.check_if_nodes_of_connection_exists(hydx_connection)
        combined_display_name_string = self.get_connection_display_names_from_manholes(
            hydx_connection
        )

        if hydx_structure.typekunstwerk == "PMP":
            self.add_pumpstation(
                hydx_connection, hydx_structure, combined_display_name_string
            )
        elif hydx_structure.typekunstwerk == "OVS":
            self.add_weir(hydx_connection, hydx_structure, combined_display_name_string)
        elif hydx_structure.typekunstwerk == "DRL":
            if hydx_profile is None:
                hydx_profile = get_hydx_default_profile()
            self.add_orifice(
                hydx_connection,
                hydx_structure,
                hydx_profile,
                combined_display_name_string,
            )

    def add_pumpstation(
        self, hydx_connection, hydx_structure, combined_display_name_string
    ):
        if hydx_structure.aanslagniveaubovenstrooms is not None:
            pumpstation_type = 2
            pumpstation_start_level = hydx_structure.aanslagniveaubovenstrooms
            pumpstation_stop_level = hydx_structure.afslagniveaubovenstrooms
        else:
            pumpstation_type = 1
            pumpstation_start_level = hydx_structure.aanslagniveaubenedenstrooms
            pumpstation_stop_level = hydx_structure.afslagniveaubenedenstrooms

        pumpstation = {
            "code": hydx_connection.identificatieknooppuntofverbinding,
            "display_name": combined_display_name_string,
            "start_node.code": hydx_connection.identificatieknooppunt1,
            "end_node.code": hydx_connection.identificatieknooppunt2,
            "type_": pumpstation_type,
            "start_level": pumpstation_start_level,
            "lower_stop_level": pumpstation_stop_level,
            # upper_stop_level is not supported by hydx
            "upper_stop_level": None,
            "capacity": round(float(hydx_structure.pompcapaciteit) / 3.6, 5),
            "sewerage": True,
        }
        self.pumpstations.append(pumpstation)

    def add_weir(self, hydx_connection, hydx_structure, combined_display_name_string):
        waterlevel_boundary = getattr(hydx_structure, "buitenwaterstand", None)
        if waterlevel_boundary is not None:
            timeseries = "0,{0}\n9999,{0} ".format(waterlevel_boundary)
            boundary = {
                "node.code": hydx_connection.identificatieknooppunt2,
                "timeseries": timeseries,
                "boundary_type": Constants.BOUNDARY_TYPE_WATERLEVEL,
            }
            self.outlets.append(boundary)
        else:
            timeseries = None

        hydx_connection = self.get_discharge_coefficients(
            hydx_connection, hydx_structure
        )

        weir = {
            "code": hydx_connection.identificatieknooppuntofverbinding,
            "display_name": combined_display_name_string,
            "start_node.code": hydx_connection.identificatieknooppunt1,
            "end_node.code": hydx_connection.identificatieknooppunt2,
            "cross_section_details": {
                "shape": Constants.SHAPE_RECTANGLE,
                "width": hydx_structure.breedteoverstortdrempel,
                "height": None,
            },
            "crest_type": Constants.CREST_TYPE_SHARP_CRESTED,
            "crest_level": hydx_structure.niveauoverstortdrempel,
            "discharge_coefficient_positive": hydx_connection.discharge_coefficient_positive,
            "discharge_coefficient_negative": hydx_connection.discharge_coefficient_negative,
            "sewerage": True,
        }
        self.weirs.append(weir)

    def add_orifice(
        self,
        hydx_connection,
        hydx_structure,
        hydx_profile,
        combined_display_name_string,
    ):
        hydx_connection = self.get_discharge_coefficients(
            hydx_connection, hydx_structure
        )
        if hydx_profile.vormprofiel in ('EIV', 'RND', 'RHK'):
            breedte_diameterprofiel = transform_unit_mm_to_m(
                hydx_profile.breedte_diameterprofiel
            )
            hoogteprofiel = transform_unit_mm_to_m(hydx_profile.hoogteprofiel)
        else:
            breedte_diameterprofiel = hydx_profile.tabulatedbreedte
            hoogteprofiel = hydx_profile.tabulatedhoogte

        orifice = {
            "code": hydx_connection.identificatieknooppuntofverbinding,
            "display_name": combined_display_name_string,
            "start_node.code": hydx_connection.identificatieknooppunt1,
            "end_node.code": hydx_connection.identificatieknooppunt2,
            "cross_section_details": {
                "shape": self.get_mapping_value(
                    SHAPE_MAPPING,
                    hydx_profile.vormprofiel,
                    hydx_connection.identificatieknooppuntofverbinding,
                    name_for_logging="shape of orifice",
                ),
                "width": breedte_diameterprofiel,
                "height": hoogteprofiel,
            },
            "discharge_coefficient_positive": hydx_connection.discharge_coefficient_positive,
            "discharge_coefficient_negative": hydx_connection.discharge_coefficient_negative,
            "sewerage": True,
            "crest_type": Constants.CREST_TYPE_SHARP_CRESTED,
            "crest_level": hydx_structure.niveaubinnenonderkantprofiel,
        }

        self.orifices.append(orifice)

    def generate_cross_sections(self):
        cross_sections = {}
        cross_sections["default"] = {
            "width": 1,
            "height": 1,
            "shape": Constants.SHAPE_ROUND,
            "code": "default",
        }

        connections_with_cross_sections = self.weirs + self.orifices + self.pipes
        for connection in connections_with_cross_sections:
            cross_section = connection["cross_section_details"]
            if cross_section["shape"] == Constants.SHAPE_ROUND:
                code = "round_{width}".format(**cross_section)
            elif cross_section["shape"] == Constants.SHAPE_EGG:
                code = "egg_w{width}_h{height}".format(**cross_section)
            elif cross_section["shape"] == Constants.SHAPE_RECTANGLE:
                code = "rectangle_w{width}_open".format(**cross_section)
            elif cross_section["shape"] == Constants.SHAPE_TABULATED_RECTANGLE:
                code = "rectangle_w{width}_h{height}".format(**cross_section)
                cross_section["width"] = "{0}".format(cross_section["width"])
                cross_section["height"] = "{0}".format(cross_section["height"])
            else:
                code = "default"
            # add unique cross_sections to cross_section definition
            if code not in cross_sections:
                cross_sections[code] = cross_section
                cross_sections[code]["code"] = code

            connection["cross_section_code"] = code

        self.cross_sections = cross_sections

    def add_impervious_surface_from_surface(self, hydx_surface, surface_nr):
        surface = {
            "code": str(surface_nr),
            "display_name": hydx_surface.identificatieknooppuntofverbinding,
            "area": hydx_surface.afvoerendoppervlak,
            "surface_class": self.get_mapping_value(
                SURFACE_CLASS_MAPPING,
                hydx_surface.afvoerkenmerken.split("_")[0],
                hydx_surface.identificatieknooppuntofverbinding,
                name_for_logging="surface class",
            ),
            "surface_inclination": self.get_mapping_value(
                SURFACE_INCLINATION_MAPPING,
                hydx_surface.afvoerkenmerken.split("_")[1],
                hydx_surface.identificatieknooppuntofverbinding,
                name_for_logging="surface inclination",
            ),
        }

        self.append_and_map_surface(
            surface, hydx_surface.identificatieknooppuntofverbinding, surface_nr
        )

    def add_impervious_surface_from_discharge(
        self, hydx_discharge, surface_nr, linkedvariations
    ):
        # aanname dat dit altijd gesloten verharding vlak is (niet duidelijk in handleiding)
        # aanname max voor dwf? of average?
        if len(linkedvariations) > 0:
            dwf = max([variation.verloopvolume for variation in linkedvariations])
        else:
            dwf = 0

        if hydx_discharge.afvoerendoppervlak:
            area = hydx_discharge.afvoerendoppervlak
        else:
            area = 0

        surface = {
            "code": str(surface_nr),
            "display_name": hydx_discharge.identificatieknooppuntofverbinding,
            "area": area,
            "surface_class": "gesloten verharding",
            "surface_inclination": "vlak",
            "dry_weather_flow": float(dwf) * 1000,
            "nr_of_inhabitants": hydx_discharge.afvoereenheden,
        }
        self.append_and_map_surface(
            surface, hydx_discharge.identificatieknooppuntofverbinding, surface_nr
        )

    def add_1d_boundary(self, hydx_structure):
        waterlevel_boundary = getattr(hydx_structure, "buitenwaterstand", None)
        if waterlevel_boundary is not None:
            timeseries = "0,{0}\n9999,{0} ".format(waterlevel_boundary)
            boundary = {
                "node.code": hydx_structure.identificatieknooppuntofverbinding,
                "timeseries": timeseries,
                "boundary_type": Constants.BOUNDARY_TYPE_WATERLEVEL,
            }
            self.outlets.append(boundary)

    def append_and_map_surface(
        self, surface, manhole_or_line_id, surface_nr, node_code=None
    ):
        manhole_codes = [manhole["code"] for manhole in self.manholes]
        if manhole_or_line_id in manhole_codes:
            node_code = manhole_or_line_id
        if node_code is None:
            for pipe in self.pipes:
                if manhole_or_line_id == pipe["code"]:
                    node_code = pipe["start_node.code"]
                    break

        if node_code is None:
            logging.error(
                "Connection node %r could not be found for surface %r",
                manhole_or_line_id,
                surface["code"],
            )
            self.impervious_surfaces.append(surface)
            return

        surface_map = {
            "node.code": node_code,
            "imp_surface.code": str(surface_nr),
            "percentage": 100,
        }

        self.impervious_surfaces.append(surface)
        self.impervious_surface_maps.append(surface_map)

    def get_mapping_value(self, mapping, hydx_value, record_code, name_for_logging):
        if hydx_value in mapping:
            return mapping[hydx_value]
        else:
            logging.warning(
                "Unknown %s: %s (code %r)", name_for_logging, hydx_value, record_code
            )
            return None

    def check_if_nodes_of_connection_exists(self, connection):
        connection_code = connection.identificatieknooppuntofverbinding
        code1 = connection.identificatieknooppunt1
        code2 = connection.identificatieknooppunt2

        manh_list = [manhole["code"] for manhole in self.manholes]
        if code1 not in manh_list:
            logging.error(
                "Start connection node %r could not be found for record %r",
                code1,
                connection_code,
            )
        if code2 not in manh_list:
            logging.error(
                "End connection node %r could not be found for record %r",
                code2,
                connection_code,
            )

    def get_connection_display_names_from_manholes(self, connection):
        code1 = connection.identificatieknooppunt1
        code2 = connection.identificatieknooppunt2
        default_code = ""

        manhole_dict = {
            manhole["code"]: manhole["display_name"] for manhole in self.manholes
        }
        display_name1 = manhole_dict.get(code1, default_code)
        display_name2 = manhole_dict.get(code2, default_code)
        combined_display_name_string = display_name1 + "-" + display_name2

        all_connections = self.pumpstations + self.weirs + self.orifices
        nr_connections = [
            element["display_name"]
            for element in all_connections
            if element["display_name"].startswith(combined_display_name_string)
        ]
        connection_number = len(nr_connections) + 1

        combined_display_name_string += "-" + str(connection_number)

        return combined_display_name_string

    def get_discharge_coefficients(self, hydx_connection, hydx_structure):
        if hydx_connection.stromingsrichting not in ["GSL", "1_2", "2_1", "OPN"]:
            hydx_connection.stromingsrichting = "OPN"
            logger.warning(
                'Flow direction is not recognized for %r with record %r, "OPN" is assumed',
                hydx_connection.typeverbinding,
                hydx_connection.identificatieknooppuntofverbinding,
            )

        if (
            hydx_connection.stromingsrichting == "GSL"
            or hydx_connection.stromingsrichting == "2_1"
        ):
            hydx_connection.discharge_coefficient_positive = 0
        elif (
            hydx_connection.stromingsrichting == "OPN"
            or hydx_connection.stromingsrichting == "1_2"
        ):
            hydx_connection.discharge_coefficient_positive = getattr(
                hydx_structure,
                DISCHARGE_COEFFICIENT_MAPPING[hydx_structure.typekunstwerk],
                None,
            )

        if (
            hydx_connection.stromingsrichting == "GSL"
            or hydx_connection.stromingsrichting == "1_2"
        ):
            hydx_connection.discharge_coefficient_negative = 0
        elif (
            hydx_connection.stromingsrichting == "OPN"
            or hydx_connection.stromingsrichting == "2_1"
        ):
            hydx_connection.discharge_coefficient_negative = getattr(
                hydx_structure,
                DISCHARGE_COEFFICIENT_MAPPING[hydx_structure.typekunstwerk],
                None,
            )
        return hydx_connection


def get_hydx_default_profile():
    default_profile = OrderedDict(
        [
            ("PRO_IDE", "DEFAULT"),
            ("PRO_MAT", "PVC"),
            ("PRO_VRM", "RND"),
            ("PRO_BRE", "1000"),
            ("PRO_HGT", "1000"),
            ("TAB_BRE", ""),
            ("TAB_HGT", ""),
            ("ALG_TOE", "default"),
        ]
    )
    return Profile.import_csvline(csvline=default_profile)


def point(x, y, srid_input=28992):

    return x, y, srid_input


def check_if_element_is_created_with_same_code(
    checked_element, created_elements, element_type
):
    added_elements = [element["code"] for element in created_elements]
    if checked_element in added_elements:
        logger.error(
            "Multiple elements %r are created with the same code %r",
            element_type,
            checked_element,
        )


def transform_unit_mm_to_m(value_mm):
    if value_mm is not None:
        return float(value_mm) / float(1000)
    else:
        return None
