from operator import attrgetter
from typing import List, Union, Set, Tuple

import numpy as np
from osgeo import ogr, osr, gdal
from shapely import wkt
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import linemerge, nearest_points, transform


def parse_cross_section_table(table:str) -> Tuple[List, List]:
    """Returns [heights], [widths]"""
    heights = []
    widths = []
    for row in table.split('\n'):
        height, width = row.split(',')
        heights.append(float(height))
        widths.append(float(width))
    return heights, widths


def reverse(geom):
    """Source: https://gis.stackexchange.com/questions/415864/how-do-you-flip-invert-reverse-the-order-of-the-
    coordinates-of-shapely-geometrie
    """
    def _reverse(x, y, z=None):
        if z:
            return x[::-1], y[::-1], z[::-1]
        return x[::-1], y[::-1]

    return transform(_reverse, geom)


class WidthsNotIncreasingError(ValueError):
    """Raised when one a width of a tabular cross section < than the previous width of that crosssection"""
    pass


class Triangle:
    def __init__(self, geometry: Polygon, vertex_indices: List[int]):
        self.geometry = geometry
        self.vertex_indices = vertex_indices


class CrossSectionLocation:
    def __init__(self, reference_level: float, bank_level: float, widths: List[float], heights: List[float],
                 geometry: Point, parent=None):
        self.reference_level = reference_level
        self.bank_level = bank_level
        self.widths = np.array(widths)
        self.heights = np.array(heights)
        self.geometry = geometry
        self.parent = parent

    @classmethod
    def from_qgs_feature(cls, feature):
        qgs_geometry = feature.geometry()
        wkt_geometry = qgs_geometry.asWkt()
        shapely_geometry = wkt.loads(wkt_geometry)
        table = feature.attribute('cross_section_table')
        heights, widths = parse_cross_section_table(table)

        return cls(
            geometry=shapely_geometry,
            reference_level=feature.attribute('reference_level'),
            bank_level=feature.attribute('bank_level'),
            widths=widths,
            heights=heights
        )

    @property
    def position(self):
        if self.parent is None:
            return
        return self.parent.geometry.project(self.geometry, normalized=True)

    @property
    def max_width(self):
        return np.max(np.array(self.widths))

    def bank_levels_as_list(self, add_value: float) -> List[float]:
        """Return list of the same length as the nr. of cross section table entries, of value bank_level + add_value"""
        return [self.bank_level + add_value] * len(self.heights)

    def elevations(self, add_value: float) -> List[float]:
        """Return list of cross section heights + add_value, but absolute instead of relevant to reference level"""
        return [height + self.reference_level + add_value for height in self.heights]

    def height_at(self, width: float) -> float:
        """Get interpolated height at given width"""
        if np.any(np.diff(np.array([1,2,3,3])) < 0):
            raise WidthsNotIncreasingError
        return np.interp(width, self.widths, self.heights)


class Channel:
    def __init__(self,
                 geometry: LineString,
                 connection_node_start_id: Union[int, None],
                 connection_node_end_id: Union[int, None]
                 ):
        self.connection_node_start_id = connection_node_start_id
        self.connection_node_end_id = connection_node_end_id
        self.cross_section_locations = []
        self.geometry = geometry
        self.parallel_offsets = []
        self._wedge_fill_points = []
        self._wedge_fill_triangles = []

    @classmethod
    def from_spatialite(cls, spatialite: ogr.DataSource, channel_id):
        pass

    @classmethod
    def from_geopackage(cls, geopackage: ogr.DataSource, channel_id):
        pass

    @classmethod
    def from_qgs_feature(cls, feature):
        qgs_geometry = feature.geometry()
        wkt_geometry = qgs_geometry.asWkt()
        shapely_geometry = wkt.loads(wkt_geometry)
        start_id = feature.attribute('connection_node_start_id')
        end_id = feature.attribute('connection_node_end_id')
        return cls(geometry=shapely_geometry, connection_node_start_id=start_id, connection_node_end_id=end_id)

    @property
    def max_widths(self) -> np.array:
        """Array describing the max crosssectional width along the channel"""
        return np.array([x.max_width for x in self.cross_section_locations])

    @property
    def unique_widths(self) -> np.array:
        widths_list = [x.widths for x in self.cross_section_locations]
        widths = np.vstack(widths_list)
        unique_widths = np.unique(widths)
        result = np.array(unique_widths)
        return result

    @property
    def cross_section_location_positions(self) -> np.array:
        """Array of normalized (0-1) cross section location positions along the channel"""
        return np.array([x.position for x in self.cross_section_locations])

    @property
    def vertex_positions(self) -> np.array:
        """Array of normalized (0-1) cross section location positions along the channel"""
        result_list = [self.geometry.project(Point(vertex), normalized=True) for vertex in self.geometry.coords]
        result_array = np.array(result_list)
        return result_array

    @property
    def outline(self) -> Polygon:
        right_vertices = []
        left_vertices = []
        for i, position in enumerate(self.vertex_positions):
            width = self.max_width_at(position)

            #left
            parallel_offset_left = self.geometry.parallel_offset(-width/2)
            vertex_left = nearest_points(parallel_offset_left, Point(self.geometry.coords[i]))[0]
            left_vertices.append(vertex_left)

            #right
            parallel_offset_right = self.geometry.parallel_offset(width/2)
            vertex_right = nearest_points(parallel_offset_right, Point(self.geometry.coords[i]))[0]
            right_vertices.append(vertex_right)

        right_vertices.reverse()
        vertices = left_vertices + right_vertices
        return Polygon(LineString(vertices))

    def add_cross_section_location(self, cross_section_location: CrossSectionLocation):
        """Become the parent of the cross section location"""
        cross_section_location.parent = self
        self.cross_section_locations.append(cross_section_location)

    def max_width_at(self, position: float) -> float:
        """Interpolated max crosssectional width at given position"""
        return np.interp(position, self.cross_section_location_positions, self.max_widths)

    def generate_parallel_offsets(self):
        """
        Generate a set of lines parallel to the input linestring, at both sides of the line
        Offsets are sorted from left to right
        """
        self.parallel_offsets = []
        for width in self.unique_widths:
            if width > 0:  # to prevent duplicate parallel offset in middle of channel
                self.parallel_offsets.append(ParallelOffset(parent=self, offset_distance= - width / 2))
        for width in self.unique_widths:
            self.parallel_offsets.append(ParallelOffset(parent=self, offset_distance=width / 2))
        self.parallel_offsets.reverse()
        last_vertex_index = -1  # so that we have 0-based indexing, because QgsMesh vertices have 0-based indices too
        for po in self.parallel_offsets:
            po.set_vertex_indices(first_vertex_index=last_vertex_index+1)
            last_vertex_index = po.vertex_indices[-1]

    def parallel_offset_at(self, offset_distance):
        if offset_distance not in self.unique_widths and offset_distance not in -1*self.unique_widths:
            raise ValueError("Offset distance not available for this Channel")
        for po in self.parallel_offsets:
            if po.offset_distance == offset_distance:
                return po
        raise ValueError(f"Parallel offset not found at offset distance {offset_distance}")

    @property
    def points(self):
        """Returns all points of all parallel offsets ordered by vertex index"""
        all_points = []
        for po in self.parallel_offsets:
            all_points += po.points
        all_points += self._wedge_fill_points
        return all_points

    @property
    def indexed_points(self):
        return [po.points for po in self.parallel_offsets]

    @property
    def triangles(self) -> List[Triangle]:
        parallel_offsets = self.parallel_offsets
        for i in range(len(parallel_offsets)-1):
            for tri in parallel_offsets[i].triangulate(parallel_offsets[i+1]):
                yield tri
        for tri in self._wedge_fill_triangles:
            yield tri

    def find_vertex(self, connection_node_id, n: int) -> Point:
        """Starting from the given connection node, find the nth vertex"""
        if connection_node_id == self.connection_node_start_id:
            return Point(self.geometry.coords[n])
        elif connection_node_id == self.connection_node_end_id:
            return Point(self.geometry.coords[-(n+1)])
        else:
            raise ValueError(f'connection_node_id {connection_node_id} is not a start or end connection node of this '
                             f'channel')

    def azimuth_at(self, connection_node_id: int) -> float:
        """Return the azimuth of the segment of the channel's geometry that links to given connection node"""
        connection_node_geometry = self.find_vertex(connection_node_id, 0)
        second_point = self.find_vertex(connection_node_id, 1)
        return azimuth(connection_node_geometry, second_point)

    def fill_wedge(self, other):
        """Add points and triangles to fill the wedge-shaped gap between self and other"""
        # Find out if and how self and other_channel are connected
        # -->-->
        if self.connection_node_end_id == other.connection_node_start_id:
            channel_to_update = self
            if ccw_angle(self, other) > 180:
                channel_to_update_side = 1  # right
                wedge_fill_points_source_side = 1  # right
            else:
                channel_to_update_side = -1  # left
                wedge_fill_points_source_side = -1  # left
            wedge_fill_points_source = other
            wedge_fill_points_source_idx = 0
        # --><--
        elif self.connection_node_end_id == other.connection_node_end_id:
            channel_to_update = self
            if ccw_angle(self, other) > 180:
                channel_to_update_side = 1  # right
                wedge_fill_points_source_side = -1  # left
            else:
                channel_to_update_side = -1  # left
                wedge_fill_points_source_side = 1  # right
            wedge_fill_points_source = other
            wedge_fill_points_source_idx = -1
        # <---->
        elif self.connection_node_start_id == other.connection_node_start_id:
            channel_to_update = self
            if ccw_angle(self, other) > 180:
                channel_to_update_side = -1  # left
                wedge_fill_points_source_side = 1  # right
            else:
                channel_to_update_side = 1  # right
                wedge_fill_points_source_side = -1  # left
            wedge_fill_points_source = other
            wedge_fill_points_source_idx = 0
        # <--<--
        elif self.connection_node_start_id == other.connection_node_end_id:
            channel_to_update = other
            if ccw_angle(self, other) > 180:
                channel_to_update_side = -1  # left
                wedge_fill_points_source_side = -1  # left
            else:
                channel_to_update_side = 1  # right
                wedge_fill_points_source_side = 1  # right
            wedge_fill_points_source = self
            wedge_fill_points_source_idx = 0
        # -->                               -->
        else:
            raise ValueError("Channels are not connected")

        # Append start or end vertices of all other_channel's parallel offsets to self._wedge_fill_points
        # left is negative, right is positive
        for width in wedge_fill_points_source.unique_widths:
            po = wedge_fill_points_source.parallel_offset_at(width * wedge_fill_points_source_side)
            self._wedge_fill_points.append(po.points[wedge_fill_points_source_idx])

        # Generate triangles to connect the added points to the existing points
        # TODO Hier verder gaan
        self._wedge_fill_triangles.append()


class ChannelGroup(Channel):
    """One or more Channels of which the geometry can be linemerged to a single linestring"""
    def __init__(self, channels: List[Channel]):
        geometries = [channel.geometry for channel in channels]
        merged_geometry = linemerge(geometries)
        if not isinstance(self.geometry, LineString):
            raise ValueError('Input channel geometries cannot be merged into a single LineString')
        super().__init__(geometry=merged_geometry, connection_node_start_id=None, connection_node_end_id=None)

        unsorted_cross_section_locations = []
        for channel in channels:
            for cross_section_location in channel.cross_section_locations:
                cross_section_location.position = self.geometry.project(cross_section_location.geometry, normalized=True)
                unsorted_cross_section_locations.append(cross_section_location)
        self.cross_section_locations = sorted(unsorted_cross_section_locations, key=attrgetter('position'))


class ParallelOffset:
    def __init__(self, parent: Union[Channel, ChannelGroup], offset_distance):
        self.parent = parent
        self.geometry = parent.geometry.parallel_offset(offset_distance)
        if offset_distance <= 0:
            self.geometry = reverse(self.geometry)
        self.offset_distance = offset_distance
        width = np.abs(self.offset_distance * 2)
        cross_section_location_points = []
        for pos in self.parent.cross_section_location_positions:
            location_xy = self.parent.geometry.interpolate(pos, normalized=True)
            cross_section_location_points.append(nearest_points(location_xy, self.geometry)[0])
        cross_section_location_positions = [self.geometry.project(point) for point in cross_section_location_points]
        heights_at_cross_sections = [xsec.height_at(width) for xsec in self.parent.cross_section_locations]
        self.vertex_positions = [self.geometry.project(Point(vertex), normalized=True) for vertex in self.geometry.coords]
        self.heights_at_vertices = np.interp(
            self.vertex_positions,
            cross_section_location_positions,
            heights_at_cross_sections
        )
        self.vertex_indices = None

    @property
    def points(self):
        result = []
        for i, vertex in enumerate(self.geometry.coords):
            result.append(Point(vertex[0], vertex[1], self.heights_at_vertices[i]))
        return result

    def set_vertex_indices(self, first_vertex_index):
        self.vertex_indices = list(range(first_vertex_index, first_vertex_index + len(self.geometry.coords)))

    def triangle_is_valid(self, triangle_points, other_parallel_offset):
        """Return True if none of the sides of the triangle crosses the parallel offsets that should enclose it"""
        valid = True
        for start, end in [(0, 1), (0, 2), (1, 2)]:
            line = LineString([triangle_points[start], triangle_points[end]])
            if self.geometry.crosses(line) or other_parallel_offset.geometry.crosses(line):
                valid = False
        return valid

    def triangulate(self, other):
        self_points = self.points
        self_current_index = self.vertex_indices[0]
        other_points = other.points
        other_current_index = other.vertex_indices[0]
        last_move = 'self'

        while (self_current_index < self.vertex_indices[-1]) or (other_current_index < other.vertex_indices[-1]):
            triangle_points = [self_points[self_current_index-self.vertex_indices[0]],
                               other_points[other_current_index-other.vertex_indices[0]]]
            triangle_indices = [self_current_index, other_current_index]
            # first we handle the case where the end of the line has been reached at one of the sides
            if self_current_index == self.vertex_indices[-1]:
                other_current_index += 1
                triangle_points.append(other_points[other_current_index-other.vertex_indices[0]])
                triangle_indices.append(other_current_index)
            elif other_current_index == other.vertex_indices[-1]:
                self_current_index += 1
                triangle_points.append(self_points[self_current_index-self.vertex_indices[0]])
                triangle_indices.append(self_current_index)
            # then we handle the 'normal' case when we are still halfway at both sides
            else:
                next_self_vertex_pos = self.vertex_positions[self_current_index-self.vertex_indices[0] + 1]
                next_other_vertex_pos = other.vertex_positions[other_current_index-other.vertex_indices[0] + 1]
                if next_other_vertex_pos == next_self_vertex_pos:
                    move = 'other' if last_move == 'self' else 'self'
                elif next_other_vertex_pos > next_self_vertex_pos:
                    move = 'self'
                else:
                    move = 'other'

                # switch move side if moving on that side results in invalid triangle
                if move == 'other':
                    additional_point = other_points[other_current_index + 1 - other.vertex_indices[0]]
                    test_triangle_points = triangle_points + [additional_point]
                    if not self.triangle_is_valid(triangle_points=test_triangle_points, other_parallel_offset=other):
                        move = 'self'
                else:
                    additional_point = self_points[self_current_index + 1 - self.vertex_indices[0]]
                    test_triangle_points = triangle_points + [additional_point]
                    if not self.triangle_is_valid(triangle_points=test_triangle_points, other_parallel_offset=other):
                        move = 'other'

                if move == 'other':
                    other_current_index += 1
                    triangle_points.append(other_points[other_current_index - other.vertex_indices[0]])
                    triangle_indices.append(other_current_index)
                    last_move = 'other'
                else:
                    self_current_index += 1
                    triangle_points.append(self_points[self_current_index-self.vertex_indices[0]])
                    triangle_indices.append(self_current_index)
                    last_move = 'self'

            yield Triangle(geometry=Polygon(LineString(triangle_points)), vertex_indices=triangle_indices)


def unique_connection_node_ids(channels: List[Channel]) -> Set[int]:
    result = set([channel.connection_node_start_id for channel in channels])
    result |= set([channel.connection_node_end_id for channel in channels])
    return result


def get_channels_per_connection_node(channels: List[Channel]) -> dict:
    result = dict()
    connection_node_ids = unique_connection_node_ids(channels)
    for connection_node_id in connection_node_ids:
        current_node_channels = []
        for channel in channels:
            if connection_node_id in [channel.connection_node_start_id, channel.connection_node_end_id]:
                current_node_channels.append(channel)
        result[connection_node_id] = current_node_channels
    return result


def azimuth(point1, point2):
    """azimuth between 2 shapely points (interval 0 - 360)"""
    angle = np.arctan2(point2.x - point1.x, point2.y - point1.y)
    return np.degrees(angle) if angle >= 0 else np.degrees(angle) + 360


def ccw_angle(channel1: Channel, channel2: Channel) -> float:
    """Calculate the CCW angle in degrees between a line from `point1` to `reference`
    and a line between `point2` and `reference`"""
    connection_node_ids = unique_connection_node_ids([channel1, channel2])
    for connection_node_id in connection_node_ids:
        if connection_node_id in [channel1.connection_node_start_id, channel1.connection_node_end_id] \
                and connection_node_id in [channel2.connection_node_start_id, channel2.connection_node_end_id]:
            break
    connection_node_geometry = channel1.find_vertex(connection_node_id, 0)
    channel1_point = channel1.find_vertex(connection_node_id, 1)
    channel2_point = channel2.find_vertex(connection_node_id, 1)
    azimuth1 = azimuth(connection_node_geometry, channel1_point)
    azimuth2 = azimuth(connection_node_geometry, channel2_point)
    if azimuth2 > azimuth1:
        return azimuth1 + (360 - azimuth2)
    else:
        return azimuth1 - azimuth2


def find_wedge_channels(channels: List[Channel], connection_node_id: int) -> \
        Union[Tuple[Channel, Channel], Tuple[None, None]]:
    """In a list of channels that connect to the same connection node, find a pair of channels that connect at
    a > 180 degree angle, so that there is a wedge-shaped gap between them"""
    azimuth_channel_dict = {}
    for channel in channels:
        key = round(channel.azimuth_at(connection_node_id))
        azimuth_channel_dict[key] = channel
    sorted_azimuths = list(azimuth_channel_dict.keys())
    sorted_azimuths.sort()
    sorted_azimuths = [sorted_azimuths[-1]] + sorted_azimuths
    for i in range(len(sorted_azimuths)):
        channel_1 = azimuth_channel_dict[sorted_azimuths[i]]
        channel_2 = azimuth_channel_dict[sorted_azimuths[i + 1]]
        if ccw_angle(channel_1, channel_2) > 180:
            return channel_1, channel_2
    return None, None


def fill_wedges(channels: List[Channel]):
    connection_node_channels_dict = get_channels_per_connection_node(channels)
    for connection_node_id, channels in connection_node_channels_dict.items():
        channel1, channel2 = find_wedge_channels(channels=channels, connection_node_id=connection_node_id)
        if channel1 and channel2:
            channel1.fill_wedge(channel2)
