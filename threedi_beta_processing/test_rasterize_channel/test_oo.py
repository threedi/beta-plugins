try:
    from rasterize_channel import *
except ImportError:
    from threedi_beta_processing.rasterize_channel_oo import *


def indexed_point():
    point = IndexedPoint(3.4, 2.4, index=3)
    assert point.index == 3
    assert point.x == 3.4
    assert point.y == 2.4


def triangle():
    point_coords = {
        0: (0, 0),
        1: (1, 1),
        2: (2, 0)
    }
    indexed_points = [IndexedPoint(val, index=key) for key, val in point_coords.items()]
    tri = Triangle(indexed_points)
    assert tri.geometry.wkt == "POLYGON ((0 0, 1 1, 2 0, 0 0))"
    line_1 = LineString([Point(-10,-10,), Point(10,10,)])
    line_2 = LineString([Point(-8, -10,), Point(12, 10,)])
    assert tri.is_between(line_1, line_2)
    line_2 = LineString([Point(-9, -10,), Point(11, 10,)])
    assert not tri.is_between(line_1, line_2)
    line_2 = LineString([Point(300, 400,), Point(310, 410,)])
    assert not tri.is_between(line_1, line_2)


def test_find_wedge_channels():
    # channel_1: last segment pointing north (azimuth = 0)
    channel_1 = Channel(
        geometry=LineString([Point(20, -100), Point(0, -50), Point(0, 0)]),
        connection_node_start_id=1,
        connection_node_end_id=2,
        id=1
    )
    xsec = cross_section_location()
    xsec.geometry = Point(0, -50)
    channel_1.add_cross_section_location(xsec)
    assert channel_1.azimuth_at(connection_node_id=2) == 180

    channel_2 = Channel(
        geometry=LineString([Point(0, 0), Point(10, 50), Point(10, 100)]),
        connection_node_start_id=2,
        connection_node_end_id=3,
        id=2
    )
    xsec = cross_section_location()
    xsec.geometry = Point(10, 50)
    channel_2.add_cross_section_location(xsec)
    print(round(channel_2.azimuth_at(connection_node_id=2), 2))
    assert round(channel_2.azimuth_at(connection_node_id=2), 2) == 11.31

    channel_3 = Channel(
        geometry=LineString([Point(0, 0), Point(50, 0), Point(100, 10)]),
        connection_node_start_id=2,
        connection_node_end_id=4,
        id=3
    )
    xsec = cross_section_location()
    xsec.geometry = Point(50, 0)
    channel_3.add_cross_section_location(xsec)
    assert channel_3.azimuth_at(connection_node_id=2) == 90

    wedge_channels = find_wedge_channels([channel_1, channel_2, channel_3], connection_node_id=2)
    for chn in wedge_channels:
        print(chn.__dict__)
    assert wedge_channels[0].connection_node_start_id == 2
    assert wedge_channels[1].connection_node_end_id == 2
    return wedge_channels


def fill_wedge():
    channel_1, channel_2 = test_find_wedge_channels()
    channel_1.generate_parallel_offsets()
    channel_2.generate_parallel_offsets()
    channel_1.fill_wedge(channel_2)
    # print("channel 1 triangles:")
    # print(channel_1.as_query())
    # print("channel 2 triangles:")
    # print(channel_2.as_query())
    assert len(channel_1._wedge_fill_triangles) == 3
    assert len(channel_2._wedge_fill_triangles) == 0
    assert channel_1._wedge_fill_triangles[0].geometry.wkt == 'POLYGON Z ((0 0 0, -0.9805806756909201 0.196116135138184 1, -1 0 1, 0 0 0))'
    assert channel_1._wedge_fill_triangles[1].geometry.wkt == 'POLYGON Z ((-1 0 1, -0.9805806756909201 0.196116135138184 1, -1.96116135138184 0.3922322702763681 2, -1 0 1))'
    assert channel_1._wedge_fill_triangles[2].geometry.wkt == 'POLYGON Z ((-1 0 1, -1.96116135138184 0.3922322702763681 2, -2 0 2, -1 0 1))'


def channel_init():
    channel_geom = LineString([[0, 0], [1, 1], [2, 2]])
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(28992)

    channel = Channel(geometry=channel_geom, connection_node_start_id=1, connection_node_end_id=2, id=1)
    return channel


def cross_section_location():
    cross_section_loc = CrossSectionLocation(
        reference_level=10.0,
        bank_level=12.0,
        widths=[0.0, 2.0, 4.0],
        heights=[0.0, 1.0, 2.0],
        geometry=Point(1, 1)
    )
    return cross_section_loc


def cross_section_location_height_at(xsec):
    assert xsec.height_at(0.0) == 10 + 0.0
    assert xsec.height_at(1.0) == 10 + 0.5
    assert xsec.height_at(2.0) == 10 + 1.0
    assert xsec.height_at(3.0) == 10 + 1.5
    assert xsec.height_at(5.0) == 10 + 2.0


def channel_vertex_positions(channel):
    vp = channel.vertex_positions
    assert (vp == np.array([0, 0.5, 1]) * channel.geometry.length).all()
    assert len(vp) == 3


def channel_add_cross_section_location(channel, xsec):
    channel.add_cross_section_location(xsec)
    return channel


def channel_properties(channel):
    assert (channel.max_widths == np.array([4.0, 4.0, 4.0])).all()
    assert (channel.unique_widths == np.array([0.0, 2.0, 4.0])).all()
    assert (channel.cross_section_location_positions == np.array([0.5*channel.geometry.length])).all()
    assert str(channel.outline) == 'POLYGON ((-1.414213562373095 1.414213562373095, -0.4142135623730949 2.414213562373095, 0.5857864376269051 3.414213562373095, 3.414213562373095 0.5857864376269051, 2.414213562373095 -0.4142135623730949, 1.414213562373095 -1.414213562373095, -1.414213562373095 1.414213562373095))'


def channel_parallel_offsets(channel):
    assert len(channel.parallel_offsets) == 5
    offset_distances = [po.offset_distance for po in channel.parallel_offsets]
    print(offset_distances)
    print(channel.offset_distances)
    assert offset_distances == [2.0, 1.0, 0.0, -1.0, -2.0]

    po1 = channel.parallel_offsets[1]
    heights_at_vertices = po1.heights_at_vertices
    assert (heights_at_vertices == np.array([1.0, 1.0])).all()
    # assert [str(point) for point in po1.points] == ['POINT Z (-0.7071067811865475 0.7071067811865475 1)', 'POINT Z (1.292893218813453 2.707106781186547 1)'].reverse()

    po5 = channel.parallel_offsets[4]
    heights_at_vertices = po5.heights_at_vertices
    assert (heights_at_vertices == np.array([2.0, 2.0])).all()
    assert [str(point) for point in po5.points] == ['POINT Z (3.414213562373095 0.5857864376269051 2)', 'POINT Z (1.414213562373095 -1.414213562373095 2)']


def two_vertex_channel():
    "Test the edge case where all parallel offsets are only two vertices long"
    wkt_geometry = "LineString (0 0, 10 10)"
    channel_geom = wkt.loads(wkt_geometry)
    channel = Channel(geometry=channel_geom, connection_node_start_id=1, connection_node_end_id=2, id=1)

    cross_section_loc = CrossSectionLocation(
        reference_level=10.0,
        bank_level=12.0,
        widths=[1.2, 2.1],
        heights=[0, 0.53],
        geometry=Point(5, 5)
    )
    channel.add_cross_section_location(cross_section_loc)
    channel.generate_parallel_offsets()
    for tri in channel.triangles:
        print(tri)


def wedge_on_both_sides():
    """Test the situation where a channel has a wedge with the connecting channel at both sides"""
    channels = []

    wkt_geometries = [
        "LineString (20 -1, 10 -1)",
        "LineString (10 -1, 0 0)",
        "LineString (20 -1, 30 0)"
    ]
    connection_node_ids = [
        (1, 2),
        (2, 3),
        (1, 4)
    ]
    cross_section_location_geoms = [
        Point(15, -1),
        Point(5, -0.5),
        Point(25, -0.5)
    ]
    for i in range(len(wkt_geometries)):
        channel_geom = wkt.loads(wkt_geometries[i])
        channels.append(Channel(
            geometry=channel_geom,
            connection_node_start_id=connection_node_ids[i][0],
            connection_node_end_id=connection_node_ids[i][1],
            id=i
        ))
        cross_section_loc = CrossSectionLocation(
            reference_level=10.0,
            bank_level=12.0,
            widths=[1.2, 2.1],
            heights=[0, 0.53],
            geometry=cross_section_location_geoms[i]
        )
        channels[i].add_cross_section_location(cross_section_loc)
        channels[i].generate_parallel_offsets()
    fill_wedges(channels)
    print(channels[1]._wedge_fill_triangles)


def cross_section_starting_at_0_0():
    wkt_geometry = "LineString (94066.74041438 441349.75156281, 94060.74041445 441355.7515628, 94064.24041445 441359.75156275, 94074.24041445 441372.25156263)"
    channel_geom = wkt.loads(wkt_geometry)
    channel = Channel(geometry=channel_geom, connection_node_start_id=1, connection_node_end_id=2, id=1)

    cross_section_loc = CrossSectionLocation(
        reference_level=10.0,
        bank_level=12.0,
        widths=[0, 15.13, 16.666, 17.413, 24.984, 32],
        heights=[0, 0.53, 1.06, 1.59, 2.12, 2.65],
        geometry=Point(0, 1)
    )
    channel.add_cross_section_location(cross_section_loc)
    channel.generate_parallel_offsets()


def channel_max_width_at(channel):
    channel_geom = LineString([[0, 0], [0, 1], [0, 2], [0, 3]])
    channel = Channel(geometry=channel_geom, connection_node_start_id=1, connection_node_end_id=2, id=1)

    cross_section_loc = CrossSectionLocation(
        reference_level=10.0,
        bank_level=12.0,
        widths=[0.0, 2.0, 4.0],
        heights=[0.0, 1.0, 2.0],
        geometry=Point(0, 1)
    )
    channel.add_cross_section_location(cross_section_loc)

    cross_section_loc = CrossSectionLocation(
        reference_level=10.0,
        bank_level=12.0,
        widths=[0.0, 2.0, 8.0],
        heights=[0.0, 1.0, 2.0],
        geometry=Point(0, 2)
    )
    channel.add_cross_section_location(cross_section_loc)

    assert channel.max_width_at(0.2) == 4.0
    assert channel.max_width_at(0*channel.geometry.length) == 4.0
    assert channel.max_width_at(0.25*channel.geometry.length) == 4.0
    assert channel.max_width_at(0.5*channel.geometry.length) == 6.0
    assert channel.max_width_at(0.75*channel.geometry.length) == 8.0
    assert channel.max_width_at(1*channel.geometry.length) == 8.0
    print("Channel outline:")
    print(channel.outline.wkt)


def parallel_offset_heights_at_vertices():
    """Test method heights_at_vertices of ParallelOffset"""
    channel_geom = LineString([[0, 0], [5, 1], [7, 1], [18, 2], [20, 2], [35, 3]])
    channel = Channel(geometry=channel_geom, connection_node_start_id=1, connection_node_end_id=2, id=1)

    cross_section_loc = CrossSectionLocation(
        reference_level=2.0,
        bank_level=12.0,
        widths=[0.0, 2.0, 4.0],
        heights=[0.0, 1.0, 2.0],
        geometry=Point(5, 1)
    )
    channel.add_cross_section_location(cross_section_loc)

    cross_section_loc = CrossSectionLocation(
        reference_level=4.0,
        bank_level=12.0,
        widths=[0.0, 2.0, 8.0],
        heights=[0.0, 1.0, 2.0],
        geometry=Point(20, 2)
    )
    channel.add_cross_section_location(cross_section_loc)
    channel.generate_parallel_offsets()
    po = channel.parallel_offset_at(1.0)
    print(f"po.geometry.wkt: {po.geometry.wkt}")
    print(f"po.vertex_positions: {po.vertex_positions}")
    print(f"po.heights_at_vertices: {po.heights_at_vertices}")
    print([vertex for vertex in po.geometry.coords])
    print(po.points[4].z)


def run_tests():
    # indexed_point()
    # triangle()
    # channel = channel_init()
    # channel_vertex_positions(channel)
    # xsec = cross_section_location()
    # cross_section_location_height_at(xsec)
    # channel_add_cross_section_location(channel, xsec)
    # channel_properties(channel)
    # channel_max_width_at(channel)
    # channel.generate_parallel_offsets()
    # two_vertex_channel()
    wedge_on_both_sides()
    # parallel_offset_heights_at_vertices()
    # cross_section_starting_at_0_0()
    # test_find_wedge_channels()
    # fill_wedge()

    # channel_parallel_offsets(channel)
    # for tri in channel.triangles:
    #     print(tri)
    # print(channel.outline)
    # selects = []
    # for i, tri in enumerate(channel.triangles):
    #     selects.append(f"SELECT {i+1} as id, geom_from_wkt('{str(tri)}')")
    # print("\nUNION\n".join(selects))
    # return channel.points


run_tests()