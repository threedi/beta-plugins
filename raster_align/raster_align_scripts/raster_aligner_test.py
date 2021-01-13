# -*- coding: utf-8 -*-
"""
Created on Wed Jan  6 14:37:58 2021

@author: chris.kerklaan
"""

import json
import numpy as np
from raster_aligner import align, raster_stats
from raster import Raster

# System imports
import os
import sys
import pathlib

# Third-party imports
import unittest

# globals

DATA_PATH = os.path.join(pathlib.Path(__file__).parents[0], "test-data")
TEMPLATE = os.path.join(DATA_PATH, "template.tif")


class UnitDatabase(unittest.TestCase):
    """ used for both unittests and integrated testing"""

    def test_too_large_raster(self):
        """tests if a too large raster is properly aligned"""

        raster = os.path.join(DATA_PATH, "template_larger.tif")
        align(
            None,
            TEMPLATE,
            raster,
            "/vsimem/output.tif",
            nodata_align=False,
            fill_value=None,
        )

        r = Raster("/vsimem/output.tif")
        r.write(os.path.join(DATA_PATH, "template_larger_fixed.tif"), copy=True)

        align_stats = raster_stats("/vsimem/output.tif")
        template_stats = raster_stats(TEMPLATE)

        for stat, value in template_stats.items():
            if stat in ["data pixels", "nodata pixels", "sum"]:
                continue
            self.assertTrue(
                value == align_stats[stat],
                "{} is unequal template: {}, aligned: {}".format(
                    stat, value, align_stats[stat]
                ),
            )

    def test_too_small_raster(self):
        """tests if a too small raster is properly aligned"""

        raster = os.path.join(DATA_PATH, "template_smaller.tif")
        align(
            None,
            TEMPLATE,
            raster,
            "/vsimem/output.tif",
            nodata_align=False,
            fill_value=None,
        )

        r = Raster("/vsimem/output.tif")
        r.write(os.path.join(DATA_PATH, "template_smaller_fixed.tif"), copy=True)

        align_stats = raster_stats("/vsimem/output.tif")
        template_stats = raster_stats(TEMPLATE)

        for stat, value in template_stats.items():
            if stat in ["data pixels", "nodata pixels", "sum"]:
                continue
            self.assertTrue(
                value == align_stats[stat],
                "{} is unequal template: {}, aligned: {}".format(
                    stat, value, align_stats[stat]
                ),
            )

    def test_raster_w_too_much_nodata(self):
        """tests if a raster with too much nodata is properly aligned"""

        raster = os.path.join(DATA_PATH, "template_w_nodata.tif")
        # print()
        align(
            None,
            TEMPLATE,
            raster,
            "/vsimem/output.tif",
            nodata_align=True,
            fill_value=100,
        )

        r = Raster("/vsimem/output.tif")
        r.write(os.path.join(DATA_PATH, "template_w_nodata_fixed.tif"), copy=True)

        align_stats = raster_stats("/vsimem/output.tif", do_sum=True)
        template_stats = raster_stats(TEMPLATE, do_sum=True)

        for stat, value in template_stats.items():
            if stat == "sum":
                continue
            self.assertTrue(
                value == align_stats[stat],
                "{} is unequal template: {}, aligned: {}".format(
                    stat, value, align_stats[stat]
                ),
            )

        # Check if correct value was added
        self.assertTrue(align_stats["sum"] == 1090)

    def test_raster_w_too_little_nodata(self):
        """tests if a raster with too little is properly aligned"""

        raster = os.path.join(DATA_PATH, "template_wo_nodata.tif")
        align(
            None,
            TEMPLATE,
            raster,
            "/vsimem/output.tif",
            nodata_align=True,
            fill_value=100,
        )

        r = Raster("/vsimem/output.tif")
        r.write(os.path.join(DATA_PATH, "template_wo_nodata_fixed.tif"), copy=True)

        align_stats = raster_stats("/vsimem/output.tif")
        template_stats = raster_stats(TEMPLATE)

        for stat, value in template_stats.items():
            if stat == "sum":
                continue
            self.assertTrue(
                value == align_stats[stat],
                "{} is unequal template: {}, aligned: {}".format(
                    stat, value, align_stats[stat]
                ),
            )


if __name__ == "__main__":
    unittest.main()
