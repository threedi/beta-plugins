from typing import List

import numpy as np
from threedigrid.admin.gridresultadmin import GridH5ResultAdmin
from threedi_result_aggregation import gradients
from threedi_result_aggregation.constants import AGGREGATION_VARIABLES

#
# ga =r'C:\Users\leendert.vanwolfswin\OneDrive - Nelen & Schuurmans\Documents 1\3Di\fuerthen_de - fuerthen_fuerthen (1)\revision 14\results\sim_65948_fuerthen_40_mm_in_een_uur\gridadmin.h5'
# res =r'C:\Users\leendert.vanwolfswin\OneDrive - Nelen & Schuurmans\Documents 1\3Di\fuerthen_de - fuerthen_fuerthen (1)\revision 14\results\sim_65948_fuerthen_40_mm_in_een_uur\results_3di.nc'
#
# gr = GridH5ResultAdmin(ga, res)
#
# print(gr.nodes.dmax.shape)
# print(gr.nodes.timeseries(0, 3600).s1.shape)
#
# print(gradients(gr=gr, flowline_ids=gr.lines.id, gradient_type="bed_level"))

print(AGGREGATION_VARIABLES.short_names())
