from enum import Enum
from typing import Iterator, List, Union, Set, Sequence, Tuple

import numpy as np
from shapely import __version__ as shapely_version
if int(shapely_version.split(".")[0]) < 2:
    raise Exception(f"Required Shapely version >= 2.0.0. Installed Shapely version: {shapely_version}")
from shapely import wkt
from shapely.geometry import LineString, MultiPolygon, Point, Polygon
from shapely.ops import unary_union, nearest_points, transform

# Shapely method "offset_curve" docs: The side is determined by the sign of the distance parameter
# (negative for right side offset, positive for left side offset). Left and right are determined by following
# the direction of the given geometric points of the LineString.
RIGHT = -1
LEFT = 1


class SupportedShape(Enum):
    TABULATED_RECTANGLE = 5
    TABULATED_TRAPEZIUM = 6
    YZ = 7


def is_monotonically_increasing(a: np.array, equal_allowed=False):
    if equal_allowed:
        return np.all(a[1:] >= a[0:-1])
    return np.all(a[1:] > a[0:-1])


def parse_cross_section_table(
        table: str,
        cross_section_shape: int,
        wall_displacement: float = 0
) -> Tuple[np.array, np.array]:
    """
    Returns [y_ordinates], [z_ordinates]
    """
    if cross_section_shape in (SupportedShape.TABULATED_RECTANGLE.value, SupportedShape.TABULATED_TRAPEZIUM.value):
        heights = list()
        widths = list()
        for row in table.split("\n"):
            height, width = row.split(",")
            if len(heights) == 0:
                # first pass
                heights.append(float(height))
                widths.append(float(width))
            else:
                if float(width) < widths[-1]:
                    raise WidthsNotIncreasingError
                if cross_section_shape == SupportedShape.TABULATED_RECTANGLE.value:
                    # add extra height/width entry to convert tabulated rectangle to tabulated trapezium
                    # but only if width is different from previous width
                    if float(width) > widths[-1]:
                        heights.append(float(height))
                        widths.append(float(widths[-1]))
                heights.append(float(height))
                widths.append(float(width))
        # convert to YZ
        if widths[0] == 0:  # do not duplicate middle y value if it is 0
            y_ordinates = np.hstack([np.flip(widths)/-2, np.array(widths)[1:]/2])
            z_ordinates = np.hstack([np.flip(heights), np.array(heights)[1:]])
        else:
            y_ordinates = np.hstack([np.flip(widths)/-2, np.array(widths)/2])
            z_ordinates = np.hstack([np.flip(heights), heights])
        y_ordinates += np.max(widths)/2
    elif cross_section_shape == SupportedShape.YZ.value:
        y_list = list()
        z_list = list()
        for row in table.split("\n"):
            y, z = row.split(",")
            y_list.append(float(y))
            z_list.append(float(z))
        y_ordinates = np.array(y_list)
        z_ordinates = np.array(z_list)
        if not is_monotonically_increasing(y_ordinates, equal_allowed=True):
            # equal Y is allowed, will be fixed with wall displacement
            raise YNotIncreasingError

    else:
        raise ValueError(f"Unsupported cross_section_shape {cross_section_shape}")

    # apply wall displacement to vertical segments
    while not is_monotonically_increasing(y_ordinates):
        y_ordinates[1:][y_ordinates[1:] == y_ordinates[:-1]] += wall_displacement
        # remove YZ coordinates that have been 'taken over' by the previous ones due to wall displacement
        valid_ordinates = y_ordinates[1:] >= y_ordinates[:-1]
        while np.sum(np.invert(valid_ordinates)) > 0:
            valid_ordinates = y_ordinates[1:] >= y_ordinates[:-1]
            valid_mask = np.hstack([np.array([True]), valid_ordinates])
            y_ordinates = y_ordinates[valid_mask]
            z_ordinates = z_ordinates[valid_mask]

    return y_ordinates, z_ordinates


def simplify(y_ordinates: np.array, z_ordinates: np.array, tolerance: float) -> Tuple[np.array, np.array]:
    """
    Simplify a YZ cross-section using shapely LineString.simplify()
    """
    linestring = LineString(np.stack([y_ordinates, z_ordinates], axis=1))
    simplified_linestring = linestring.simplify(tolerance)
    coord_array = simplified_linestring.coords.xy
    y_ordinates, z_ordinates = np.array(coord_array)
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


def variable_buffer(linestring: LineString, radii: Sequence[float], shifts: Sequence[float] = None) -> Polygon:
    """
    Create a buffer around a Linestring, for which the buffer distance varies per vertex
    By default, the buffer is symmetrical. This can be varied by specifying the ``shifts``

    :param linestring: line to be buffered
    :param radii: buffer distance per vertex (must be >= 0
    :param shifts: shift of the center of the buffer. right = negative, left = positive
    """
    assert len(linestring.coords) == len(radii)
    assert np.all(np.array(radii) >= 0)
    vertices = [Point(coord) for coord in linestring.coords]
    if shifts is not None:
        # shift each vertex onto the offset_curve with given shift
        vertices = [
            nearest_points(linestring if shifts[i] == 0 else linestring.offset_curve(shifts[i]), vertices[i])[0]
            for i, coord in enumerate(linestring.coords)
        ]
    buffered_points = [
        v.buffer(radii[i]) for i, v in enumerate(vertices)
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

class MinYNotZeroError(ValueError):
    """"Raised when a YZ cross-section's lowest value is not 0"""

    pass


class YNotIncreasingError(ValueError):
    """Raised when one a Y value of a YZ cross section <= than the previous Y of that crosssection"""

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
        self.points: List[IndexedPoint] = points
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

    def is_between(self, line_1: Union[Point, LineString], line_2: Union[Point, LineString]):
        if type(line_1) == Point or type(line_2) == Point:
            return True
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
        y_ordinates: np.array,
        z_ordinates: np.array,
        geometry: Point,
        parent=None,
    ):
        """
        Note: adds reference level to z_ordinates

        :param reference_level:
        :param bank_level:
        :param y_ordinates: Use ``parse_cross_section_table`` to convert tabulated to yz
        :param z_ordinates: Use ``parse_cross_section_table`` to convert tabulated to yz. Input has 0 as lowest z.
        :param geometry:
        :param parent:
        """
        if not np.min(y_ordinates) == 0:
            raise MinYNotZeroError
        if not is_monotonically_increasing(y_ordinates):
            raise YNotIncreasingError

        self.reference_level = reference_level
        self.bank_level = bank_level
        self.y_ordinates = y_ordinates
        self.z_ordinates = z_ordinates + reference_level
        self.geometry = geometry
        self.parent = parent

    @classmethod
    def from_qgs_feature(cls, feature, wall_displacement: float, simplify_tolerance: float):
        """
        wall_displacement is used as simplify tolerance for the cross-section. remaining vertical segments are made
        diagonal by displacing the top or bottom by wall_displacement
        """
        qgs_geometry = feature.geometry()
        wkt_geometry = qgs_geometry.asWkt()
        shapely_geometry = wkt.loads(wkt_geometry)
        cross_section_shape = feature.attribute("cross_section_shape")
        table = feature.attribute("cross_section_table")
        y, z = parse_cross_section_table(
            table=table,
            cross_section_shape=cross_section_shape,
            wall_displacement=wall_displacement
        )
        y, z = simplify(y, z, tolerance=simplify_tolerance)

        return cls(
            geometry=shapely_geometry,
            reference_level=feature.attribute("reference_level"),
            bank_level=feature.attribute("bank_level"),
            y_ordinates=y,
            z_ordinates=z,
        )

    @property
    def position(self):
        if self.parent is None:
            return
        return self.parent.geometry.project(self.geometry)

    @property
    def max_width(self):
        return np.max(self.y_ordinates)

    @property
    def thalweg_y(self):
        """Returns distance between the start of the cross-section at the left bank and the lowest point of the
        cross-section. The thalweg is located at the average y index of all points with the minimum z value"""
        z0_indices = np.where(self.z_ordinates == np.min(self.z_ordinates))[0]
        average_z0_index = np.average(z0_indices)
        if int(average_z0_index) == average_z0_index:
            return self.y_ordinates[int(average_z0_index)]
        else:
            # linear interpolation between y before and y after, only using y's where z=min(z)
            z0_index_before = z0_indices[z0_indices < average_z0_index][-1]
            z0_index_after = z0_indices[z0_indices > average_z0_index][0]
            y_before = self.y_ordinates[z0_index_before]
            y_after = self.y_ordinates[z0_index_after]
            return y_before + ((average_z0_index-z0_index_before)/(z0_index_after-z0_index_before))*(y_after-y_before)

    @property
    def offsets(self):
        """
        Return array of y_ordinates, but relative to the thalweg
        and using the shapely offset_curve logic of right = negative and left is positive
        """
        return self.thalweg_y - self.y_ordinates

    def z_at(self, offset: float) -> float:
        """Get interpolated z at given offset"""

        # offsets and z_ordinates are flipped ([::-1]) because offsets must be monotonically increasing, but is
        # monotonically decreasing due to the shapely offset_curve right = -1 and left = +1 logic
        return np.interp(offset, self.offsets[::-1], self.z_ordinates[::-1])


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
        self.cross_section_locations: List[CrossSectionLocation] = []
        self.geometry: LineString = geometry
        self.parallel_offsets: List[ParallelOffset] = []
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
    def thalweg_ys(self) -> np.array:
        """Array of y ordinates of the thalweg of each cross-section location along the channel"""
        return np.array([x.thalweg_y for x in self.cross_section_locations])

    @property
    def unique_offsets(self) -> np.array:
        """Unique offsets for entire channel, see ``CrossSectionLocation.offsets`` documentation"""
        offsets_list = [xsec.offsets for xsec in self.cross_section_locations]
        all_offsets_array = np.hstack(offsets_list)
        return np.array(np.unique(all_offsets_array))

    @property
    def cross_section_location_positions(self) -> np.array:
        """Array of cross-section location positions along the channel"""
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
        thalweg_ys = [self.thalweg_y_at(position) for position in self.vertex_positions]
        shifts = -1*(np.array(radii) - np.array(thalweg_ys))
        result = variable_buffer(self.geometry, radii, shifts)

        # add extra outline generated by self.fill_wedge()
        for extra in self._extra_outline:
            result = result.union(extra)
        return result

    def add_cross_section_location(self, cross_section_location: CrossSectionLocation):
        """Become the parent of the cross section location"""
        cross_section_location.parent = self
        self.cross_section_locations.append(cross_section_location)
        self.cross_section_locations.sort(key=lambda x: x.position)

    def max_width_at(self, position: float) -> float:
        """Interpolated max cross-sectional width at given position along the channel"""
        return np.interp(
            position, self.cross_section_location_positions, self.max_widths
        )

    def thalweg_y_at(self, position: float) -> float:
        """Interpolated y ordinate of thalweg at given position along the channel"""
        return np.interp(
            position, self.cross_section_location_positions, self.thalweg_ys
        )

    def generate_parallel_offsets(self, offset_0: bool = False):
        """
        Generate a set of lines parallel to the input linestring, at both sides of the line
        Offsets are sorted from ``LEFT`` to ``RIGHT``

        :param offset_0: guarantee an offset at 0, even if this does not occur in the channel's ``unique_offsets``
        """
        self.parallel_offsets = []
        offsets = sorted(list(set(self.unique_offsets) | {0}), reverse=RIGHT == -1) if offset_0 else self.unique_offsets
        self.parallel_offsets = [ParallelOffset(parent=self, offset_distance=offset) for offset in offsets]

        last_vertex_index = -1
        # -1 so that we have 0-based indexing, because QgsMesh vertices have 0-based indices too
        for po in self.parallel_offsets:
            po.set_vertex_indices(first_vertex_index=last_vertex_index + 1)
            last_vertex_index = po.vertex_indices[-1]

    def parallel_offset_at(self, offset_distance):
        """
        Find the ParallelOffset at given ``offset_distance``
        """
        if offset_distance not in self.unique_offsets:
            raise ValueError(
                f"Parallel offset not found at offset distance {offset_distance}. "
                f"Channel between nodes {self.connection_node_start_id} and "
                f"{self.connection_node_end_id}. Available offset distances: {self.unique_offsets}"
            )
        for po in self.parallel_offsets:
            if po.offset_distance == offset_distance:
                return po
        raise ValueError(
            f"Parallel offset not found at offset distance {offset_distance}. "
            f"Channel between nodes {self.connection_node_start_id} and "
            f"{self.connection_node_end_id}. Available offset distances: {self.unique_offsets}"
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
        # head of `self` connects to tail of `other` | -->-->
        # wedge is added to `self`
        if self.connection_node_end_id == other.connection_node_start_id:
            channel_to_update = self
            channel_to_update_idx = -1  # end
            if ccw_angle(self, other) > 180:
                channel_to_update_side = RIGHT
                wedge_fill_points_source_side = RIGHT
            else:
                channel_to_update_side = LEFT
                wedge_fill_points_source_side = LEFT
            wedge_fill_points_source = other
            wedge_fill_points_source_idx = 0  # start

        # head of `self` connects to head of `other` | --><--
        # wedge is added to `self`
        elif self.connection_node_end_id == other.connection_node_end_id:
            channel_to_update = self
            channel_to_update_idx = -1  # end
            if ccw_angle(self, other) > 180:
                channel_to_update_side = RIGHT
                wedge_fill_points_source_side = LEFT
            else:
                channel_to_update_side = LEFT
                wedge_fill_points_source_side = RIGHT
            wedge_fill_points_source = other
            wedge_fill_points_source_idx = -1  # end

        # tail of `self` connects to tail of `other` | <---->
        # wedge is added to `self`
        elif self.connection_node_start_id == other.connection_node_start_id:
            channel_to_update = self
            channel_to_update_idx = 0  # start
            if ccw_angle(self, other) > 180:
                channel_to_update_side = LEFT
                wedge_fill_points_source_side = RIGHT
            else:
                channel_to_update_side = RIGHT
                wedge_fill_points_source_side = LEFT
            wedge_fill_points_source = other
            wedge_fill_points_source_idx = 0  # start

        # tail of `self` is connected to head of `other` | <--<--
        # wedge is connected to `other`
        elif self.connection_node_start_id == other.connection_node_end_id:
            channel_to_update = other
            channel_to_update_idx = -1  # end
            wedge_fill_points_source = self
            wedge_fill_points_source_idx = 0  # start
            if ccw_angle(self, other) > 180:
                channel_to_update_side = LEFT
                wedge_fill_points_source_side = LEFT
            else:
                channel_to_update_side = RIGHT
                wedge_fill_points_source_side = RIGHT

        # channels are not connected | -->          -->
        else:
            raise ValueError("Channels are not connected")

        # Regenerate parallel offsets if offset 0 is not included
        if 0 not in channel_to_update.unique_offsets:
            channel_to_update.generate_parallel_offsets(offset_0=True)

        channel_to_update_offsets = []
        channel_to_update_points = []

        # add points from `channel_to_update`, including the 0 point
        for po in channel_to_update.parallel_offsets:
            if po.offset_distance * channel_to_update_side >= 0:
                channel_to_update_offsets.append(po.offset_distance)
                channel_to_update_points.append(po.points[channel_to_update_idx])

        # Append start or end vertices of all other_channel's parallel offsets to self._wedge_fill_points
        # left is positive, right is negative

        # add points from the other channel (`wedge_fill_points_source`)
        wedge_fill_points = []
        wedge_fill_points_source_offsets = []
        last_index = channel_to_update.parallel_offsets[-1].vertex_indices[-1]
        for po in wedge_fill_points_source.parallel_offsets:
            if po.offset_distance * wedge_fill_points_source_side > 0:
                wedge_fill_points_source_offsets.append(po.offset_distance)
                existing_point = po.points[wedge_fill_points_source_idx]
                wedge_fill_points.append(
                    IndexedPoint(
                        existing_point.geom, index=last_index + 1
                    )
                )
                last_index += 1

        # Generate triangles to connect the added points to the existing points
        for triangle in triangulate_between(
            side_1_points=channel_to_update_points,
            side_1_distances=channel_to_update_offsets,
            side_2_points=wedge_fill_points,
            side_2_distances=wedge_fill_points_source_offsets,
        ):
            self._wedge_fill_triangles.append(triangle)

        # Add wedge fill points
        channel_to_update._wedge_fill_points += wedge_fill_points

        # test that point indices are unique
        point_indices = [point.index for point in channel_to_update.points]
        assert len(set(point_indices)) == len(point_indices)

        # Create extra outline buffer for the wedge
        extra_point = Point(
            wedge_fill_points_source.geometry.coords[wedge_fill_points_source_idx]
        )
        position = (
            0
            if wedge_fill_points_source_idx == 0
            else wedge_fill_points_source.geometry.length
        )
        width_at_extra_point = wedge_fill_points_source.max_width_at(position)
        thalweg_y_at_extra_point = wedge_fill_points_source.thalweg_y_at(position)
        shift = -1*(width_at_extra_point - thalweg_y_at_extra_point)
        extra_point_shifted = nearest_points(
            wedge_fill_points_source.geometry
                if shift == 0
                else wedge_fill_points_source.geometry.offset_curve(shift),
            extra_point
        )[0]
        self._extra_outline.append(extra_point_shifted.buffer(width_at_extra_point / 2))

    def as_query(self):
        selects = []
        for i, tri in enumerate(self.triangles):
            selects.append(
                f"SELECT {i + 1} as id, geom_from_wkt('{str(tri.geometry.wkt)}') as geom /*:polygon:28992*/"
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
        self.geometry = parent.geometry \
            if offset_distance == 0 \
            else parent.geometry.offset_curve(distance=offset_distance)
        if self.geometry.is_empty:
            raise EmptyOffsetError
        if type(self.geometry) != LineString:
            raise InvalidOffsetError
        self.offset_distance = offset_distance
        cross_section_location_points = []
        for pos in self.parent.cross_section_location_positions:
            location_xy = self.parent.geometry.interpolate(pos)
            cross_section_location_points.append(
                nearest_points(location_xy, self.geometry)[0]
            )
        cross_section_location_positions = [
            self.geometry.project(point) for point in cross_section_location_points
        ]
        z_ordinates_at_cross_sections = [
            xsec.z_at(self.offset_distance) for xsec in self.parent.cross_section_locations
        ]
        self.vertex_positions = [
            self.geometry.project(Point(vertex)) for vertex in self.geometry.coords
        ]
        self.heights_at_vertices = np.interp(
            self.vertex_positions,
            cross_section_location_positions,
            z_ordinates_at_cross_sections,
        )
        self.vertex_indices = None

    @property
    def points(self) -> List[IndexedPoint]:
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
    side_1_line = LineString([point.geom for point in side_1_points]) if len(side_1_points) > 1 else side_1_points[0].geom
    side_2_line = LineString([point.geom for point in side_2_points]) if len(side_2_points) > 1 else side_2_points[0].geom
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
    """
    In a list of Channels, find cases where a wedge needs to be filled and fill them, i.e. add wedge triangles to
    one of the two channels involved.

    We iterate over each junction (connection node), find the two channels in the junction between which a wedge needs
    to be filled (i.e. angle between them is > 180 degrees), and fill them once (i.e. we only call
    ``channel1.fill_wedge(channel2)`` and not ``channel2.fill_wedge(channel1)``
    """
    connection_node_channels_dict = get_channels_per_connection_node(channels)
    for connection_node_id, channels in connection_node_channels_dict.items():
        channel1, channel2 = find_wedge_channels(
            channels=channels, connection_node_id=connection_node_id
        )
        if channel1 and channel2:
            channel1.fill_wedge(channel2)
