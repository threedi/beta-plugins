from osgeo import ogr
from shapely import wkt
from pathlib import Path
from typing import Dict, Tuple, List, Union
from rasterize_channel import (
    Channel,
    CrossSectionLocation,
    parse_cross_section_table,
    fill_wedges,
)
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import random

ogr.UseExceptions()


def read_from_geopackage(
        path: Union[Path, str],
        channel_ids: List = None,
        wall_displacement: float = 0
) -> Tuple[Dict[int, Channel], Dict[int, CrossSectionLocation]]:
    path = str(path)

    driver = ogr.GetDriverByName('GPKG')
    data_source = driver.Open(path, 0)  # 0 for read-only mode

    if data_source is None:
        raise ValueError("Could not open GeoPackage")
    else:
        channel_layer = data_source.GetLayerByName("channel")
        field_indices = {field_defn.name: i for i, field_defn in enumerate(channel_layer.schema)}
        channels = dict()
        for feature in channel_layer:
            if channel_ids:
                if feature[field_indices["id"]] not in channel_ids:
                    continue
            geom_wkt = feature.GetGeometryRef().ExportToWkt()
            shapely_geom = wkt.loads(geom_wkt)
            channel = Channel(
                id=feature[field_indices["id"]],
                connection_node_start_id=feature[field_indices["connection_node_start_id"]],
                connection_node_end_id=feature[field_indices["connection_node_end_id"]],
                geometry=shapely_geom
            )
            channels[feature[field_indices["id"]]] = channel

        cross_section_location_layer = data_source.GetLayerByName("cross_section_location")
        field_indices = {field_defn.name: i for i, field_defn in enumerate(cross_section_location_layer.schema)}
        print(field_indices)
        cross_section_locations = dict()
        for feature in cross_section_location_layer:
            if channel_ids:
                if feature[field_indices["channel_id"]] not in channel_ids:
                    continue
            geom_wkt = feature.GetGeometryRef().ExportToWkt()
            shapely_geom = wkt.loads(geom_wkt)
            y, z = parse_cross_section_table(
                table=feature[field_indices["cross_section_table"]],
                cross_section_shape=feature[field_indices["cross_section_shape"]],
                wall_displacement=wall_displacement
            )
            cross_section_location = CrossSectionLocation(
                id=feature[field_indices["id"]],
                reference_level=feature[field_indices["reference_level"]],
                bank_level=feature[field_indices["bank_level"]],
                y_ordinates=y,
                z_ordinates=z,
                geometry=shapely_geom
            )
            channels[feature[field_indices["channel_id"]]].add_cross_section_location(cross_section_location)
            cross_section_locations[field_indices["id"]] = cross_section_location

        # Close the GeoPackage
        data_source = None

        return channels, cross_section_locations


gpkg_path = r"C:\Users\leendert.vanwolfswin\Documents\rasterize_channel test data\MKDC\Mekong operational model.gpkg"
input_channels, input_cross_section_locations = read_from_geopackage(
    path=gpkg_path,
    channel_ids=[135]
)
print(input_channels, input_cross_section_locations)
pixel_size = 30
channels = []
input_channels[135].generate_parallel_offsets()
for input_channel in input_channels.values():
    input_channel.geometry = input_channel.geometry.simplify(pixel_size)
    sub_channels = input_channel.make_valid()
    for sub_channel in sub_channels:
        sub_channel.generate_parallel_offsets()
    channels += sub_channels
fill_wedges(channels)

# plot the triangles
for channel in channels:
    random_color = random.choice(list(mcolors.CSS4_COLORS.keys()))
    for triangle in channel.triangles:
        x, y = triangle.geometry.exterior.xy
        plt.plot(x, y, color=random_color)
        plt.fill(x, y, color=random_color, alpha=0.5)

plt.xlabel('X-axis')
plt.ylabel('Y-axis')
plt.axis('equal')  # Set equal scaling
plt.show()
