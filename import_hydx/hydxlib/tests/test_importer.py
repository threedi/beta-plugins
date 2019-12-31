# -*- coding: utf-8 -*-
"""Tests for importer.py"""
from hydxlib.importer import import_hydx


def test_import_connection_node_csv_into_hydx_class():
    hydx_path = "hydxlib/tests/example_files_structures_hydx/"
    hydx = import_hydx(hydx_path)
    assert hydx.connection_nodes[1].x_coordinaat == 300


def test_import_connection_csv_into_hydx_class():
    hydx_path = "hydxlib/tests/example_files_structures_hydx/"
    hydx = import_hydx(hydx_path)
    assert hydx.connections[6].identificatieknooppuntofverbinding == "lei13"


def test_import_structure_csv_into_hydx_class():
    hydx_path = "hydxlib/tests/example_files_structures_hydx/"
    hydx = import_hydx(hydx_path)
    assert hydx.structures[7].identificatieknooppuntofverbinding == "ovs84"


def test_import_profile_csv_into_hydx_class():
    hydx_path = "hydxlib/tests/example_files_structures_hydx/"
    hydx = import_hydx(hydx_path)
    assert hydx.profiles[37].breedte_diameterprofiel == "400"
