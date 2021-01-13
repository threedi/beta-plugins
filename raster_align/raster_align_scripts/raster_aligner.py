# -*- coding: utf-8 -*-
"""
Created on Wed Jan  6 14:37:58 2021

@author: chris.kerklaan
"""

import json
import numpy as np
from .raster import Raster


def align(
    qgistask,
    template_fn,
    raster_to_be_aligned_fn,
    output_file,
    nodata_align=False,
    fill_value=None,
):
    print('Startin aligning', template_fn)
    print("nodata {} \n fill value {}".format(nodata_align, fill_value))
    template = Raster(template_fn)
    raster_to_be_aligned = Raster(raster_to_be_aligned_fn)

    aligned = raster_to_be_aligned.align(
        template, nodata_align=nodata_align, fill_value=fill_value, quiet=False
    )
    aligned.write(output_file, copy=True)

    aligned = None
    template = None
    raster_to_be_aligned = None
    return {"output_file": output_file}


def raster_stats(filename, do_sum=False):
    raster = Raster(filename)
    pixels = raster.shape[0] * raster.shape[1]
    raster_array = raster.array
    data_pixels = np.count_nonzero(~np.isnan(raster_array))
    stat = {
        "rows": raster.shape[0],
        "columns": raster.shape[1],
        "minx": raster.minx,
        "maxx": raster.maxx,
        "miny": raster.miny,
        "maxy": raster.maxy,
        "pixels": pixels,
        "data pixels": data_pixels,
        "nodata pixels": pixels - data_pixels,
        #"sum":np.nansum(raster_array)
    }
    if do_sum:
        stat.update({"sum":np.nansum(raster_array)})
    raster = None
    return stat


def total_raster_stats(
    qgis_task, template_fn, raster_to_be_aligned_fn, output_file, output_stat_file
):
    stats = {}
    for name, fn in [
        ("template", template_fn),
        ("to_be_aligned_raster", raster_to_be_aligned_fn),
        ("output_file", output_file),
    ]:
        stats[name] = raster_stats(fn)

    with open(output_stat_file, "w") as write_file:
        json.dump(stats, write_file, indent=4)

    return stats
