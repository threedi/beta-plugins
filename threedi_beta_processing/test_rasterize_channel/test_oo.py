try:
    from rasterize_channel_oo import *
except ImportError:
    from threedi_beta_processing.rasterize_channel_oo import *


def channel_init():
    channel_geom = LineString([[0, 0], [1, 1], [2, 2]])
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(28992)

    channel = Channel(geometry=channel_geom, srs=srs)
    return channel


def cross_section_location_init():
    cross_section_location = CrossSectionLocation(
        reference_level=10.0,
        bank_level=12.0,
        widths=[0.0, 2.0, 4.0],
        heights=[0.0, 1.0, 2.0],
        geometry=Point(1,1)
    )
    return cross_section_location


def cross_section_location_height_at(cross_section_location):
    assert cross_section_location.height_at(0.0) == 0.0
    assert cross_section_location.height_at(1.0) == 0.5
    assert cross_section_location.height_at(2.0) == 1.0
    assert cross_section_location.height_at(3.0) == 1.5
    assert cross_section_location.height_at(5.0) == 2.0

def channel_vertex_positions(channel):
    vp = channel.vertex_positions
    assert (vp == np.array([0, 0.5, 1])).all()
    assert len(vp) == 3


def channel_add_cross_section_location(channel, cross_section_location):
    channel.add_cross_section_location(cross_section_location)
    return channel


def channel_properties(channel):
    assert (channel.max_widths == np.array([4.0, 4.0, 4.0])).all()
    assert (channel.unique_widths == np.array([0.0, 2.0, 4.0])).all()
    assert (channel.cross_section_location_positions == np.array([0.5])).all()
    assert str(channel.outline) == 'POLYGON ((-1.414213562373095 1.414213562373095, -0.4142135623730949 2.414213562373095, 0.5857864376269051 3.414213562373095, 3.414213562373095 0.5857864376269051, 2.414213562373095 -0.4142135623730949, 1.414213562373095 -1.414213562373095, -1.414213562373095 1.414213562373095))'


def channel_parallel_offsets(channel):
    assert len(channel.parallel_offsets) == 6
    offset_distances = [po.offset_distance for po in channel.parallel_offsets]
    assert offset_distances == [-2.0, -1.0, -0.0, 0.0, 1.0, 2.0]

    po1 = channel.parallel_offsets[1]
    heights_at_vertices = po1.heights_at_vertices
    assert (heights_at_vertices == np.array([1.0, 1.0])).all()
    assert [str(point) for point in po1.points] == ['POINT Z (-0.7071067811865475 0.7071067811865475 1)', 'POINT Z (1.292893218813453 2.707106781186547 1)']

    po5 = channel.parallel_offsets[5]
    heights_at_vertices = po5.heights_at_vertices
    assert (heights_at_vertices == np.array([2.0, 2.0])).all()
    assert [str(point) for point in po5.points] == ['POINT Z (3.414213562373095 0.5857864376269051 2)', 'POINT Z (1.414213562373095 -1.414213562373095 2)']

def channel_max_width_at(channel):
    assert channel.max_width_at(0.2) == 4.0


def run_tests():
    channel = channel_init()
    channel_vertex_positions(channel)
    cross_section_location = cross_section_location_init()
    cross_section_location_height_at(cross_section_location)
    channel_add_cross_section_location(channel, cross_section_location)
    channel_properties(channel)
    channel_max_width_at(channel)
    channel.generate_parallel_offsets()
    channel_parallel_offsets(channel)
    print(channel.outline)
    return channel.points

run_tests()