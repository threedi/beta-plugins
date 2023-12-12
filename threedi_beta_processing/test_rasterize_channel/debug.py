from osgeo import ogr
from shapely import wkt
from pathlib import Path
from typing import Dict, Tuple, List, Union
from rasterize_channel import (
    Channel,
    CrossSectionLocation,
    parse_cross_section_table,
    fill_wedges,
    simplify,
)
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import random
import numpy as np

ogr.UseExceptions()


def read_from_geopackage(
        path: Union[Path, str],
        channel_ids: List = None,
        wall_displacement: float = 0,
        simplify_tolerance: float = 0
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
            y, z = simplify(y, z, tolerance=simplify_tolerance)
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


gpkg_path = r"C:\Users\leendert.vanwolfswin\Documents\rasterize_channel test data\Olof Geul\geul_oost.gpkg"
# gpkg_path = r"C:\Users\leendert.vanwolfswin\Documents\rasterize_channel test data\MKDC\Mekong operational model.gpkg"
pixel_size = 0.5

input_channels, input_cross_section_locations = read_from_geopackage(
    path=gpkg_path,
    # channel_ids=[181],
    channel_ids=[2000286],
    wall_displacement=pixel_size/4.0,
    simplify_tolerance=0.01
)

channels = []
for input_channel in input_channels.values():
    print(input_channel.id)
    print(input_channel.max_width_at(0))
    input_channel.simplify(pixel_size)
    print("Simplified")
    sub_channels = input_channel.make_valid()
    print(f"Made valid, nr. of sub channels: {len(sub_channels)}")
    for sub_channel in sub_channels:
        print(f"Processing sub_channel {sub_channel.id}")
        sub_channel.generate_parallel_offsets()
        print(f"Generated parallel offsets for sub channel {sub_channel.id}")
    channels += sub_channels
fill_wedges(channels)

for channel in channels:
    print(channel.id)
    print(channel.unique_offsets)
    random_color = random.choice(list(mcolors.CSS4_COLORS.keys()))
    # plot the triangles
    for i, triangle in enumerate(channel.triangles):
        # print(f"triangle {i}")
        x, y = triangle.geometry.exterior.xy
        plt.plot(x, y, color=random_color)
        plt.fill(x, y, color=random_color, alpha=0.5)

    # plot outline
    # x, y = channel.outline.exterior.xy
    # plt.plot(x, y, color=random_color, lw=5)

    # plot the parallel offsets
    for po in channel.parallel_offsets:
        x, y = po.geometry.xy
        x = np.array(x)
        y = np.array(y)
        plt.plot(x, y, color=random_color)
        plt.quiver(x[:-1], y[:-1], x[1:] - x[:-1], y[1:] - y[:-1], scale_units='xy', angles='xy', scale=1, color=random_color)

plt.xlabel('X-axis')
plt.ylabel('Y-axis')
plt.axis('equal')  # Set equal scaling
plt.show()
