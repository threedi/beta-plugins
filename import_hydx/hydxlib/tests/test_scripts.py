# -*- coding: utf-8 -*-
"""Tests for scripts.py"""
import mock
import pytest
import os

from hydxlib import scripts


@mock.patch("sys.argv", ["program"])
def test_get_parser():
    parser = scripts.get_parser()
    # As a test, we just check one option. That's enough.
    options = parser.parse_args()
    assert options.verbose is False


def test_run_import_export_same(caplog):
    import_type = "hydx"
    export_type = "hydx"
    with pytest.raises(scripts.OptionException):
        scripts.run_import_export(import_type, export_type)


def test_run_import_export_not_available_import(caplog):
    import_type = "this is wrong"
    export_type = "threedi"
    with pytest.raises(scripts.OptionException):
        scripts.run_import_export(import_type, export_type)


def test_run_import_export_not_available_export(caplog):
    import_type = "hydx"
    hydx_path = "hydxlib/tests/example_files_structures_hydx/"
    export_type = "this is wrong"
    with pytest.raises(scripts.OptionException):
        scripts.run_import_export(import_type, export_type, hydx_path)


def test_run_import_export_log_file(caplog):
    import_type = "hydx"
    hydx_path = "hydxlib/tests/example_files_structures_hydx/"
    export_type = "threedi"
    if "TRAVIS" in os.environ:
        # TODO: temporary measure, Reinout will have to investigate proper db env
        # variables. If we run on travis-ci, the default password should be empty.
        TODO_TREEDI_DB_PASSWORD = ""
    else:
        TODO_TREEDI_DB_PASSWORD = "postgres"
    threedi_db_settings = {
        "threedi_dbname": "test_gwsw",
        "threedi_host": "localhost",
        "threedi_user": "postgres",
        "threedi_password": TODO_TREEDI_DB_PASSWORD,
        "threedi_port": 5432,
    }
    finished = scripts.run_import_export(
        import_type, export_type, hydx_path, threedi_db_settings
    )
    assert finished == "method is finished"
