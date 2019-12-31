# -*- coding: utf-8 -*-
import logging
from collections import Counter

logger = logging.getLogger(__name__)


class Generic:
    FIELDS = []

    @classmethod
    def csvheaders(cls):
        return [field["csvheader"] for field in cls.FIELDS]

    @classmethod
    def import_csvline(cls, csvline):
        # AV - function looks like hydroObjectListFromSUFHYD in turtleurbanclasses.py
        instance = cls()

        for field in cls.FIELDS:
            fieldname = field["fieldname"].lower()
            value = csvline[field["csvheader"]]
            datatype = field["type"]

            # set fields to defined data type and load into object
            if value is None or value == "":
                setattr(instance, fieldname, None)
            elif datatype == float and not check_string_to_float(value):
                setattr(instance, fieldname, None)
                logger.error(
                    "%s in %s does not contain a float: %r", fieldname, instance, value
                )
            else:
                setattr(instance, fieldname, datatype(value))
        return instance

    def __str__(self):
        return self.__repr__().strip("<>")


class ConnectionNode(Generic):
    FIELDS = [
        {
            "csvheader": "UNI_IDE",
            "fieldname": "IdentificatieKnooppuntOfVerbinding",
            "type": str,
            "required": True,
        },
        {
            "csvheader": "RST_IDE",
            "fieldname": "IdentificatieRioolstelsel",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "PUT_IDE",
            "fieldname": "IdentificatieRioolput",
            "type": str,
            "required": True,
        },
        {
            "csvheader": "KNP_XCO",
            "fieldname": "X_coordinaat",
            "type": float,
            "required": True,
        },
        {
            "csvheader": "KNP_YCO",
            "fieldname": "Y_coordinaat",
            "type": float,
            "required": True,
        },
        {
            "csvheader": "CMP_IDE",
            "fieldname": "IdentificatieCompartiment",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "MVD_NIV",
            "fieldname": "NiveauMaaiveld",
            "type": float,
            "required": True,
        },
        {
            "csvheader": "MVD_SCH",
            "fieldname": "Maaiveldschematisering",
            "type": str,
            "required": True,
        },
        {
            "csvheader": "WOS_OPP",
            "fieldname": "OppervlakWaterOpStraat",
            "type": float,
            "required": False,
        },
        {
            "csvheader": "KNP_MAT",
            "fieldname": "MateriaalPut",
            "type": str,
            "required": True,
        },
        {"csvheader": "KNP_VRM", "fieldname": "VormPut", "type": str, "required": True},
        {
            "csvheader": "KNP_BOK",
            "fieldname": "NiveauBinnenonderkantPut",
            "type": float,
            "required": True,
        },
        {
            "csvheader": "KNP_BRE",
            "fieldname": "Breedte_diameterPutbodem",
            "type": float,
            "required": True,
        },
        {
            "csvheader": "KNP_LEN",
            "fieldname": "LengtePutbodem",
            "type": float,
            "required": False,
        },
        {
            "csvheader": "KNP_TYP",
            "fieldname": "TypeKnooppunt",
            "type": str,
            "required": True,
        },
        {
            "csvheader": "INI_NIV",
            "fieldname": "InitieleWaterstand",
            "type": float,
            "required": False,
        },
        {
            "csvheader": "STA_OBJ",
            "fieldname": "StatusObject",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "AAN_MVD",
            "fieldname": "AannameMaaiveldhoogte",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "ITO_IDE",
            "fieldname": "IdentificatieDefinitieIT_object",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "ALG_TOE",
            "fieldname": "ToelichtingRegel",
            "type": str,
            "required": False,
        },
    ]

    def __init__(self):
        pass

    def __repr__(self):
        return "<ConnectionNode %s>" % getattr(self, "identificatierioolput", None)


class Connection(Generic):
    FIELDS = [
        {
            "csvheader": "UNI_IDE",
            "fieldname": "IdentificatieKnooppuntOfVerbinding",
            "type": str,
            "required": True,
        },
        {
            "csvheader": "KN1_IDE",
            "fieldname": "IdentificatieKnooppunt1",
            "type": str,
            "required": True,
        },
        {
            "csvheader": "KN2_IDE",
            "fieldname": "IdentificatieKnooppunt2",
            "type": str,
            "required": True,
        },
        {
            "csvheader": "VRB_TYP",
            "fieldname": "TypeVerbinding",
            "type": str,
            "required": True,
        },
        {
            "csvheader": "LEI_IDE",
            "fieldname": "IdentificatieLeiding",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "BOB_KN1",
            "fieldname": "BobKnooppunt1",
            "type": float,
            "required": False,
        },
        {
            "csvheader": "BOB_KN2",
            "fieldname": "BobKnooppunt2",
            "type": float,
            "required": False,
        },
        {
            "csvheader": "STR_RCH",
            "fieldname": "Stromingsrichting",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "VRB_LEN",
            "fieldname": "LengteVerbinding",
            "type": float,
            "required": False,
        },
        {
            "csvheader": "INZ_TYP",
            "fieldname": "TypeInzameling",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "ITO_IDE",
            "fieldname": "IdentificatieDefinitieIT_object",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "PRO_IDE",
            "fieldname": "IdentificatieProfieldefinitie",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "STA_OBJ",
            "fieldname": "StatusObject",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "AAN_BB1",
            "fieldname": "AannameBobKnooppunt1",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "AAN_BB2",
            "fieldname": "AannameBobKnooppunt2",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "AAN_PRO",
            "fieldname": "AannameProfiel",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "INI_NIV",
            "fieldname": "InitieleWaterstand",
            "type": float,
            "required": False,
        },
        {
            "csvheader": "ALG_TOE",
            "fieldname": "ToelichtingRegel",
            "type": str,
            "required": False,
        },
    ]

    def __init__(self):
        pass

    def __repr__(self):
        return "<Connection %s: %s>" % (
            getattr(self, "typeverbinding", None),
            getattr(self, "identificatieknooppuntofverbinding", None),
        )


class Structure(Generic):
    FIELDS = [
        {
            "csvheader": "UNI_IDE",
            "fieldname": "IdentificatieKnooppuntOfVerbinding",
            "type": str,
            "required": True,
        },
        {
            "csvheader": "KWK_TYP",
            "fieldname": "TypeKunstwerk",
            "type": str,
            "required": True,
        },
        {
            "csvheader": "BWS_NIV",
            "fieldname": "Buitenwaterstand",
            "type": float,
            "required": False,
        },
        {
            "csvheader": "PRO_BOK",
            "fieldname": "NiveauBinnenonderkantProfiel",
            "type": float,
            "required": False,
        },
        {
            "csvheader": "DRL_COE",
            "fieldname": "ContractiecoefficientDoorlaatprofiel",
            "type": float,
            "required": False,
        },
        {
            "csvheader": "DRL_CAP",
            "fieldname": "MaximaleCapaciteitDoorlaat",
            "type": float,
            "required": False,
        },
        {
            "csvheader": "OVS_BRE",
            "fieldname": "BreedteOverstortdrempel",
            "type": float,
            "required": False,
        },
        {
            "csvheader": "OVS_NIV",
            "fieldname": "NiveauOverstortdrempel",
            "type": float,
            "required": False,
        },
        {
            "csvheader": "OVS_VOH",
            "fieldname": "VrijeOverstorthoogte",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "OVS_COE",
            "fieldname": "AfvoercoefficientOverstortdrempel",
            "type": float,
            "required": False,
        },
        {
            "csvheader": "PMP_CAP",
            "fieldname": "Pompcapaciteit",
            "type": float,
            "required": False,
        },
        {
            "csvheader": "PMP_AN1",
            "fieldname": "AanslagniveauBenedenstrooms",
            "type": float,
            "required": False,
        },
        {
            "csvheader": "PMP_AF1",
            "fieldname": "AfslagniveauBenedenstrooms",
            "type": float,
            "required": False,
        },
        {
            "csvheader": "PMP_AN2",
            "fieldname": "AanslagniveauBovenstrooms",
            "type": float,
            "required": False,
        },
        {
            "csvheader": "PMP_AF2",
            "fieldname": "AfslagniveauBovenstrooms",
            "type": float,
            "required": False,
        },
        {
            "csvheader": "QDH_NIV",
            "fieldname": "NiveauverschilDebiet_verhangrelatie",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "QDH_DEB",
            "fieldname": "DebietverschilDebiet_verhangrelatie",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "AAN_OVN",
            "fieldname": "AannameNiveauOverstortdrempel",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "AAN_OVB",
            "fieldname": "AannameBreedteOverstortdrempel",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "AAN_CAP",
            "fieldname": "AannamePompcapaciteitPomp",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "AAN_ANS",
            "fieldname": "AannameAanslagniveauPomp",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "AAN_AFS",
            "fieldname": "AannameAfslagniveauPomp",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "ALG_TOE",
            "fieldname": "ToelichtingRegel",
            "type": str,
            "required": False,
        },
    ]

    def __init__(self):
        pass

    def __repr__(self):
        return "<Structure %s: %s>" % (
            getattr(self, "typekunstwerk", None),
            getattr(self, "identificatieknooppuntofverbinding", None),
        )


class Profile(Generic):
    FIELDS = [
        {
            "csvheader": "PRO_IDE",
            "fieldname": "IdentificatieProfieldefinitie",
            "type": str,
            "required": True,
        },
        {
            "csvheader": "PRO_MAT",
            "fieldname": "Materiaal",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "PRO_VRM",
            "fieldname": "VormProfiel",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "PRO_BRE",
            "fieldname": "Breedte_diameterProfiel",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "PRO_HGT",
            "fieldname": "HoogteProfiel",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "TAB_BRE",
            "fieldname": "TabulatedBreedte",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "TAB_HGT",
            "fieldname": "TabulatedHoogte",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "ALG_TOE",
            "fieldname": "ToelichtingRegel",
            "type": str,
            "required": False,
        },
    ]

    def __init__(self):
        pass

    def __repr__(self):
        return "<Profile %s>" % (getattr(self, "identificatieprofieldefinitie", None),)


class Surface(Generic):
    FIELDS = [
        {
            "csvheader": "UNI_IDE",
            "fieldname": "IdentificatieKnooppuntOfVerbinding",
            "type": str,
            "required": True,
        },
        {
            "csvheader": "NSL_STA",
            "fieldname": "NeerslagStation",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "AFV_DEF",
            "fieldname": "AfvoerConcept",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "AFV_IDE",
            "fieldname": "AfvoerKenmerken",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "AFV_OPP",
            "fieldname": "AfvoerendOppervlak",
            "type": float,
            "required": False,
        },
        {
            "csvheader": "ALG_TOE",
            "fieldname": "ToelichtingRegel",
            "type": str,
            "required": False,
        },
    ]

    def __init__(self):
        pass

    def __repr__(self):
        return "<Surface %s>" % (
            getattr(self, "identificatieknooppuntofverbinding", None),
        )


class Discharge(Generic):
    FIELDS = [
        {
            "csvheader": "UNI_IDE",
            "fieldname": "IdentificatieKnooppuntOfVerbinding",
            "type": str,
            "required": True,
        },
        {
            "csvheader": "DEB_TYP",
            "fieldname": "DebietType",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "VER_IDE",
            "fieldname": "VerloopIdentificatie",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "AVV_ENH",
            "fieldname": "AfvoerEenheden",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "AFV_OPP",
            "fieldname": "AfvoerendOppervlak",
            "type": float,
            "required": False,
        },
        {
            "csvheader": "ALG_TOE",
            "fieldname": "ToelichtingRegel",
            "type": str,
            "required": False,
        },
    ]

    def __init__(self):
        pass

    def __repr__(self):
        return "<Discharge %s>" % (
            getattr(self, "identificatieknooppuntofverbinding", None),
        )


class Variation(Generic):
    FIELDS = [
        {
            "csvheader": "VER_IDE",
            "fieldname": "VerloopIdentificatie",
            "type": str,
            "required": True,
        },
        {
            "csvheader": "VER_TYP",
            "fieldname": "VerloopType",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "VER_DAG",
            "fieldname": "VerloopDag",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "VER_VOL",
            "fieldname": "VerloopVolume",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "U00_DAG",
            "fieldname": "Uur0Dag",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "U01_DAG",
            "fieldname": "Uur1Dag",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "U02_DAG",
            "fieldname": "Uur2Dag",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "U03_DAG",
            "fieldname": "Uur3Dag",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "U04_DAG",
            "fieldname": "Uur4Dag",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "U05_DAG",
            "fieldname": "Uur5Dag",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "U06_DAG",
            "fieldname": "Uur6Dag",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "U07_DAG",
            "fieldname": "Uur7Dag",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "U08_DAG",
            "fieldname": "Uur8Dag",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "U09_DAG",
            "fieldname": "Uur9Dag",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "U10_DAG",
            "fieldname": "Uur10Dag",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "U11_DAG",
            "fieldname": "Uur11Dag",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "U12_DAG",
            "fieldname": "Uur12Dag",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "U13_DAG",
            "fieldname": "Uur13Dag",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "U14_DAG",
            "fieldname": "Uur14Dag",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "U15_DAG",
            "fieldname": "Uur15Dag",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "U16_DAG",
            "fieldname": "Uur16Dag",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "U17_DAG",
            "fieldname": "Uur17Dag",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "U18_DAG",
            "fieldname": "Uur18Dag",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "U19_DAG",
            "fieldname": "Uur19Dag",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "U20_DAG",
            "fieldname": "Uur20Dag",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "U21_DAG",
            "fieldname": "Uur21Dag",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "U22_DAG",
            "fieldname": "Uur22Dag",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "U23_DAG",
            "fieldname": "Uur23Dag",
            "type": str,
            "required": False,
        },
        {
            "csvheader": "ALG_TOE",
            "fieldname": "ToelichtingRegel",
            "type": str,
            "required": False,
        },
    ]

    def __init__(self):
        pass

    def __repr__(self):
        return "<Variation %s>" % (getattr(self, "VerloopIdentificatie", None),)


class Meta:
    pass


class Hydx:
    CSVFILES = {
        "Knooppunt.csv": {
            "hydx_class": ConnectionNode,
            "collection_name": "connection_nodes",
        },
        "Kunstwerk.csv": {"hydx_class": Structure, "collection_name": "structures"},
        "Verbinding.csv": {"hydx_class": Connection, "collection_name": "connections"},
        "Profiel.csv": {"hydx_class": Profile, "collection_name": "profiles"},
        "Oppervlak.csv": {"hydx_class": Surface, "collection_name": "surfaces"},
        "Debiet.csv": {"hydx_class": Discharge, "collection_name": "discharges"},
        "Verloop.csv": {"hydx_class": Variation, "collection_name": "variations"},
    }

    def __init__(self):
        self.connection_nodes = []
        self.connections = []
        self.structures = []
        self.profiles = []
        self.surfaces = []
        self.discharges = []
        self.variations = []

    def import_csvfile(self, csvreader, csvfilename):

        csvfile_information = self.CSVFILES[csvfilename]
        check_headers(
            csvreader.fieldnames, csvfile_information["hydx_class"].csvheaders()
        )

        for line in csvreader:
            hydx_class = csvfile_information["hydx_class"]
            hydxelement = hydx_class.import_csvline(csvline=line)
            collection = getattr(self, csvfile_information["collection_name"])
            collection.append(hydxelement)

    def check_import_data(self):
        self._check_on_unique(
            self.connection_nodes, "identificatieknooppuntofverbinding"
        )
        self._check_on_unique(self.connections, "identificatieknooppuntofverbinding")
        self._check_on_unique(self.structures, "identificatieknooppuntofverbinding")
        self._check_on_unique(self.profiles, "identificatieprofieldefinitie")

    def _check_on_unique(self, records, unique_field, remove_double=False):
        values = [m.__dict__[unique_field] for m in records]
        counter = Counter(values)
        doubles = [key for key, count in counter.items() if count > 1]

        for double in doubles:
            logging.error(
                "double values in %s for records with %s %r",
                records[0].__class__.__name__,
                unique_field,
                double,
            )


def check_headers(found, expected):
    """Compares two header columns on extra or missing ones"""
    extra_columns = set(found) - set(expected)
    missing_columns = set(expected) - set(found)
    if extra_columns:
        logger.warning("extra columns found: %s", extra_columns)

    if missing_columns:
        logger.error("missing columns found: %s", missing_columns)


def check_string_to_float(value):
    try:
        float(value)
        return True
    except ValueError:
        return False
