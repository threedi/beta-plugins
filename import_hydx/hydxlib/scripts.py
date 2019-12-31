# -*- coding: utf-8 -*-
"""
A library for the GWSW-hydx exchange format
=============================================================================
Consists of a import and export functionality for currently hydx and threedi.
Author: Arnold van 't Veld - Nelen & Schuurmans
"""
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import logging
import os
import sys
from datetime import datetime

from import_hydx.hydxlib.importer import import_hydx
from import_hydx.hydxlib.exporter import export_threedi

logger = logging.getLogger(__name__)


if "TRAVIS" in os.environ:
    # TODO: temporary measure, Reinout will have to investigate proper db env
    # variables. If we run on travis-ci, the default password should be empty.
    TODO_TREEDI_DB_PASSWORD = ""
else:
    TODO_TREEDI_DB_PASSWORD = "postgres"


class OptionException(Exception):
    pass


def run_import_export(
    import_type, export_type, hydx_path=None, threedi_db_settings=None
):
    """ Run import and export functionality of hydxlib

    Args:
        import_type (str):          import operator ["hydx", "threedi"]
        export_type (str):          export operator ["hydx", "threedi", "json"]
        hydx_path (str):            folder with your hydx *.csv files
        threedi_db_settings (dict): settings of your threedi database

    Returns:
        string: "INFO: method is finished"

    *import_type*
        hydx
        threedi (not yet supported)

    *export_type*
        hydx (not yet supported)
        threedi
        json (not yet supported)

    *hydx_path*
        required when selected operator 'hydx'
        
        relative or absolute path to your hydx location files
        example: hydx_path = "hydxlib\\tests\\example_files_structures_hydx"
    
    *threedi_db_settings*
        required when selected operator 'threedi'

        example:    threedi_db_settings = {
                        "threedi_dbname": "test_gwsw",
                        "threedi_host": "localhost",
                        "threedi_user": "postgres",
                        "threedi_password": TODO_TREEDI_DB_PASSWORD,
                        "threedi_port": 5432,
                    }
        
        threedi_dbname (str):   name of your threedi database, e.g. test_gwsw
        threedi_host (str):     host of your threedi database, e.g. localhost
        threedi_user (str):     username of your threedi database, e.g. postgres
        threedi_password (str): password of your threedi database, e.g. postgres
        threedi_port (int):     port of your threedi database, e.g. 5432

    usage example:
        from hydxlib import run_import_export, write_logging_to_file
        log_relpath = log_relpath = os.path.join(
            os.path.abspath(options.hydx_path), "import_hydx_hydxlib.log"
        )
        write_logging_to_file(hydx_path)
        run_import_export(import_type, export_type, hydx_path, threedi_db_settings)
        
    """
    logger.info("Started exchange of GWSW-hydx at %s", datetime.now())
    logger.info("import type %r ", import_type)
    logger.info("export type %r ", export_type)

    if import_type == export_type:
        raise OptionException(
            "not allowed to use same import and export type %r" % import_type
        )

    if import_type == "hydx":
        hydx = import_hydx(hydx_path)
    else:
        raise OptionException("no available import type %r is selected" % import_type)

    if export_type == "threedi":
        export_threedi(hydx, threedi_db_settings)
    else:
        raise OptionException("no available export type %r is selected" % export_type)

    logger.info("Exchange of GWSW-hydx finished")

    return "method is finished"  # Return value only for testing


def write_logging_to_file(log_relpath):
    """ Add file handler for writing logfile with warning and errors of hydxlib """
    fh = logging.FileHandler(log_relpath, mode="w")
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter("%(levelname)s: %(message)s")
    fh.setFormatter(formatter)
    logging.getLogger("hydxlib").addHandler(fh)


def get_parser():
    """ Return argument parser. """
    parser = ArgumentParser(
        description=__doc__, formatter_class=ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        dest="verbose",
        default=False,
        help="Verbose output",
    )
    parser.add_argument(
        "--import",
        dest="import_type",
        default="hydx",
        choices=["hydx", "threedi"],
        help="select your import operator",
    )
    parser.add_argument(
        "--export",
        dest="export_type",
        default="threedi",
        choices=["hydx", "threedi", "json"],
        help="select your export operator",
    )

    group_hydx = parser.add_argument_group("Import or export a hydx")
    group_hydx.add_argument(
        "--hydx_path",
        default="hydxlib\\tests\\example_files_structures_hydx",
        metavar="HYDX_PATH",
        dest="hydx_path",
        help="Folder with your hydx *.csv files",
    )
    group_threedi = parser.add_argument_group("Import or export a 3di database")
    group_threedi.add_argument(
        "--threedi_dbname",
        metavar="DBNAME",
        default="test_gwsw",
        dest="threedi_dbname",
        help="name of your threedi database",
    )
    group_threedi.add_argument(
        "--threedi_host",
        default="localhost",
        metavar="HOST",
        dest="threedi_host",
        help="host of your threedi database",
    )
    group_threedi.add_argument(
        "--threedi_user",
        default="postgres",
        metavar="USERNAME",
        dest="threedi_user",
        help="username of your threedi database",
    )
    group_threedi.add_argument(
        "--threedi_password",
        default=TODO_TREEDI_DB_PASSWORD,
        metavar="PASSWORD",
        dest="threedi_password",
        help="password of your threedi database",
    )
    group_threedi.add_argument(
        "--threedi_port",
        default=5432,
        type=int,
        metavar="PORT",
        dest="threedi_port",
        help="port of your threedi database",
    )
    return parser


def main():
    """ Call command with args from parser. """
    options = get_parser().parse_args()
    threedi_db_settings = {
        k: vars(options)[k] for k in vars(options) if k.startswith("threedi_")
    }

    if options.verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
    logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")

    # add file handler to logging options
    if options.import_type == "hydx":
        log_relpath = os.path.join(
            os.path.abspath(options.hydx_path), "import_hydx_hydxlib.log"
        )
        write_logging_to_file(log_relpath)
        logger.info("Log file is created in hydx directory: %r", log_relpath)

    try:
        run_import_export(
            options.import_type,
            options.export_type,
            options.hydx_path,
            threedi_db_settings,
        )
    except OptionException as e:
        logger.critical(e)
        sys.exit(1)
