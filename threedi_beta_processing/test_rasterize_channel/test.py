import numpy as np
from shapely.geometry import LineString, Point
from shapely import wkt
import pytest

from rasterize_channel import (
    WALL_DISPLACEMENT,
    IndexedPoint,
    Triangle,
    Channel,
    CrossSectionLocation,
    SupportedShape,
    find_wedge_channels,
    # fill_wedges,
    parse_cross_section_table,
)


# Generate test data
def channel_init():
    channel_geom = LineString([[0, 0], [1, 1], [2, 2]])

    channel = Channel(
        geometry=channel_geom,
        connection_node_start_id=1,
        connection_node_end_id=2,
        id=1,
    )
    return channel


def cross_section_location():
    y, z = parse_cross_section_table(
        table="0, 0\n1.0, 2.0\n2.0, 4.0",
        cross_section_shape=SupportedShape.TABULATED_TRAPEZIUM.value
    )

    cross_section_loc = CrossSectionLocation(
        reference_level=10.0,
        bank_level=12.0,
        y_ordinates=y,
        z_ordinates=z,
        geometry=Point(1, 1),
    )
    return cross_section_loc


# Tests
def test_parse_cross_section_table():
    # TABULATED RECTANGLE
    y, z = parse_cross_section_table(
        table="0, 2\n1, 4",
        cross_section_shape=SupportedShape.TABULATED_RECTANGLE.value,
        wall_displacement=WALL_DISPLACEMENT
    )
    assert np.all(y == np.array([0, 1, 1 + WALL_DISPLACEMENT, 3, 3 + WALL_DISPLACEMENT, 4]))
    assert np.all(z == np.array([1, 1, 0, 0, 1, 1]))

    # TABULATED TRAPEZIUM
    y, z = parse_cross_section_table(
        table="0, 2\n1, 4",
        cross_section_shape=SupportedShape.TABULATED_TRAPEZIUM.value,
        wall_displacement=WALL_DISPLACEMENT
    )
    assert np.all(y == np.array([0, 1, 3, 4]))
    assert np.all(z == np.array([1, 0, 0, 1]))

    # TABULATED TRAPEZIUM WITH THREE ROWS
    y, z = parse_cross_section_table(
        table="0, 10.0\n1.0, 20.0\n2.0, 40.0",
        cross_section_shape=SupportedShape.TABULATED_TRAPEZIUM.value
    )
    assert np.all(y == np.array([0, 10, 15, 25, 30, 40]))
    assert np.all(z == np.array([2, 1, 0, 0, 1, 2]))

    # TABULATED TRAPEZIUM WITH LOWEST WIDTH = 0
    y, z = parse_cross_section_table(
        table="0, 0\n1, 4",
        cross_section_shape=SupportedShape.TABULATED_TRAPEZIUM.value,
        wall_displacement=WALL_DISPLACEMENT
    )
    assert np.all(y == np.array([0, 2, 4]))
    assert np.all(z == np.array([1, 0, 1]))

    # TABULATED TRAPEZIUM WITH VERTICAL WALL
    y, z = parse_cross_section_table(
        table="0, 0\n"
              "0.434, 6.823\n"
              "0.867, 8.975\n"
              "1.301, 9.995\n"
              "1.734, 11.273\n"
              "2.168, 11.644\n"
              "2.601, 11.644\n"
              "3.035, 42.656",
        cross_section_shape=SupportedShape.TABULATED_TRAPEZIUM.value,
        wall_displacement=WALL_DISPLACEMENT
    )
    assert np.allclose(
        y,
        [
            0., 15.506, 15.506 + WALL_DISPLACEMENT, 15.6915, 16.3305, 16.8405, 17.9165, 21.328, 24.7395, 25.8155,
            26.3255,
            26.9645, 27.15, 27.15 + WALL_DISPLACEMENT, 42.656
        ]
    )
    assert np.allclose(
        z, [3.035, 2.601, 2.168, 1.734, 1.301, 0.867, 0.434, 0., 0.434, 0.867, 1.301, 1.734, 2.168, 2.601, 3.035]
    )

    # TABULATED RECTANGLE which describes a rectangle
    # 0.0, 1.0
    # 0.5, 1.0
    y, z = parse_cross_section_table(
        table="0.0, 1.0\n0.5, 1.0",
        cross_section_shape=SupportedShape.TABULATED_RECTANGLE.value,
        wall_displacement=WALL_DISPLACEMENT
    )
    print(y)
    print(z)

    # YZ
    y, z = parse_cross_section_table(
        table="0, 3\n2, 1\n4, 0\n8, 4",
        cross_section_shape=SupportedShape.YZ.value,
        wall_displacement=WALL_DISPLACEMENT
    )
    assert np.all(y == np.array([0, 2, 4, 8]))
    assert np.all(z == np.array([3, 1, 0, 4]))

    # Invalid shape
    with pytest.raises(ValueError):
        y, z = parse_cross_section_table(
            table="0, 3\n2, 1\n4, 0\n8, 4",
            cross_section_shape=1,
            wall_displacement=WALL_DISPLACEMENT
        )


def test_indexed_point():
    point = IndexedPoint(3.4, 2.4, np.float64(48.3), index=3)
    assert point.index == 3
    assert point.x == 3.4
    assert point.y == 2.4
    assert point.z == 48.3


def test_triangle():
    point_coords = {0: (0, 0), 1: (1, 1), 2: (2, 0)}
    indexed_points = [IndexedPoint(val, index=key) for key, val in point_coords.items()]
    tri = Triangle(indexed_points)
    assert tri.geometry.wkt == "POLYGON ((0 0, 1 1, 2 0, 0 0))"
    line_1 = LineString(
        [
            Point(
                -10,
                -10,
            ),
            Point(
                10,
                10,
            ),
        ]
    )
    line_2 = LineString(
        [
            Point(
                -8,
                -10,
            ),
            Point(
                12,
                10,
            ),
        ]
    )
    assert tri.is_between(line_1, line_2)
    line_2 = LineString(
        [
            Point(
                -9,
                -10,
            ),
            Point(
                11,
                10,
            ),
        ]
    )
    assert not tri.is_between(line_1, line_2)
    line_2 = LineString(
        [
            Point(
                300,
                400,
            ),
            Point(
                310,
                410,
            ),
        ]
    )
    assert not tri.is_between(line_1, line_2)


def test_find_wedge_channels():
    # channel_1: last segment pointing north (azimuth = 0)
    channel_1 = Channel(
        geometry=LineString([Point(20, -100), Point(0, -50), Point(0, 0)]),
        connection_node_start_id=1,
        connection_node_end_id=2,
        id=1,
    )
    xsec = cross_section_location()
    xsec.geometry = Point(0, -50)
    channel_1.add_cross_section_location(xsec)
    assert channel_1.azimuth_at(connection_node_id=2) == 180

    channel_2 = Channel(
        geometry=LineString([Point(0, 0), Point(10, 50), Point(10, 100)]),
        connection_node_start_id=2,
        connection_node_end_id=3,
        id=2,
    )
    xsec = cross_section_location()
    xsec.geometry = Point(10, 50)
    channel_2.add_cross_section_location(xsec)
    assert round(channel_2.azimuth_at(connection_node_id=2), 2) == 11.31

    channel_3 = Channel(
        geometry=LineString([Point(0, 0), Point(50, 0), Point(100, 10)]),
        connection_node_start_id=2,
        connection_node_end_id=4,
        id=3,
    )
    xsec = cross_section_location()
    xsec.geometry = Point(50, 0)
    channel_3.add_cross_section_location(xsec)
    assert channel_3.azimuth_at(connection_node_id=2) == 90

    wedge_channels = find_wedge_channels(
        [channel_1, channel_2, channel_3], connection_node_id=2
    )
    for chn in wedge_channels:
        print(chn.__dict__)
    assert wedge_channels[0].connection_node_start_id == 2
    assert wedge_channels[1].connection_node_end_id == 2
    return wedge_channels


def test_fill_wedge():
    channel_1, channel_2 = test_find_wedge_channels()
    channel_1.generate_parallel_offsets()
    channel_2.generate_parallel_offsets()

    # print("channel 1 triangles:")
    # print(channel_1.as_query())
    # print("channel 2 triangles:")
    # print(channel_2.as_query())

    channel_1.fill_wedge(channel_2)

    # print("Wedge:")
    # tri_queries = [f"SELECT ST_GeomFromText('{tri.geometry.wkt}') as geom" for tri in channel_1._wedge_fill_triangles]
    # print("\nUNION\n".join(tri_queries))
    # [print(tri.geometry.wkb) for tri in channel_1._wedge_fill_triangles]
    assert len(channel_1._wedge_fill_triangles) == 3
    assert channel_1. \
           _wedge_fill_triangles[0]. \
           geometry. \
           wkb == b"\x01\x03\x00\x00\x80\x01\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\xf0\xbf\x00\x00\x00" \
                  b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00&@\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00" \
                  b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00$@\xa2\xd3\xa5\xb9\xea`\xef\xbf\x1cvQaU\x1a\xc9?\x00\x00" \
                  b"\x00\x00\x00\x00&@\x00\x00\x00\x00\x00\x00\xf0\xbf\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00" \
                  b"\x00\x00\x00&@"
    assert channel_1. \
           _wedge_fill_triangles[1]. \
           geometry. \
           wkb == b"\x01\x03\x00\x00\x80\x01\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\xf0\xbf\x00\x00\x00" \
                  b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00&@\xa2\xd3\xa5\xb9\xea`\xef\xbf\x1cvQaU\x1a\xc9?\x00" \
                  b"\x00\x00\x00\x00\x00&@\x00\x00\x00\x00\x00\x00\x00\xc0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00" \
                  b"\x00\x00\x00\x00(@\x00\x00\x00\x00\x00\x00\xf0\xbf\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00" \
                  b"\x00\x00\x00&@"
    assert channel_1. \
           _wedge_fill_triangles[2]. \
           geometry. \
           wkb == b"\x01\x03\x00\x00\x80\x01\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xc0\x00\x00\x00" \
                  b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00(" \
                  b"@\xa2\xd3\xa5\xb9\xea`\xef\xbf\x1cvQaU\x1a\xc9?\x00\x00\x00\x00\x00\x00&@\xa2\xd3\xa5\xb9\xea" \
                  b"`\xff\xbf\x1cvQaU\x1a\xd9?\x00\x00\x00\x00\x00\x00(" \
                  b"@\x00\x00\x00\x00\x00\x00\x00\xc0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00(@"
    # assert len(channel_1._wedge_fill_triangles) == 3
    # assert len(channel_2._wedge_fill_triangles) == 0
    # assert (
    #     channel_1._wedge_fill_triangles[0].geometry.wkt
    #     == "POLYGON Z ((0 0 0, -0.9805806756909201 0.196116135138184 1, -1 0 1, 0 0 0))"
    # )
    # assert (
    #     channel_1._wedge_fill_triangles[1].geometry.wkt
    #     == "POLYGON Z ((-1 0 1, -0.9805806756909201 0.196116135138184 1, -1.96116135138184 0.3922322702763681 2, -1 0 1))"
    # )
    # assert (
    #     channel_1._wedge_fill_triangles[2].geometry.wkt
    #     == "POLYGON Z ((-1 0 1, -1.96116135138184 0.3922322702763681 2, -2 0 2, -1 0 1))"
    # )


def test_cross_section_location_z_at():
    xsec = cross_section_location()
    assert xsec.z_at(0.0) == 10 + 2.0
    assert xsec.z_at(1.0) == 10 + 1.0
    assert xsec.z_at(2.0) == 10 + 0.0
    assert xsec.z_at(3.5) == 10 + 1.5
    assert xsec.z_at(5.0) == 10 + 2.0


def test_cross_section_location_thalweg_y():
    y, z = parse_cross_section_table(
        table="0, 10.0\n1.0, 20.0\n2.0, 40.0",
        cross_section_shape=SupportedShape.TABULATED_TRAPEZIUM.value
    )

    cross_section_loc = CrossSectionLocation(
        reference_level=10.0,
        bank_level=12.0,
        y_ordinates=y,
        z_ordinates=z,
        geometry=Point(0, 0),
    )
    assert cross_section_loc.thalweg_y == 20.0


def test_channel_vertex_positions():
    channel = channel_init()
    vp = channel.vertex_positions
    assert (vp == np.array([0, 0.5, 1]) * channel.geometry.length).all()
    assert len(vp) == 3


def test_channel_properties():
    channel = channel_init()
    xsec = cross_section_location()
    channel.add_cross_section_location(xsec)

    y, z = parse_cross_section_table(
        table="0, 10.0\n1.0, 20.0\n2.0, 40.0",
        cross_section_shape=SupportedShape.TABULATED_TRAPEZIUM.value
    )

    cross_section_loc = CrossSectionLocation(
        reference_level=10.0,
        bank_level=12.0,
        y_ordinates=y,
        z_ordinates=z,
        geometry=Point(0, 0),
    )

    channel.add_cross_section_location(cross_section_loc)

    y, z = parse_cross_section_table(
        table="0, 0.1\n1.0, 0.2\n2.0, 0.4",
        cross_section_shape=SupportedShape.TABULATED_TRAPEZIUM.value
    )

    cross_section_loc = CrossSectionLocation(
        reference_level=10.0,
        bank_level=12.0,
        y_ordinates=y,
        z_ordinates=z,
        geometry=Point(2, 2),
    )

    channel.add_cross_section_location(cross_section_loc)

    assert np.all(channel.max_widths == np.array([40.0, 4.0, 0.4]))
    assert np.allclose(channel.unique_y_ordinates, np.array(
        [-20.00, -10.00, -5.00, -2.00, -1.00, -0.20, -0.10, -0.05, 0.00, 0.05, 0.10, 0.20, 1.00, 2.00, 5.00, 10.00,
         20.00]
    )
                       )
    assert np.all(channel.cross_section_location_positions == np.array([0, 0.5, 1]) * channel.geometry.length)


def test_channel_outline():
    # Straight channel with 1 symmetrical cross-section
    channel = channel_init()
    xsec = cross_section_location()
    channel.add_cross_section_location(xsec)

    assert round(channel.outline.area, 10) == round(channel.geometry.buffer(2).area, 10)

    # Straight channel with 1 asymmetrical YZ.value cross-section
    channel = channel_init()
    y, z = parse_cross_section_table(
        table="0, 3\n1.0, 2\n2.0, 0\n3.0, 3",
        cross_section_shape=SupportedShape.YZ.value
    )

    cross_section_loc = CrossSectionLocation(
        reference_level=10.0,
        bank_level=12.0,
        y_ordinates=y,
        z_ordinates=z,
        geometry=Point(0, 0),
    )

    channel.add_cross_section_location(cross_section_loc)

    assert channel.outline.wkb == \
           b"\x01\x03\x00\x00\x00\x01\x00\x00\x00E\x00\x00\x00\xafo\x87v\xbe\x04\xe0\xbf\xe9\x0c=\xa1B:\xf2\xbf)<\xe7I" \
           b"\x94\xad\xe4\xbf\x91\xb6YB\xca\xe1\xf1\xbf(\xd5_\xd6S?\xe9\xbfq\xd3tgIO\xf1\xbf\xf0\x9cB0\xb9\xae\xed\xbf" \
           b"\x01\x1b\xc6A)\x84\xf0\xbfJk\xa2\x8ej\xf8\xf0\xbf\xa4~\x017\xbd\x04\xef\xbf\x88\x9d\xe2\x04\x94\xfd\xf2" \
           b"\xbf\x90TV\n\xca\x98\xec\xbfS\xa5f\xf5\xdd\xe1\xf4\xbf\xfe\x04`mq\xca\xe9\xbf\xcc;\x7ff\x9e\xa0\xf6\xbf" \
           b"\xce;\x7ff\x9e\xa0\xe6\xbfd\xa0\xef\xe9\x875\xf8\xbf\xdb\x0eN\x84\x1d#\xe3\xbf.\xc8j8\xb4\x9c\xf9\xbf\x8c" \
           b"\xfe\x8bF\x13\xb5\xde\xbf7]\xc0\xce\xad\xd2\xfa\xbf\x905\x8bmm\xa0\xd6\xbf\xe7\xb8\x05ux\xd4\xfb\xbf\x98" \
           b"\x84\r'k8\xcc\xbfWq\xb4\x9a\x98\x9f\xfc\xbf\xf4\xca\x04\x7f\xab\xf5\xb4\xbfwT\x99u\x192\xfd\xbf\xd8\xf9" \
           b"\x7f\xc9\xa10\xaf?\xcf\xaa|\xd4\x91\x8a\xfd\xbfk0\xdf\xbf\x7fo\xca?\xf3\xce\x9f\x99'\xa8\xfd\xbf\xc9;\x7ff" \
           b"\x9e\xa0\xd6?\xcf\xaa|\xd4\x91\x8a\xfd\xbf\xaeo\x87v\xbe\x04\xe0?wT\x99u\x192\xfd\xbf+<\xe7I\x94\xad\xe4?Wq" \
           b"\xb4\x9a\x98\x9f\xfc\xbf'\xd5_\xd6S?\xe9?\xe8\xb8\x05ux\xd4\xfb\xbf\xef\x9cB0\xb9\xae\xed?8]\xc0\xce\xad" \
           b"\xd2\xfa\xbfIk\xa2\x8ej\xf8\xf0?/\xc8j8\xb4\x9c\xf9\xbf\x88\x9d\xe2\x04\x94\xfd\xf2?e\xa0\xef\xe9\x875\xf8" \
           b"\xbfR\xa5f\xf5\xdd\xe1\xf4?\xcd;\x7ff\x9e\xa0\xf6\xbf\xcc;\x7ff\x9e\xa0\xf6?4\xef\xfc\x99y\x82\xda\xbf\xe6" \
           b"\x9d?3OP\x03@f\x88\x013\xc3\xbe\xe2?\xe6\x9d?3OP\x0b@S\xb52\x15D<\xe6?1\xd0\xf7\xf4\xc3\x1a\x0c@\xee\xc4:" \
           b"\xf6\xd7\x04\xea?\x17d5\x1cZ\xce\x0c@k)\xbb\xe2*\x0f\xee?\x9c.`\xe7Vi\r@\x84\xb1\xdeg\xa3(\xf1?t\xdc\x82:<" \
           b"\xea\r@j\x15\xd0\x14V`\xf3?\xac8ZM\xccO\x0e@\xe8a\x0c\xdb5\xa9\xf5?<\xaa\xcc\xba\x0c\x99\x0e@*H\xbc\xc4\xa0" \
           b"\xfd\xf7?hU>\xeaH\xc5\x0e@\x0c1`f\xd8W\xfa?z\xe7\xcf\xcc\x13\xd4\x0e@\xee\x19\x04\x08\x10\xb2\xfc?hU>\xeaH" \
           b"\xc5\x0e@/\x00\xb4\xf1z\x06\xff?<\xaa\xcc\xba\x0c\x99\x0e@V&\xf8[\xad\xa7\x00@\xac8ZM\xccO\x0e@J\xd8p\xb2" \
           b"\x86\xc3\x01@t\xdc\x82:<\xea\r@\xb2f\xb1\xad\r\xd4\x02@\x9c.`\xe7Vi\r@\xd0\x7f\xd1h\xa2\xd6\x03@\x18d5\x1cZ" \
           b"\xce\x0c@\xb7\x83\x13a\xc7\xc8\x04@2\xd0\xf7\xf4\xc3\x1a\x0c@\xf2\xce\x9f\x99'\xa8\x05@\xe7\x9d?3OP\x0b@>" \
           b"\x01X[\x9cr\x06@\xacR\xb3\xfa\xeep\n@$\x95\x95\x822&\x07@\xc5Nq\x02\xca~\t@\xa8_\xc0M/\xc1\x07@\xa65QG5|" \
           b"\x08@\x80\r\xe3\xa0\x14B\x08@>\xa7\x10L\xaek\x07@\xb8i\xba\xb3\xa4\xa7\x08@L\xf5\x97\xf5\xd4O\x06@H\xdb,!" \
           b"\xe5\xf0\x08@\x0c\xcfy\x12e+\x05@t\x86\x9eP!\x1d\t@\xec\xdb\xa1\x9d/\x01\x04@\x86\x1803\xec+\t@z\xe7\xcf" \
           b"\xcc\x13\xd4\x02@t\x86\x9eP!\x1d\t@\x08\xf3\xfd\xfb\xf7\xa6\x01@H\xdb,!\xe5\xf0\x08@\xe9\xff%\x87\xc2|" \
           b"\x00@\xb8i\xba\xb3\xa4\xa7\x08@R\xb3\x0fH\xa5\xb0\xfe?\x80\r\xe3\xa0\x14B\x08@oO\x1e\x9b\xf2x\xfc?\xa9_" \
           b"\xc0M/\xc1\x07@\x9e2\x9d\xa4\xe4W\xfa?$\x95\x95\x822&\x07@^\x00].\xbbR\xf8??\x01X[\x9cr\x06@\x94\xf8" \
           b"\xd8=qn\xf6?\xf4\xce\x9f\x99'\xa8\x05@\x1ab\xc0\xcc\xb0\xaf\xf4?\xe7\x9d?3OP\xfb?d\x88\x013\xc3\xbe\xd2?" \
           b"\xce;\x7ff\x9e\xa0\xe6?\xce;\x7ff\x9e\xa0\xe6\xbf\xdb\x0eN\x84\x1d#\xe3?\xfa\x04`mq\xca\xe9\xbf\x90\xfe" \
           b"\x8bF\x13\xb5\xde?\x8eTV\n\xca\x98\xec\xbf\x905\x8bmm\xa0\xd6?\xa2~\x017\xbd\x04\xef\xbf\x94\x84\r'k8\xcc?" \
           b"\x01\x1b\xc6A)\x84\xf0\xbf\xf0\xca\x04\x7f\xab\xf5\xb4?q\xd3tgIO\xf1\xbf\x10\xfa\x7f\xc9\xa10\xaf\xbf\x91" \
           b"\xb6YB\xca\xe1\xf1\xbfn0\xdf\xbf\x7fo\xca\xbf\xe9\x0c=\xa1B:\xf2\xbf\xca;\x7ff\x9e\xa0\xd6\xbf\r1`f\xd8W" \
           b"\xf2\xbf\xafo\x87v\xbe\x04\xe0\xbf\xe9\x0c=\xa1B:\xf2\xbf"

    # Straight channel with 2 YZ.value cross-sections that are assymetrical in opposite directions
    channel = channel_init()
    y, z = parse_cross_section_table(
        table="0, 3\n1.0, 2\n2.0, 0\n3.0, 3",
        cross_section_shape=SupportedShape.YZ.value
    )

    cross_section_loc = CrossSectionLocation(
        reference_level=10.0,
        bank_level=12.0,
        y_ordinates=y,
        z_ordinates=z,
        geometry=Point(0, 0),
    )

    channel.add_cross_section_location(cross_section_loc)

    y, z = parse_cross_section_table(
        table="0, 3\n1.0, 0\n2.0, 1.0\n3.0, 3",
        cross_section_shape=SupportedShape.YZ.value
    )

    cross_section_loc = CrossSectionLocation(
        reference_level=10.0,
        bank_level=12.0,
        y_ordinates=y,
        z_ordinates=z,
        geometry=Point(2, 2),
    )

    channel.add_cross_section_location(cross_section_loc)

    assert channel.outline.wkb == \
           b"\x01\x03\x00\x00\x00\x01\x00\x00\x00E\x00\x00\x00\xafo\x87v\xbe\x04\xe0\xbf\xe9\x0c=\xa1B:\xf2\xbf" \
           b")<\xe7I\x94\xad\xe4\xbf\x91\xb6YB\xca\xe1\xf1\xbf(" \
           b"\xd5_\xd6S?\xe9\xbfq\xd3tgIO\xf1\xbf\xf0\x9cB0\xb9\xae\xed\xbf\x01\x1b\xc6A)\x84\xf0\xbfJk\xa2\x8ej\xf8" \
           b"\xf0\xbf\xa4~\x017\xbd\x04\xef\xbf\x88\x9d\xe2\x04\x94\xfd\xf2\xbf\x90TV\n\xca\x98\xec\xbfS\xa5f\xf5\xdd" \
           b"\xe1\xf4\xbf\xfe\x04`mq\xca\xe9\xbf\xcc;\x7ff\x9e\xa0\xf6\xbf\xce;\x7ff\x9e\xa0\xe6\xbfd\xa0\xef\xe9" \
           b"\x875\xf8\xbf\xdb\x0eN\x84\x1d#\xe3\xbf.\xc8j8\xb4\x9c\xf9\xbf\x8c\xfe\x8bF\x13\xb5\xde\xbf7]\xc0\xce" \
           b"\xad\xd2\xfa\xbf\x905\x8bmm\xa0\xd6\xbf\xe7\xb8\x05ux\xd4\xfb\xbf\x98\x84\r'k8\xcc\xbfWq\xb4\x9a\x98\x9f" \
           b"\xfc\xbf\xf4\xca\x04\x7f\xab\xf5\xb4\xbfwT\x99u\x192\xfd\xbf\xd8\xf9\x7f\xc9\xa10\xaf?\xcf\xaa|\xd4\x91" \
           b"\x8a\xfd\xbfk0\xdf\xbf\x7fo\xca?\xf3\xce\x9f\x99'\xa8\xfd\xbf\xc9;\x7ff\x9e\xa0\xd6?\xcf\xaa|\xd4\x91" \
           b"\x8a\xfd\xbf\xaeo\x87v\xbe\x04\xe0?wT\x99u\x192\xfd\xbf+<\xe7I\x94\xad\xe4?Wq\xb4\x9a\x98\x9f\xfc\xbf" \
           b"'\xd5_\xd6S?\xe9?\xe8\xb8\x05ux\xd4\xfb\xbf\xef\x9cB0\xb9\xae\xed?8]\xc0\xce\xad\xd2\xfa\xbfIk\xa2\x8ej" \
           b"\xf8\xf0?/\xc8j8\xb4\x9c\xf9\xbf\x88\x9d\xe2\x04\x94\xfd\xf2?e\xa0\xef\xe9\x875\xf8\xbfR\xa5f\xf5\xdd" \
           b"\xe1\xf4?\xcd;\x7ff\x9e\xa0\xf6\xbf\xcc;\x7ff\x9e\xa0\xf6?V\xa5f\xf5\xdd\xe1\xf4\xbfa\xa0\xef\xe9\x875" \
           b"\xf8?\x89\x9d\xe2\x04\x94\xfd\xf2\xbf-\xc8j8\xb4\x9c\xf9?Jk\xa2\x8ej\xf8\xf0\xbf7]\xc0\xce\xad\xd2\xfa" \
           b"?\xa2\x8e\xf5+\xf4\xbe\xd2?\"G\x90\x1aC\x95\x02@\x9c2\x9d\xa4\xe4W\xfa?\xa8_\xc0M/\xc1\x07@kO\x1e\x9b" \
           b"\xf2x\xfc?\x80\r\xe3\xa0\x14B\x08@R\xb3\x0fH\xa5\xb0\xfe?\xb8i\xba\xb3\xa4\xa7\x08@\xe8\xff%\x87\xc2" \
           b"|\x00@H\xdb,!\xe5\xf0\x08@\x08\xf3\xfd\xfb\xf7\xa6\x01@t\x86\x9eP!\x1d\t@y\xe7\xcf\xcc\x13\xd4\x02@\x86" \
           b"\x1803\xec+\t@\xea\xdb\xa1\x9d/\x01\x04@t\x86\x9eP!\x1d\t@\x0b\xcfy\x12e+\x05@H\xdb," \
           b"!\xe5\xf0\x08@J\xf5\x97\xf5\xd4O\x06@\xb8i\xba\xb3\xa4\xa7\x08@=\xa7\x10L\xaek\x07@\x80\r\xe3\xa0\x14B" \
           b"\x08@\xa55QG5|\x08@\xa9_\xc0M/\xc1\x07@\xc4Nq\x02\xca~\t@$\x95\x95\x822&\x07@\xaaR\xb3\xfa\xeep\n" \
           b"@>\x01X[\x9cr\x06@\xe6\x9d?3OP\x0b@\xf4\xce\x9f\x99'\xa8\x05@1\xd0\xf7\xf4\xc3\x1a\x0c@\xb8\x83\x13a\xc7" \
           b"\xc8\x04@\x17d5\x1cZ\xce\x0c@\xd2\x7f\xd1h\xa2\xd6\x03@\x9c.`\xe7Vi\r@\xb2f\xb1\xad\r\xd4\x02@t\xdc\x82" \
           b":<\xea\r@K\xd8p\xb2\x86\xc3\x01@\xac8ZM\xccO\x0e@X&\xf8[" \
           b"\xad\xa7\x00@<\xaa\xcc\xba\x0c\x99\x0e@2\x00\xb4\xf1z\x06\xff?hU>\xeaH\xc5\x0e@\xf0\x19\x04\x08\x10\xb2" \
           b"\xfc?z\xe7\xcf\xcc\x13\xd4\x0e@\r1`f\xd8W\xfa?hU>\xeaH\xc5\x0e@)H\xbc\xc4\xa0\xfd\xf7?<\xaa\xcc\xba\x0c" \
           b"\x99\x0e@\xeba\x0c\xdb5\xa9\xf5?\xac8ZM\xccO\x0e@k\x15\xd0\x14V`\xf3?t\xdc\x82:<\xea\r@\x88\xb1\xdeg" \
           b"\xa3(\xf1?\x9c.`\xe7Vi\r@n)\xbb\xe2*\x0f\xee?\x17d5\x1cZ\xce\x0c@\xee\xc4:\xf6\xd7\x04\xea?2\xd0\xf7\xf4" \
           b"\xc3\x1a\x0c@Y\xb52\x15D<\xe6?\xe7\x9d?3OP\x0b@f\x88\x013\xc3\xbe\xe2?\xaaR\xb3\xfa\xeep\n@t~AX\xe0)\xdf" \
           b"?\xc6Nq\x02\xca~\t@L\xdfT\x1e/\x8d\xd9?\xa65QG5|\x08@$\x8b\xfe\xc4H\xb5\xd4?W\x9c\x02\xf5BP\xfb?\x109" \
           b"\x82\xd4\x18\xaa\xd4\xbf\x905\x8bmm\xa0\xd6?\xa2~\x017\xbd\x04\xef\xbf\x94\x84\r'k8\xcc?\x01\x1b\xc6A" \
           b")\x84\xf0\xbf\xf0\xca\x04\x7f\xab\xf5\xb4?q\xd3tgIO\xf1\xbf\x10\xfa\x7f\xc9\xa10\xaf\xbf\x91\xb6YB\xca" \
           b"\xe1\xf1\xbfn0\xdf\xbf\x7fo\xca\xbf\xe9\x0c=\xa1B:\xf2\xbf\xca;\x7ff\x9e\xa0\xd6\xbf\r1`f\xd8W\xf2\xbf" \
           b"\xafo\x87v\xbe\x04\xe0\xbf\xe9\x0c=\xa1B:\xf2\xbf"


def test_channel_parallel_offsets():
    channel = channel_init()
    xsec = cross_section_location()
    channel.add_cross_section_location(xsec)
    channel.generate_parallel_offsets()
    assert len(channel.parallel_offsets) == 5
    offset_distances = [po.offset_distance for po in channel.parallel_offsets]
    assert offset_distances == [2.0, 1.0, 0.0, -1.0, -2.0]
    assert (channel.unique_y_ordinates * -1 == offset_distances).all()

    # Parallel offset 1 is 1 m to the left of the channel geometry
    po1 = channel.parallel_offsets[1]
    heights_at_vertices = po1.heights_at_vertices
    assert (heights_at_vertices == np.array([11.0, 11.0])).all()
    assert [str(point.geom) for point in po1.points] == [
        'POINT Z (-0.7071067811865475 0.7071067811865475 11)',
        'POINT Z (1.2928932188134525 2.7071067811865475 11)'
    ]

    # Parallel offset 5 is 2 m to the right of the channel geometry
    po5 = channel.parallel_offsets[4]
    heights_at_vertices = po5.heights_at_vertices
    assert (heights_at_vertices == np.array([12.0, 12.0])).all()
    points_str = [str(point.geom) for point in po5.points]
    assert points_str == [
        "POINT Z (1.414213562373095 -1.414213562373095 12)",
        "POINT Z (3.414213562373095 0.5857864376269051 12)",
    ]


def test_two_vertex_channel():
    "Test the edge case where all parallel offsets are only two vertices long"
    wkt_geometry = "LineString (0 0, 10 10)"
    channel_geom = wkt.loads(wkt_geometry)
    channel = Channel(
        geometry=channel_geom,
        connection_node_start_id=1,
        connection_node_end_id=2,
        id=1,
    )

    y, z = parse_cross_section_table(
        table="0, 1.2\n0.53, 2.1",
        cross_section_shape=SupportedShape.TABULATED_TRAPEZIUM.value
    )

    cross_section_loc = CrossSectionLocation(
        reference_level=10.0,
        bank_level=12.0,
        y_ordinates=y,
        z_ordinates=z,
        geometry=Point(5, 5),
    )

    channel.add_cross_section_location(cross_section_loc)
    channel.generate_parallel_offsets()
    assert channel.as_query() == "SELECT 1 as id, geom_from_wkt('POLYGON Z ((-0.7424621202458748 0.7424621202458748 " \
                                 "10.53, -0.4242640687119283 0.4242640687119283 10, 9.575735931288072 " \
                                 "10.424264068711928 10, -0.7424621202458748 0.7424621202458748 10.53))')" \
                                 "\nUNION\n" \
                                 "SELECT 2 as id, geom_from_wkt('POLYGON Z ((-0.7424621202458748 0.7424621202458748 " \
                                 "10.53, 9.575735931288072 10.424264068711928 10, 9.257537879754125 " \
                                 "10.742462120245875 10.53, -0.7424621202458748 0.7424621202458748 10.53))')" \
                                 "\nUNION\n" \
                                 "SELECT 3 as id, geom_from_wkt('POLYGON Z ((-0.4242640687119283 0.4242640687119283 " \
                                 "10, 10.424264068711928 9.575735931288072 10, 9.575735931288072 10.424264068711928 " \
                                 "10, -0.4242640687119283 0.4242640687119283 10))')" \
                                 "\nUNION\n" \
                                 "SELECT 4 as id, geom_from_wkt('POLYGON Z ((-0.4242640687119283 0.4242640687119283 " \
                                 "10, 0.4242640687119286 -0.4242640687119286 10, 10.424264068711928 9.575735931288072 " \
                                 "10, -0.4242640687119283 0.4242640687119283 10))')" \
                                 "\nUNION\n" \
                                 "SELECT 5 as id, geom_from_wkt('POLYGON Z ((0.4242640687119286 -0.4242640687119286 " \
                                 "10, 10.742462120245875 9.257537879754125 10.53, 10.424264068711928 " \
                                 "9.575735931288072 10, 0.4242640687119286 -0.4242640687119286 10))')" \
                                 "\nUNION\n" \
                                 "SELECT 6 as id, geom_from_wkt('POLYGON Z ((0.4242640687119286 -0.4242640687119286 " \
                                 "10, 0.7424621202458751 -0.7424621202458751 10.53, 10.742462120245875 " \
                                 "9.257537879754125 10.53, 0.4242640687119286 -0.4242640687119286 10))')"


# def test_wedge_on_both_sides():
#     """Test the situation where a channel has a wedge with the connecting channel at both sides"""
#     channels = []
#
#     wkt_geometries = [
#         "LineString (20 -1, 10 -1)",
#         "LineString (10 -1, 0 0)",
#         "LineString (20 -1, 30 0)",
#     ]
#     connection_node_ids = [(1, 2), (2, 3), (1, 4)]
#     cross_section_location_geoms = [Point(15, -1), Point(5, -0.5), Point(25, -0.5)]
#     for i in range(len(wkt_geometries)):
#         channel_geom = wkt.loads(wkt_geometries[i])
#         channels.append(
#             Channel(
#                 geometry=channel_geom,
#                 connection_node_start_id=connection_node_ids[i][0],
#                 connection_node_end_id=connection_node_ids[i][1],
#                 id=i,
#             )
#         )
#
#         y, z = parse_cross_section_table(
#             table="0, 1.2\n0.53, 2.1",
#             cross_section_shape=SupportedShape.TABULATED_TRAPEZIUM.value
#         )
#
#         cross_section_loc = CrossSectionLocation(
#             reference_level=10.0,
#             bank_level=12.0,
#             y_ordinates=y,
#             z_ordinates=z,
#             geometry=cross_section_location_geoms[i],
#         )
#         channels[i].add_cross_section_location(cross_section_loc)
#         channels[i].generate_parallel_offsets()
#     fill_wedges(channels)
#     print(channels[1]._wedge_fill_triangles)


def test_cross_section_starting_at_0_0():
    """"Just to check if this does not give an error"""
    wkt_geometry = "LineString (94066.74041438 441349.75156281, 94060.74041445 441355.7515628, 94064.24041445 " \
                   "441359.75156275, 94074.24041445 441372.25156263)"
    channel_geom = wkt.loads(wkt_geometry)
    channel = Channel(
        geometry=channel_geom,
        connection_node_start_id=1,
        connection_node_end_id=2,
        id=1,
    )

    y, z = parse_cross_section_table(
        table="0, 0\n0.53, 15.13\n1.060, 16.666\n1.590, 17.413\n2.120, 24.984\n2.65, 32.00",
        cross_section_shape=SupportedShape.TABULATED_TRAPEZIUM.value
    )

    cross_section_loc = CrossSectionLocation(
        reference_level=10.0,
        bank_level=12.0,
        y_ordinates=y,
        z_ordinates=z,
        geometry=Point(0, 1),
    )
    channel.add_cross_section_location(cross_section_loc)
    channel.generate_parallel_offsets()


def test_channel_max_width_at():
    channel_geom = LineString([[0, 0], [0, 1], [0, 2], [0, 3]])
    channel = Channel(
        geometry=channel_geom,
        connection_node_start_id=1,
        connection_node_end_id=2,
        id=1,
    )

    y, z = parse_cross_section_table(
        table="0, 0\n1.0, 2.0\n2.0, 4.0",
        cross_section_shape=SupportedShape.TABULATED_TRAPEZIUM.value
    )

    cross_section_loc = CrossSectionLocation(
        reference_level=10.0,
        bank_level=12.0,
        y_ordinates=y,
        z_ordinates=z,
        geometry=Point(0, 1),
    )

    channel.add_cross_section_location(cross_section_loc)

    y, z = parse_cross_section_table(
        table="0, 0\n1.0, 2.0\n2.0, 8.0",
        cross_section_shape=SupportedShape.TABULATED_TRAPEZIUM.value
    )

    cross_section_loc = CrossSectionLocation(
        reference_level=10.0,
        bank_level=12.0,
        y_ordinates=y,
        z_ordinates=z,
        geometry=Point(0, 2),
    )
    channel.add_cross_section_location(cross_section_loc)

    assert channel.max_width_at(0.2) == 4.0
    assert channel.max_width_at(0 * channel.geometry.length) == 4.0
    assert channel.max_width_at(0.25 * channel.geometry.length) == 4.0
    assert channel.max_width_at(0.5 * channel.geometry.length) == 6.0
    assert channel.max_width_at(0.75 * channel.geometry.length) == 8.0
    assert channel.max_width_at(1 * channel.geometry.length) == 8.0


def test_parallel_offset_heights_at_vertices():
    """Test method heights_at_vertices of ParallelOffset"""
    channel_geom = LineString([[0, 0], [5, 1], [7, 1], [18, 2], [20, 2], [35, 3]])
    channel = Channel(
        geometry=channel_geom,
        connection_node_start_id=1,
        connection_node_end_id=2,
        id=1,
    )

    y, z = parse_cross_section_table(
        table="0, 0\n1.0, 2.0\n2.0, 4.0",
        cross_section_shape=SupportedShape.TABULATED_TRAPEZIUM.value
    )
    cross_section_loc = CrossSectionLocation(
        reference_level=2.0,
        bank_level=12.0,
        y_ordinates=y,
        z_ordinates=z,
        geometry=Point(5, 1),
    )
    channel.add_cross_section_location(cross_section_loc)

    y, z = parse_cross_section_table(
        table="0, 0\n1.0, 2.0\n2.0, 8.0",
        cross_section_shape=SupportedShape.TABULATED_TRAPEZIUM.value
    )

    cross_section_loc = CrossSectionLocation(
        reference_level=4.0,
        bank_level=12.0,
        y_ordinates=y,
        z_ordinates=z,
        geometry=Point(20, 2),
    )
    channel.add_cross_section_location(cross_section_loc)
    channel.generate_parallel_offsets()
    po = channel.parallel_offset_at(1.0)
    assert np.allclose(po.heights_at_vertices,
                       np.array([3., 3., 3., 3.00655041, 3.26610821, 4.72680547, 4.73884013, 5., 5.])
                       )


if __name__ == "__main__":
    test_parse_cross_section_table()
