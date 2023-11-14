# TODO for YZ support
#  - For YZ, the channel geometry is not necessarily located at the (y-dimension) center of the cross-section
#  - We can assume that the channel geometry is located at the thalweg, i.e. the lowest point in the river bed
#  - For each cross-section, calculate thalweg location in the Y dimension
#  - Two options: thalweg is lowest point in cross-section, or thalweg is middle of cross-section
#  - Instead of widths, use offsets, i.e. Y relative to thalweg (positive for points to the left of the thalweg, negative for points to the right of the thalweg)
#  - I.e., for tab. trapezium and rectangle, convert widths to offsets
from enum import Enum
from typing import Iterator, List, Union, Set, Tuple

import numpy as np
from shapely import wkt
from shapely.geometry import LineString, MultiPolygon, Point, Polygon
from shapely.ops import unary_union, nearest_points, transform


WALL_DISPLACEMENT = 0.01  # tops of vertical segments are moved by this amount


class SupportedShape(Enum):
    TABULATED_RECTANGLE = 5
    TABULATED_TRAPEZIUM = 6
    YZ = 7


def parse_cross_section_table(table: str, cross_section_shape: SupportedShape, wall_displacement: float = 0) -> Tuple[np.array, np.array]:
    """Returns [y_ordinates], [z_ordinates]"""
    if cross_section_shape in (SupportedShape.TABULATED_RECTANGLE, SupportedShape.TABULATED_TRAPEZIUM):
        heights = list()
        widths = list()
        for row in table.split("\n"):
            height, width = row.split(",")
            if len(heights) == 0:
                # first pass
                heights.append(float(height))
                widths.append(float(width))
            else:
                if height == heights[-1]:
                    width += wall_displacement*2   # *2 because /2 when converting to YZ
                if cross_section_shape == SupportedShape.TABULATED_RECTANGLE:
                    # add extra height/width entry to convert tabulated rectangle to tabulated trapezium
                    heights.append(float(height))
                    widths.append(float(widths[-1]) + wall_displacement*2)  # *2 because /2 when converting to YZ
                heights.append(float(height))
                widths.append(float(width))
        # convert to YZ
        if widths[0] == 0:  # do no duplicate middle y value if it is 0
            y_ordinates = np.hstack([np.flip(widths)/-2, np.array(widths)[1:]/2])
            z_ordinates = np.hstack([np.flip(heights), np.array(heights)[1:]])
        else:
            y_ordinates = np.hstack([np.flip(widths)/-2, np.array(widths)/2])
            z_ordinates = np.hstack([np.flip(heights), heights])
        y_ordinates += np.max(widths)/2
    elif cross_section_shape in (SupportedShape.YZ):
        y_list = list()
        z_list = list()
        for row in table.split("\n"):
            y, z = row.split(",")
            y_list.append(float(y))
            z_list.append(float(z))
        y_ordinates = np.array(y_list)
        z_ordinates = np.array(z_list)
    else:
        raise ValueError(f"Unsupported cross_section_shape {cross_section_shape}")
    return y_ordinates, z_ordinates


def reverse(geom):
    """Source: https://gis.stackexchange.com/questions/415864/how-do-you-flip-invert-reverse-the-order-of-the-
    coordinates-of-shapely-geometrie
    """

    def _reverse(x, y, z=None):
        if z:
            return x[::-1], y[::-1], z[::-1]
        return x[::-1], y[::-1]

    return transform(_reverse, geom)


def variable_buffer(linestring: LineString, radii: List[float]) -> Polygon:
    """Create a buffer around a Linestring, for which the (> 0) buffer distance varies per vertex"""
    assert len(linestring.coords) == len(radii)
    assert np.all(np.array(radii) >= 0)
    buffered_points = [
        Point(coord).buffer(radii[i]) for i, coord in enumerate(linestring.coords)
    ]
    convex_hulls = [
        MultiPolygon([buffered_points[i], buffered_points[i + 1]]).convex_hull
        for i in range(len(buffered_points) - 1)
    ]
    result = unary_union(convex_hulls)
    return result


class EmptyOffsetError(ValueError):
    """Raised when the parallel offset at given offset distance results in an empty geometry"""

    pass


class InvalidOffsetError(ValueError):
    """Raised when the parallel offset at given offset distance results in a geometry that is not a LineString"""


class WedgeFillPointsAlreadySetError(ValueError):
    """Raised when it is attempted to set a channel's _wedge_fill_points that have already been set"""

    pass


class WidthsNotIncreasingError(ValueError):
    """Raised when one a width of a tabular cross section < than the previous width of that crosssection"""

    pass


class IndexedPoint:
    def __init__(self, *args, index: int):
        self.geom = Point(*args)  # since shapely 2.0, it is no longer possible to add any custom attributes to a Point,
                                  # so it is impossible to inherit all from Point and add index
        self.index = index

    @property
    def x(self):
        return self.geom.x

    @property
    def y(self):
        return self.geom.y

    @property
    def z(self):
        return self.geom.z


class Triangle:
    def __init__(self, points: List[IndexedPoint]):
        self.points = points
        self.geometry = Polygon(LineString([point.geom for point in points]))
        self.vertex_indices = [point.index for point in points]

    @property
    def sides(self) -> Set:
        """Returns a set of tuples, where each tuple is a sorted pair of vertex indices describing a triangle's side"""
        idx = self.vertex_indices
        return {
            tuple(sorted(idx[0:2])),
            tuple(sorted(idx[1:3])),
            tuple(sorted([idx[2], idx[0]])),
        }

    def is_between(self, line_1: LineString, line_2: LineString):
        if not (self.geometry.touches(line_1) and self.geometry.touches(line_2)):
            return False
        valid = True
        for start, end in [(0, 1), (0, 2), (1, 2)]:
            line = LineString([self.points[start].geom, self.points[end].geom])
            if line.crosses(line_1) or line.crosses(line_2):
                valid = False
        return valid


class CrossSectionLocation:
    def __init__(
        self,
        reference_level: float,
        bank_level: float,
        widths: List[float],
        heights: List[float],
        geometry: Point,
        parent=None,
    ):
        self.reference_level = reference_level
        self.bank_level = bank_level
        self.widths = np.array(widths)
        self.heights = np.array(heights) + reference_level
        self.geometry = geometry
        self.parent = parent

    @classmethod
    def from_qgs_feature(cls, feature):
        qgs_geometry = feature.geometry()
        wkt_geometry = qgs_geometry.asWkt()
        shapely_geometry = wkt.loads(wkt_geometry)
        cross_section_shape = feature.attribute("cross_section_shape")
        table = feature.attribute("cross_section_table")
        heights, widths = parse_cross_section_table(table)

        return cls(
            geometry=shapely_geometry,
            reference_level=feature.attribute("reference_level"),
            bank_level=feature.attribute("bank_level"),
            widths=widths,
            heights=heights,
        )

    @property
    def position(self):
        if self.parent is None:
            return
        return self.parent.geometry.project(self.geometry)

    @property
    def max_width(self):
        return np.max(np.array(self.widths))

    @property
    def thalweg_y(self):
        """Returns distance between the start of the cross-section at the left bank and the lowest point of the
        cross-section. The thalweg is located at the average y index of all points with the minimum z value"""
        self.y_ordinates
        z0_indices = np.where(self.z_ordinates == np.min(self.z_ordinates))
        thalweg_index = int(np.average(z0_indices))
        return self.y_ordinates[thalweg_index]

    def bank_levels_as_list(self, add_value: float) -> List[float]:
        """Return list of the same length as the nr. of cross section table entries, of value bank_level + add_value"""
        return [self.bank_level + add_value] * len(self.heights)

    def elevations(self, add_value: float) -> List[float]:
        """Return list of cross section heights + add_value, but absolute instead of relevant to reference level"""
        return [height + self.reference_level + add_value for height in self.heights]

    def height_at(self, width: float) -> float:
        """Get interpolated height at given width"""
        if np.any(np.diff(self.widths) < 0):
            raise WidthsNotIncreasingError
        return np.interp(width, self.widths, self.heights)


class Channel:
    def __init__(
        self,
        id: int,
        connection_node_start_id: Union[int, None],
        connection_node_end_id: Union[int, None],
        geometry: LineString,
    ):
        self.id = id
        self.connection_node_start_id = connection_node_start_id
        self.connection_node_end_id = connection_node_end_id
        self.cross_section_locations = []
        self.geometry = geometry
        self.parallel_offsets = []
        self._wedge_fill_points = []
        self._wedge_fill_triangles = []
        self._extra_outline = []

    @classmethod
    def from_qgs_feature(cls, feature):
        qgs_geometry = feature.geometry()
        wkt_geometry = qgs_geometry.asWkt()
        shapely_geometry = wkt.loads(wkt_geometry)
        start_id = feature.attribute("connection_node_start_id")
        end_id = feature.attribute("connection_node_end_id")
        id = feature.attribute("id")
        return cls(
            geometry=shapely_geometry,
            connection_node_start_id=start_id,
            connection_node_end_id=end_id,
            id=id,
        )

    @property
    def max_widths(self) -> np.array:
        """Array describing the max crosssectional width along the channel"""
        return np.array([x.max_width for x in self.cross_section_locations])

    @property
    def unique_widths(self) -> np.array:
        widths_list = [x.widths for x in self.cross_section_locations]
        widths = np.hstack(widths_list)
        unique_widths = np.unique(widths)
        result = np.array(unique_widths)
        return result

    @property
    def offset_distances(self) -> np.array:
        negatives = [-width / 2 for width in self.unique_widths if width > 0]
        negatives.reverse()
        positives = [width / 2 for width in self.unique_widths]
        result = negatives + positives
        result.reverse()
        return np.array(result)

    @property
    def cross_section_location_positions(self) -> np.array:
        """Array of cross section location positions along the channel"""
        return np.array([x.position for x in self.cross_section_locations])

    @property
    def vertex_positions(self) -> np.array:
        """Array of channel vertex positions along the channel"""
        result_list = [
            self.geometry.project(Point(vertex)) for vertex in self.geometry.coords
        ]
        result_array = np.array(result_list)
        return result_array

    @property
    def outline(self) -> Polygon:
        radii = [self.max_width_at(position) / 2 for position in self.vertex_positions]
        result = variable_buffer(self.geometry, radii)
        for extra in self._extra_outline:
            result = result.union(extra)
        return result

    def add_cross_section_location(self, cross_section_location: CrossSectionLocation):
        """Become the parent of the cross section location"""
        cross_section_location.parent = self
        self.cross_section_locations.append(cross_section_location)
        self.cross_section_locations.sort(key=lambda x: x.position)

    def max_width_at(self, position: float) -> float:
        """Interpolated max crosssectional width at given position"""
        return np.interp(
            position, self.cross_section_location_positions, self.max_widths
        )

    def generate_parallel_offsets(self):
        """
        Generate a set of lines parallel to the input linestring, at both sides of the line
        Offsets are sorted from left to right
        """
        self.parallel_offsets = []
        for offset_distance in self.offset_distances:
            self.parallel_offsets.append(
                ParallelOffset(parent=self, offset_distance=offset_distance)
            )

        last_vertex_index = (
            -1
        )  # so that we have 0-based indexing, because QgsMesh vertices have 0-based indices too
        for po in self.parallel_offsets:
            po.set_vertex_indices(first_vertex_index=last_vertex_index + 1)
            last_vertex_index = po.vertex_indices[-1]

    def parallel_offset_at(self, offset_distance):
        if offset_distance not in self.offset_distances:
            raise ValueError(
                f"Parallel offset not found at offset distance {offset_distance}. "
                f"Channel between nodes {self.connection_node_start_id} and "
                f"{self.connection_node_end_id}. Available offset distances: {self.offset_distances}"
            )
        for po in self.parallel_offsets:
            if po.offset_distance == offset_distance:
                return po
        raise ValueError(
            f"Parallel offset not found at offset distance {offset_distance}. "
            f"Channel between nodes {self.connection_node_start_id} and "
            f"{self.connection_node_end_id}. Available offset distances: {self.offset_distances}"
        )

    @property
    def points(self):
        """Returns all points of all parallel offsets ordered by vertex index"""
        all_points = []
        for po in self.parallel_offsets:
            all_points += po.points
        all_points += self._wedge_fill_points
        return all_points

    @staticmethod
    def add_to_triangle_sort(
        triangle: Triangle,
        processed_sides: Set[Tuple],
        sorted_triangles: List[Triangle],
    ) -> bool:
        """Adds the triangle to `sorted_triangles` if at least one of its sides is already present in `processed_sides`
        Returns True if adding was successful, False if not"""
        new_sides = triangle.sides
        if len(
            new_sides & processed_sides
        ):  # at least one of the sides of the new triangle has already been processed
            sorted_triangles.append(triangle)
            processed_sides.update(new_sides)
            return True
        else:
            return False

    @property
    def triangles(self) -> List[Triangle]:
        """
        Returns a list of Triangles, sorted in such a way that each triangle shares at least one side with a
        preceding triangle in the list. If this is not possible, the resulting list may contain several sections to
        which this requirement applies, but not between the sections.
        """
        triangles = []
        for i in range(len(self.parallel_offsets) - 1):
            for tri in self.parallel_offsets[i].triangulate(
                self.parallel_offsets[i + 1]
            ):
                triangles.append(tri)
        for tri in self._wedge_fill_triangles:
            triangles.append(tri)

        # sort
        processed_sides = triangles[0].sides
        sorted_triangles = [triangles[0]]

        while len(sorted_triangles) < len(triangles):
            failed_triangles = []
            for triangle in triangles[1:]:
                # handle next triangle from the original list
                if not self.add_to_triangle_sort(
                    triangle, processed_sides, sorted_triangles
                ):
                    failed_triangles.append(triangle)

                # handle failed triangles from previous run(s)
                triangle_added = True
                while triangle_added:
                    before_count = len(sorted_triangles)
                    failed_triangles = [
                        ft
                        for ft in failed_triangles
                        if not self.add_to_triangle_sort(
                            ft, processed_sides, sorted_triangles
                        )
                    ]
                    triangle_added = len(sorted_triangles) > before_count
            if failed_triangles:
                # force first failed triangle in the sorted list and continue while loop
                sorted_triangles.append(failed_triangles[0])
                processed_sides.update(failed_triangles[0].sides)
                triangles = failed_triangles[1:]

        return sorted_triangles

    def find_vertex(self, connection_node_id, n: int) -> Point:
        """Starting from the given connection node, find the nth vertex"""
        if connection_node_id == self.connection_node_start_id:
            return Point(self.geometry.coords[n])
        elif connection_node_id == self.connection_node_end_id:
            return Point(self.geometry.coords[-(n + 1)])
        else:
            raise ValueError(
                f"connection_node_id {connection_node_id} is not a start or end connection node of this "
                f"channel"
            )

    def azimuth_at(self, connection_node_id: int) -> float:
        """Return the azimuth of the segment of the channel's geometry that links to given connection node"""
        connection_node_geometry = self.find_vertex(connection_node_id, 0)
        second_point = self.find_vertex(connection_node_id, 1)
        return azimuth(connection_node_geometry, second_point)

    def fill_wedge(self, other):
        """Add points and triangles to fill the wedge-shaped gap between self and other. Also updates self.outline"""
        # Find out if and how self and other_channel are connected
        # -->-->
        if self.connection_node_end_id == other.connection_node_start_id:
            channel_to_update = self
            channel_to_update_idx = -1  # end
            if ccw_angle(self, other) > 180:
                channel_to_update_side = 1  # right
                wedge_fill_points_source_side = 1  # right
            else:
                channel_to_update_side = -1  # left
                wedge_fill_points_source_side = -1  # left
            wedge_fill_points_source = other
            wedge_fill_points_source_idx = 0  # start
        # --><--
        elif self.connection_node_end_id == other.connection_node_end_id:
            channel_to_update = self
            channel_to_update_idx = -1  # end
            if ccw_angle(self, other) > 180:
                channel_to_update_side = 1  # right
                wedge_fill_points_source_side = -1  # left
            else:
                channel_to_update_side = -1  # left
                wedge_fill_points_source_side = 1  # right
            wedge_fill_points_source = other
            wedge_fill_points_source_idx = -1  # end
        # <---->
        elif self.connection_node_start_id == other.connection_node_start_id:
            channel_to_update = self
            channel_to_update_idx = 0  # start
            if ccw_angle(self, other) > 180:
                channel_to_update_side = -1  # left
                wedge_fill_points_source_side = 1  # right
            else:
                channel_to_update_side = 1  # right
                wedge_fill_points_source_side = -1  # left
            wedge_fill_points_source = other
            wedge_fill_points_source_idx = 0  # start
        # <--<--
        elif self.connection_node_start_id == other.connection_node_end_id:
            channel_to_update = other
            channel_to_update_idx = -1  # end
            wedge_fill_points_source = self
            wedge_fill_points_source_idx = 0  # start
            if ccw_angle(self, other) > 180:
                channel_to_update_side = -1  # left
                wedge_fill_points_source_side = -1  # left
            else:
                channel_to_update_side = 1  # right
                wedge_fill_points_source_side = 1  # right
        # -->                               -->
        else:
            raise ValueError("Channels are not connected")

        channel_to_update_offsets = []
        wedge_fill_points_source_offsets = [0]
        channel_to_update_points = []
        last_index = channel_to_update.parallel_offsets[-1].vertex_indices[-1]

        # the point where the two channels meet (connection node) has to be included in the wedge fill points
        # if any of the channels does have a width starting at 0, we use that point
        # if neither channel has a width starting at 0, the x, y, z and index have to be calculated
        wedge_fill_points = []
        if 0 in channel_to_update.unique_widths:
            po = channel_to_update.parallel_offset_at(0)
            wedge_fill_points.append(po.points[channel_to_update_idx])
        elif 0 in wedge_fill_points_source.unique_widths:
            po = wedge_fill_points_source.parallel_offset_at(0)
            wedge_fill_points.append(po.points[wedge_fill_points_source_idx])
        else:
            first_width = channel_to_update.unique_widths[0]
            po_1 = channel_to_update.parallel_offset_at(first_width / 2)
            point_1 = po_1.points[channel_to_update_idx]
            po_2 = channel_to_update.parallel_offset_at(-1 * first_width / 2)
            point_2 = po_2.points[channel_to_update_idx]
            x = (point_1.x + point_2.x) / 2
            y = (point_1.y + point_2.y) / 2
            z = (point_1.z + point_2.z) / 2
            point_to_add = IndexedPoint(x, y, z, index=last_index + 1)
            wedge_fill_points.append(point_to_add)
            last_index += 1

        for i, width in enumerate(channel_to_update.unique_widths):
            if width > 0:
                channel_to_update_offsets.append(width / 2)
                offset = width * channel_to_update_side / 2
                po = channel_to_update.parallel_offset_at(offset)
                channel_to_update_points.append(po.points[channel_to_update_idx])

        # Append start or end vertices of all other_channel's parallel offsets to self._wedge_fill_points
        # left is negative, right is positive

        for width in wedge_fill_points_source.unique_widths:
            if width > 0:
                wedge_fill_points_source_offsets.append(width / 2)
                offset = width * wedge_fill_points_source_side / 2
                po = wedge_fill_points_source.parallel_offset_at(offset)
                existing_point = po.points[wedge_fill_points_source_idx]
                wedge_fill_point = IndexedPoint(
                    existing_point.geom, index=existing_point.index
                )
                wedge_fill_point.index = last_index + 1
                wedge_fill_points.append(wedge_fill_point)
                last_index += 1

        # Generate triangles to connect the added points to the existing points
        for triangle in triangulate_between(
            side_1_points=channel_to_update_points,
            side_1_distances=channel_to_update_offsets,
            side_2_points=wedge_fill_points,
            side_2_distances=wedge_fill_points_source_offsets,
        ):
            self._wedge_fill_triangles.append(triangle)
        channel_to_update._wedge_fill_points += wedge_fill_points
        extra_point = Point(
            wedge_fill_points_source.geometry.coords[wedge_fill_points_source_idx]
        )
        position = (
            0
            if wedge_fill_points_source_idx == 0
            else wedge_fill_points_source.geometry.length
        )
        width_at_extra_point = wedge_fill_points_source.max_width_at(position)
        self._extra_outline.append(extra_point.buffer(width_at_extra_point / 2))

    def as_query(self):
        selects = []
        for i, tri in enumerate(self.triangles):
            selects.append(
                f"SELECT {i + 1} as id, geom_from_wkt('{str(tri.geometry.wkt)}')"
            )
        return "\nUNION\n".join(selects)


class ParallelOffset:
    def __init__(self, parent: Channel, offset_distance):
        """
        The side is determined by the sign of the distance parameter (negative for right side offset, positive for left
        side offset). Left and right are determined by following the direction of the given geometric points of the
        LineString.
        """
        self.parent = parent
        self.geometry = parent.geometry.parallel_offset(offset_distance)
        if self.geometry.is_empty:
            raise EmptyOffsetError
        if type(self.geometry) != LineString:
            raise InvalidOffsetError
        self.offset_distance = offset_distance
        width = np.abs(self.offset_distance * 2)
        cross_section_location_points = []
        for pos in self.parent.cross_section_location_positions:
            location_xy = self.parent.geometry.interpolate(pos)
            cross_section_location_points.append(
                nearest_points(location_xy, self.geometry)[0]
            )
        cross_section_location_positions = [
            self.geometry.project(point) for point in cross_section_location_points
        ]
        heights_at_cross_sections = [
            xsec.height_at(width) for xsec in self.parent.cross_section_locations
        ]
        self.vertex_positions = [
            self.geometry.project(Point(vertex)) for vertex in self.geometry.coords
        ]
        self.heights_at_vertices = np.interp(
            self.vertex_positions,
            cross_section_location_positions,
            heights_at_cross_sections,
        )
        self.vertex_indices = None

    @property
    def points(self):
        result = []
        for i, (x, y) in enumerate(self.geometry.coords):
            result.append(IndexedPoint(x, y, self.heights_at_vertices[i], index=self.vertex_indices[i]))
        return result

    def set_vertex_indices(self, first_vertex_index):
        self.vertex_indices = list(
            range(first_vertex_index, first_vertex_index + len(self.geometry.coords))
        )

    def triangle_is_valid(self, triangle_points, other_parallel_offset):
        """Return True if none of the sides of the triangle crosses the parallel offsets that should enclose it"""
        valid = True
        for start, end in [(0, 1), (0, 2), (1, 2)]:
            line = LineString([triangle_points[start], triangle_points[end]])
            if self.geometry.crosses(line) or other_parallel_offset.geometry.crosses(
                line
            ):
                valid = False
        return valid

    def triangulate(self, other):
        return triangulate_between(
            side_1_points=self.points,
            side_1_distances=self.vertex_positions,
            side_2_points=other.points,
            side_2_distances=other.vertex_positions,
        )


def triangulate_between(
    side_1_points: List[IndexedPoint],
    side_1_distances: List[float],
    side_2_points: List[IndexedPoint],
    side_2_distances: List[float],
) -> Iterator[Triangle]:
    """
    Generate a set of triangles that fills the space between two lines (side 1 and side 2)

    :param side_1_points: list of points located along a line on side 1
    :param side_1_distances: distance along the line on which these points are located
    :param side_2_points: list of points located along a line on side 2
    :param side_2_distances: distance along the line on which these points are located
    """
    side_1_line = LineString([point.geom for point in side_1_points])
    side_2_line = LineString([point.geom for point in side_2_points])
    side_1_idx = 0
    side_2_idx = 0
    side_1_last_idx = len(side_1_points) - 1
    side_2_last_idx = len(side_2_points) - 1
    last_move = 1

    while (side_1_idx < side_1_last_idx) or (side_2_idx < side_2_last_idx):
        triangle_points = [side_1_points[side_1_idx], side_2_points[side_2_idx]]
        # first we handle the case where the end of the line has been reached at one of the sides
        if side_1_idx == side_1_last_idx:
            side_2_idx += 1
            triangle_points.append(side_2_points[side_2_idx])
        elif side_2_idx == side_2_last_idx:
            side_1_idx += 1
            triangle_points.append(side_1_points[side_1_idx])

        # then we handle the 'normal' case when we are still halfway at both sides
        else:
            next_side_1_vertex_pos = side_1_distances[side_1_idx + 1]
            next_side_2_vertex_pos = side_2_distances[side_2_idx + 1]
            if next_side_2_vertex_pos == next_side_1_vertex_pos:
                move = 2 if last_move == 1 else 1
            elif next_side_2_vertex_pos > next_side_1_vertex_pos:
                move = 1
            else:
                move = 2

            # switch move side if moving on that side results in invalid triangle
            if move == 2:
                additional_point = side_2_points[side_2_idx + 1]
                test_triangle = Triangle(triangle_points + [additional_point])
                if not test_triangle.is_between(side_1_line, side_2_line):
                    move = 1
            else:
                additional_point = side_1_points[side_1_idx + 1]
                test_triangle = Triangle(triangle_points + [additional_point])
                if not test_triangle.is_between(side_1_line, side_2_line):
                    move = 2

            if move == 2:
                side_2_idx += 1
                triangle_points.append(side_2_points[side_2_idx])
                last_move = 2
            else:
                side_1_idx += 1
                triangle_points.append(side_1_points[side_1_idx])
                last_move = 1

        yield Triangle(points=triangle_points)


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
            if connection_node_id in [
                channel.connection_node_start_id,
                channel.connection_node_end_id,
            ]:
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
        if connection_node_id in [
            channel1.connection_node_start_id,
            channel1.connection_node_end_id,
        ] and connection_node_id in [
            channel2.connection_node_start_id,
            channel2.connection_node_end_id,
        ]:
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


def find_wedge_channels(
    channels: List[Channel], connection_node_id: int
) -> Union[Tuple[Channel, Channel], Tuple[None, None]]:
    """In a list of channels that connect to the same connection node, find a pair of channels that connect at
    a > 180 degree angle, so that there is a wedge-shaped gap between them"""
    azimuth_channel_dict = {}
    for channel in channels:
        key = round(channel.azimuth_at(connection_node_id), 6)
        azimuth_channel_dict[key] = channel
    sorted_azimuths = list(azimuth_channel_dict.keys())
    sorted_azimuths.sort(reverse=True)
    sorted_azimuths = [sorted_azimuths[-1]] + sorted_azimuths + [sorted_azimuths[0]]
    for i in range(len(sorted_azimuths) - 1):
        channel_1 = azimuth_channel_dict[sorted_azimuths[i]]
        channel_2 = azimuth_channel_dict[sorted_azimuths[i + 1]]
        angle = ccw_angle(channel_1, channel_2)
        if angle > 180:
            return channel_1, channel_2
    return None, None


def fill_wedges(channels: List[Channel]):
    connection_node_channels_dict = get_channels_per_connection_node(channels)
    for connection_node_id, channels in connection_node_channels_dict.items():
        channel1, channel2 = find_wedge_channels(
            channels=channels, connection_node_id=connection_node_id
        )
        if channel1 and channel2:
            channel1.fill_wedge(channel2)
