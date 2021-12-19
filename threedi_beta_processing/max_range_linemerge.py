import ogr 
from shapely import wkb
from shapely.ops import linemerge
from operator import itemgetter
from typing import Union, Iterable
import numpy as np

ogr.UseExceptions()

GEOMETRY = 'geometry'
VALUE = 'value'


class Collection:
    """"Contiguous set of linestring geometries for which all values are within max_range
    average of the values for all linestrings"""
    def __init__(self, max_range):
        self.max_range = max_range
        self.geometries = []
        self.values = np.array([], dtype=float)
        self.weights = np.array([], dtype=float)

    def __len__(self):
        return len(self.values)

    def add(self, geometry, value):
        if self.average:
            if max(np.max(self.values), value) - min(np.min(self.values), value) > self.max_range:
                raise ValueError('Adding this value would create a range > max_range')
        self.geometries.append(geometry)
        self.values = np.append(self.values, value)
        self.weights = np.append(self.weights, geometry.length)

    @property
    def average(self):
        """Length-weighted average of values"""
        if np.nansum(self.weights) != 0:
            return np.nansum(self.values * self.weights) / np.nansum(self.weights)
        else:
            return None

    @property
    def linestring(self):
        return linemerge(self.geometries)


def distinct(layer, field_names):
    """Return a set of unique values present in the field"""
    if isinstance(field_names, str):
        field_names = [field_names]
    return set([tuple([feature[field_name] for field_name in field_names]) for feature in layer])


def max_range_linemerge_io(input_filename, input_layername, output_drivername, output_filename, output_layername,
                           merge_attribute, max_range, group_by: Union[str, Iterable] = None):
    # input
    in_ds = ogr.Open(input_filename)
    in_layer = in_ds.GetLayerByName(input_layername)
    geometry_groups = dict()
    value_groups = dict()
    if group_by:
        groups = tuple(distinct(in_layer, group_by))
    else:
        groups = tuple('DUMMY_GROUP_9876543210')
    print(f'groups: {groups}')
    for group in groups:
        geometry_groups[group] = []
        value_groups[group] = []
    for feat in in_layer:
        ogr_geom = feat.GetGeometryRef()
        wkb_geom = ogr_geom.ExportToWkb()
        feat_group = tuple([feat[group_by_field] for group_by_field in group_by])
        geometry_groups[feat_group].append(wkb.loads(wkb_geom))
        value_groups[feat_group].append(feat[merge_attribute])

    # output
    out_driver = ogr.GetDriverByName(output_drivername)
    out_ds = out_driver.CreateDataSource(output_filename)
    srs = in_layer.GetSpatialRef()
    out_layer = out_ds.CreateLayer(output_layername, srs=srs, geom_type=ogr.wkbLineString)
    merge_field_defn = ogr.FieldDefn(merge_attribute, ogr.OFTReal)
    out_layer.CreateField(merge_field_defn)
    if group_by:
        for field in in_layer.schema:
            if field.name in group_by:
                out_layer.CreateField(field)

    # write results to output
    out_layer_defn = out_layer.GetLayerDefn()
    for group in groups:
        for geom, val in max_range_linemerge(geometry_groups[group], value_groups[group], max_range):
            out_feat = ogr.Feature(out_layer_defn)
            out_geom = ogr.CreateGeometryFromWkb(geom.wkb)
            out_feat.SetGeometry(out_geom)
            out_feat[merge_attribute] = val
            if group_by:
                for i, group_by_fieldname in enumerate(group_by):
                    out_feat[group_by_fieldname] = group[i]
            out_layer.CreateFeature(out_feat)
            out_feat = None


def max_range_linemerge(geometries, values, max_range):
    input_lines = [{GEOMETRY: geometry, VALUE: values[i]} for i, geometry in enumerate(geometries)]
    multilinestring = linemerge(geometries)
    linestrings = [linestring for linestring in multilinestring]

    # group the input lines by merged linestring that they belong to
    # sort them within groups by position along line
    input_line_groups = []
    for linestring in linestrings:
        input_line_group = []
        for input_line in input_lines:
            if linestring.contains(input_line['geometry']):
                middle_of_feature = input_line['geometry'].interpolate(0.5, normalized=True)
                input_line['position_along_line'] = linestring.project(middle_of_feature)
                input_line_group.append(input_line)
        input_line_group_sorted = sorted(input_line_group, key=itemgetter('position_along_line'))
        input_line_groups.append(input_line_group_sorted)

    # within each input line group, merge lines by geometry and attribute value
    for input_line_group in input_line_groups:
        collection = Collection(max_range=max_range)
        for input_line in input_line_group:
            try:
                collection.add(input_line[GEOMETRY], input_line[VALUE])
            except ValueError:  # value is too different from average values already in collection
                yield collection.linestring, collection.average
                collection = Collection(max_range=max_range)
                collection.add(input_line[GEOMETRY], input_line[VALUE])
        yield collection.linestring, collection.average


if __name__ == "__main__":
    max_range_linemerge_io(input_filename='C:/3Di/zeeuws-vlaanderen-hulst/T4000.gpkg',
                           input_layername='linear_obstacle',
                           output_drivername='GPKG',
                           output_filename='max_range_linemerge_0_25.gpkg',
                           output_layername='linear_obstacle',
                           merge_attribute='crest_level',
                           max_range=0.25,
                           group_by=['code', 'type', 'material']
                           )
