from threedigrid.admin.gridresultadmin import GridH5ResultAdmin
import numpy as np
from osgeo import gdal, ogr, osr
try:
    from scipy.ndimage import label, generate_binary_structure, minimum_position, maximum_position
except ModuleNotFoundError:
    from pathlib import Path
    import os
    import sys
    import subprocess
    
    def _get_python_interpreter():
        """Return the path to the python3 interpreter.

        Under linux sys.executable is set to the python3 interpreter used by Qgis.
        However, under Windows/Mac this is not the case and sys.executable refers to the
        Qgis start-up script.
        """
        interpreter = None
        executable = sys.executable
        directory, filename = os.path.split(executable)
        if "python3" in filename.lower():
            interpreter = executable
        elif "qgis" in filename.lower():
            interpreter = os.path.join(directory, "python3.exe")
        else:
            raise EnvironmentError("Unexpected value for sys.executable: %s" % executable)
        assert os.path.exists(interpreter)  # safety check
        return interpreter

    python_interpreter = _get_python_interpreter()
    target_dir = Path(__file__).parent.parent.parent
    process = subprocess.Popen(
        [
            python_interpreter,
            "-m",
            "pip",
            "install",
            "scipy",
            "--target",
            str(target_dir)
        ],
        universal_newlines=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    # The input/output/error stream handling is a bit involved, but it is
    # necessary because of a python bug on windows 7, see
    # https://bugs.python.org/issue3905 .
    i, o, e = (process.stdin, process.stdout, process.stderr)
    i.close()
    result = o.read() + e.read()
    # f = open(os.path.join(OUR_DIR, "external-dependencies/install.log"),"w+")
    f = open("C:\\Users\\leendert.vanwolfswin\\AppData\\Roaming\\QGIS\\QGIS3\\profiles\\default\\python\\plugins\\threedi_leak_detector\\external-dependencies\\install.log","w+")
    f.write(result)
    f.close()
    o.close()
    e.close()
    exit_code = process.wait()
    if exit_code:
        raise RuntimeError("Installing scipy failed")
    from scipy.ndimage import label, generate_binary_structure, minimum_position, maximum_position


# This algorithm calculates the real minimum exchange height (exchange_height_real),
# i.e. the minimum waterlevel required for flow between two nodes to be possible?
# The measure of leakyness is obtained by comparing exchange_height_real to the min. exchange height at the cell border
# (exchange_height_border)
# The cell border is 0% leaky if exchange_height_real <= exchange_height_border
# The cell border is super leaky if exchange_height_real >> exchange_height_border


def read_as_array(raster, bbox, band_nr=1):
    band = raster.GetRasterBand(band_nr)
    gt = raster.GetGeoTransform()
    inv_gt = gdal.InvGeoTransform(gt)
    x0, y0 = gdal.ApplyGeoTransform(inv_gt, float(bbox[0]), float(bbox[1]))
    x1, y1 = gdal.ApplyGeoTransform(inv_gt, float(bbox[2]), float(bbox[3]))
    xmin, ymin = min(x0, x1), min(y0, y1)
    xmax, ymax = max(x0, x1), max(y0, y1)
    arr = band.ReadAsArray(int(xmin), int(ymin), int(xmax - xmin), int(ymax - ymin))
    return arr


def filter_lines_by_node_ids(lines, node_ids):
    boolean_mask = np.sum(np.isin(lines.line_nodes, node_ids), axis=1) > 0
    line_ids = lines.id[boolean_mask]
    result = lines.filter(id__in=line_ids)
    return result


# def get_flow_area_as_array(raster, gr, node_id, direction='N'):
#     this_cell = gr.cells.filter(id__in=[node_id])
#     flowlines = filter_lines_by_node_ids(lines=gr.lines.subset('2D_OPEN_WATER'), node_ids=[node_id])
#     for i in range(0, flowlines.count - 1):
#         x0, y0, x1, y1 = flowlines.line_coords[:, i]
#         if direction == 'N' and abs(x1-x0) < abs(y1-y0) and y1 < y0:
#             other_node = flowlines.line_nodes[i, 0]
#             other_cell = gr.cells.filter(id__eq=int(other_node))
#     return other_node


def flow_domain(raster, gr, line_id):
    """
    Extract the flow domain from a raster as numpy array and
    return the array positions of the start and end node in that raster
    and those of the lowest pixels in the row/column the nodes are in

    :param raster: gdal.Dataset
    :param gr: threedigrid GridResultAdmin
    :param line_id: flowline id
    :return: numpy array of pixels, pixel position [x,y] of node1, pixel position [x,y] of node2
    """

    flowline = gr.lines.filter(id__eq=line_id)

    node1_id = flowline.line_nodes[0, 0]
    node1 = gr.nodes.filter(id__eq=node1_id)
    node1_x = node1.coordinates[0]
    node1_y = node1.coordinates[1]

    node2_id = flowline.line_nodes[0, 1]
    node2 = gr.nodes.filter(id__eq=node2_id)
    node2_x = node2.coordinates[0]
    node2_y = node2.coordinates[1]

    cell1 = gr.cells.filter(id__eq=node1_id)
    cell1_xmin, cell1_ymin, cell1_xmax, cell1_ymax = cell1.cell_coords.squeeze()

    cell2 = gr.cells.filter(id__eq=node2_id)
    cell2_xmin, cell2_ymin, cell2_xmax, cell2_ymax = cell2.cell_coords.squeeze()

    # Determine cell alignment direction
    aligned_horizontally = cell1_xmax == cell2_xmin
    if aligned_horizontally:
        bbox = [float(min(node1_x, node2_x)),
                float(max(cell1_ymin, cell2_ymin)),
                float(max(node1_x, node2_x)),
                float(min(cell1_ymax, cell2_ymax))]
    else:
        bbox = [float(max(cell1_xmin, cell2_xmin)),
                float(min(node1_y, node2_y)),
                float(min(cell1_xmax, cell2_xmax)),
                float(max(node1_y, node2_y))]
    flow_domain_arr = read_as_array(raster=raster, bbox=bbox)

    raster_px_size_x = raster.GetGeoTransform()[1]
    raster_px_size_y = raster.GetGeoTransform()[5]
    origin_x = bbox[0]
    origin_y = bbox[3]
    gt = (origin_x, raster_px_size_x, 0, origin_y, 0, raster_px_size_y)
    inv_gt = gdal.InvGeoTransform(gt)
    node1_array_pos_x, node1_array_pos_y = gdal.ApplyGeoTransform(inv_gt, float(node1_x), float(node1_y))
    node2_array_pos_x, node2_array_pos_y = gdal.ApplyGeoTransform(inv_gt, float(node2_x), float(node2_y))

    # Push node positions into shape of flow_domain_array
    last_row = flow_domain_arr.shape[0] - 1
    last_col = flow_domain_arr.shape[1] - 1
    node1_array_pos_x = int(min(max(0, int(node1_array_pos_x)), last_col))
    node1_array_pos_y = int(min(max(0, int(node1_array_pos_y)), last_row))
    node2_array_pos_x = int(min(max(0, int(node2_array_pos_x)), last_col))
    node2_array_pos_y = int(min(max(0, int(node2_array_pos_y)), last_row))

    # Find minima
    if aligned_horizontally:
        node1_col = flow_domain_arr[:, 0]
        node1_min_pos = (minimum_position(node1_col)[0], 0)
        node2_col = flow_domain_arr[:, last_col]
        node2_min_pos = (minimum_position(node2_col)[0], last_col)
    else:
        node1_row = flow_domain_arr[last_row, :].squeeze()
        node1_min_pos = (last_row, minimum_position(node1_row)[0])
        node2_row = flow_domain_arr[0, :]
        node2_min_pos = (0, minimum_position(node2_row)[0])

    return flow_domain_arr, \
           (node1_array_pos_y, node1_array_pos_x), (node2_array_pos_y, node2_array_pos_x), \
           node1_min_pos, node2_min_pos


def cell_border(raster, gr, line_id):
    """

    :param raster:
    :param gr:
    :param line_id:
    :return: pixels as array, cell border as geometry
    """
    flowline = gr.lines.subset('2D_OPEN_WATER').filter(id__eq=line_id)
    if flowline.line_nodes.shape[0] == 0:
        raise Exception('Input line is not a 2D line')

    line_nodes = flowline.line_nodes.squeeze()

    if line_nodes.shape[0] == 0:
        raise Exception('Input line is not a 2D line')

    node1_id = line_nodes[0]
    node2_id = line_nodes[1]

    cell1 = gr.cells.filter(id__eq=node1_id)
    cell1_xmin, cell1_ymin, cell1_xmax, cell1_ymax = cell1.cell_coords.squeeze()

    cell2 = gr.cells.filter(id__eq=node2_id)
    cell2_xmin, cell2_ymin, cell2_xmax, cell2_ymax = cell2.cell_coords.squeeze()

    pxsize = raster.GetGeoTransform()[1]

    aligned_horizontally = cell1_xmax == cell2_xmin
    if aligned_horizontally:
        x0 = cell1_xmax
        y0 = min(cell1_ymax, cell2_ymax)
        x1 = cell1_xmax
        y1 = max(cell1_ymin, cell2_ymin)
        bbox = [x0 - pxsize, y0, x1 + pxsize, y1]
    else:
        x0 = max(cell1_xmin, cell2_xmin)
        y0 = cell1_ymax
        x1 = min(cell1_xmax, cell2_xmax)
        y1 = cell1_ymax
        bbox = [x0, y0 - pxsize, x1, y1 + pxsize]

    geom = ogr.Geometry(ogr.wkbLineString)
    geom.AddPoint(x0, y0)
    geom.AddPoint(x1, y1)

    cell_border_pixels = read_as_array(raster=raster, bbox=bbox)
    return cell_border_pixels, geom


def cell_heights(dem, gr, line_id, reduce_method):
    flowline = gr.lines.filter(id__eq=line_id)

    line_nodes = flowline.line_nodes.squeeze()

    node1_id = line_nodes[0]
    node2_id = line_nodes[1]

    cell1 = gr.cells.filter(id__eq=node1_id)
    cell2 = gr.cells.filter(id__eq=node2_id)

    cell1_arr = read_as_array(raster=dem, bbox=list(cell1.cell_coords.squeeze()))
    cell2_arr = read_as_array(raster=dem, bbox=list(cell2.cell_coords.squeeze()))

    cell1_height = reduce_method(cell1_arr)
    cell2_height = reduce_method(cell2_arr)

    return cell1_height, cell2_height


def pivot(array_2d, dz, axis):
    """Pivot a 2d array in x or y direction; right or bottom is lifted by dz"""
    shape = array_2d.shape
    indices = np.indices(array_2d.shape)[axis]
    lift_factor = dz/(array_2d.shape[axis]-1)
    lift_array = np.multiply(indices, lift_factor)
    result = np.add(array_2d, lift_array)
    return result


def find_sink(array_2d, start_pos, search_size):
    curr_row, curr_col = start_pos
    last_row = array_2d.shape[0]
    last_col = array_2d.shape[1]

    sink_found = False
    while not sink_found:
        row_idx_from = np.clip(curr_row - search_size, 0, last_row)
        row_idx_to = np.clip(curr_row + search_size + 1, 0, last_row)
        col_idx_from = np.clip(curr_col - search_size, 0, last_col)
        col_idx_to = np.clip(curr_col + search_size + 1, 0, last_col)
        search_area = array_2d[row_idx_from:row_idx_to, col_idx_from:col_idx_to]
        nw_min_pos = minimum_position(search_area)
        former_row, former_col = curr_row, curr_col
        curr_row = nw_min_pos[0] + row_idx_from
        curr_col = nw_min_pos[1] + col_idx_from
        if (former_row, former_col) == (curr_row, curr_col):
            sink_found = True

    return curr_row, curr_col


def exchange_height_border(dem, gr, line_id):
    cell_border_pixels, cell_border_geom = cell_border(raster=dem, gr=gr, line_id=line_id)
    shape = cell_border_pixels.shape
    if shape[0] > shape[1]:  # border is vertical
        axis = 1
    else:
        axis = 0
    result = np.min(np.max(cell_border_pixels, axis=axis))
    return result, cell_border_geom


def obstacle_height(dem, gr, line_id, search_precision, search_structure=generate_binary_structure(2, 2)):
    """

    :param dem:
    :param gr:
    :param line_id:
    :param search_precision:
    :param search_structure:
    :return: estimated obstacle height
    """
    flow_domain_arr, \
    node1_pixel_pos, node2_pixel_pos, \
    node1_min_pos, node2_min_pos = flow_domain(raster=dem, gr=gr, line_id=line_id)

    # let the highest node flow to its sink
    if flow_domain_arr[node1_min_pos] > flow_domain_arr[node2_min_pos]:
        node1_min_pos = find_sink(array_2d=flow_domain_arr, start_pos=node1_min_pos, search_size=2)
    else:
        node2_min_pos = find_sink(array_2d=flow_domain_arr, start_pos=node2_min_pos, search_size=2)

    if node1_min_pos == node2_min_pos:
        return flow_domain_arr[node1_min_pos]

    hmin = np.min(flow_domain_arr)
    hmax = np.max(flow_domain_arr)

    while (hmax - hmin) > search_precision:
        hcurrent = np.mean([hmin, hmax])
        pixels_below_threshold = flow_domain_arr < hcurrent
        labelled_pixels, labelled_pixels_nr_features = label(pixels_below_threshold, structure=search_structure)
        node1_pixel_label = int(labelled_pixels[node1_min_pos])
        node2_pixel_label = int(labelled_pixels[node2_min_pos])
        if node1_pixel_label == node2_pixel_label != 0:  # if true, nodes are connected
            hmax = hcurrent
        else:
            hmin = hcurrent

    return hcurrent


def obstacle_info_to_ogr(dem, gr, line_ids, search_precision, datasource_name, driver_name='Memory'):
    drv = ogr.GetDriverByName(driver_name)
    ds = drv.CreateDataSource(datasource_name)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(int(gr.epsg_code))
    lyr = ds.CreateLayer('obstacle_info', srs, geom_type=ogr.wkbLineString)

    field_defn_line_id = ogr.FieldDefn('line_id', ogr.OFTInteger)
    lyr.CreateField(field_defn_line_id)
    field_defn_3di = ogr.FieldDefn('exchange_height_3di', ogr.OFTReal)
    lyr.CreateField(field_defn_3di)
    field_defn_obstacle = ogr.FieldDefn('obstacle_height_estimate', ogr.OFTReal)
    lyr.CreateField(field_defn_obstacle)

    feature_defn = lyr.GetLayerDefn()

    for line_id in line_ids:
        try:
            exchange_height_3di, geom = exchange_height_border(dem=dem, gr=gr, line_id=line_id)
        except:
            continue
        obstacle_height_estimate = obstacle_height(dem=dem, gr=gr, line_id=line_id, search_precision=search_precision)

        feature = ogr.Feature(feature_defn)
        feature.SetGeometry(geom)

        feature.SetField('exchange_height_3di', float(exchange_height_3di))
        feature.SetField('obstacle_height_estimate', float(obstacle_height_estimate))
        feature.SetField('line_id', line_id)

        lyr.CreateFeature(feature)
        feature = None

    return ds
