# -*- coding: utf-8 -*-
import logging
import os
import csv

from import_hydx.hydxlib.hydx import Hydx

logger = logging.getLogger(__name__)


def import_hydx(hydx_path):
    """Read set of hydx-csvfiles and return Hydx objects"""
    hydx = Hydx()

    hydxcsvfiles = [
        "Debiet.csv",
        "ItObject.csv",
        "Knooppunt.csv",
        "Kunstwerk.csv",
        "Meta.csv",
        "Nwrw.csv",
        "Oppervlak.csv",
        "Profiel.csv",
        "Verbinding.csv",
        "Verloop.csv",
    ]
    implementedcsvfiles = [
        "Debiet.csv",
        # "ItObject1.csv",
        "Knooppunt.csv",
        "Kunstwerk.csv",
        # "Meta1.csv",
        # "Nwrw1.csv",
        "Oppervlak.csv",
        "Profiel.csv",
        "Verbinding.csv",
        "Verloop.csv",
    ]

    existing_files = []
    for f in hydxcsvfiles:
        csvpath = os.path.join(hydx_path, f)
        if not os.path.isfile(csvpath):
            logger.warning(
                "The following hydx file could not be found: %s",
                os.path.abspath(csvpath),
            )
        elif f not in implementedcsvfiles:
            logger.warning(
                "The following hydx file is currently not implemented in this importer: %s",
                csvpath,
            )
        else:
            existing_files.append(f)

    # TODO check if number of csvfiles loaded is same as number inside meta1.csv

    for f in existing_files:
        csvpath = os.path.join(hydx_path, f)
        with open(csvpath, encoding="utf-8-sig") as csvfile:
            csvreader = csv.DictReader(csvfile, delimiter=";")
            hydx.import_csvfile(csvreader, f)

    hydx.check_import_data()

    return hydx
