from operator import attrgetter
from typing import List, Union, Tuple

import numpy as np
from osgeo import ogr, osr, gdal
from shapely import wkt
from shapely.geometry import LineString, Point, Polygon, MultiPoint
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
    def __init__(self, geometry: LineString):
        self.cross_section_locations = []
        self.geometry = geometry
        self.parallel_offsets = []

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
        return cls(geometry=shapely_geometry)

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

    @property
    def points(self):
        """Returns all points of all parallel offsets ordered by vertex index"""
        # outline = self.outline
        all_points = []
        for po in self.parallel_offsets:
            all_points += po.points
        # result = [point for point in all_points if outline.intersects(point)]
        return all_points

    @property
    def indexed_points(self):
        return [po.points for po in self.parallel_offsets]

    # def triangles(self):
    #     indexed_points = self.indexed_points
    #     for i in range(len(indexed_points) - 1):
    #         next_po_points = MultiPoint(indexed_points[i+1])
    #         for j in range(len(indexed_points[i]) - 1):
    #             third_vertex_2d = nearest_points(next_po_points, indexed_points[i][j])[0]  # nearest_points loses z ord
    #             intersecting_vertices_3d = [point for point in indexed_points[i+1] if point.intersects(third_vertex_2d)]
    #             third_vertex = intersecting_vertices_3d[0]
    #             triangle_vertices = [indexed_points[i][j], indexed_points[i][j+1], third_vertex]
    #             yield Polygon(LineString(triangle_vertices))
    #     for i in range(len(indexed_points) - 1, 0, -1):
    #         next_po_points = MultiPoint(indexed_points[i-1])
    #         for j in range(len(indexed_points[i]) - 1, 0, - 1):
    #             third_vertex_2d = nearest_points(next_po_points, indexed_points[i][j])[0]  # nearest_points loses z ord
    #             intersecting_vertices_3d = [point for point in indexed_points[i-1] if point.intersects(third_vertex_2d)]
    #             third_vertex = intersecting_vertices_3d[0]
    #             triangle_vertices = [indexed_points[i][j], indexed_points[i][j-1], third_vertex]
    #             yield Polygon(LineString(triangle_vertices))
    @property
    def triangles(self) -> List[Triangle]:
        parallel_offsets = self.parallel_offsets
        for i in range(len(parallel_offsets)-1):
            for tri in parallel_offsets[i].triangulate(parallel_offsets[i+1]):
                yield tri


class ChannelGroup(Channel):
    """One or more Channels of which the geometry can be linemerged to a single linestring"""
    def __init__(self, channels: List[Channel]):
        geometries = [channel.geometry for channel in channels]
        merged_geometry = linemerge(geometries)
        if not isinstance(self.geometry, LineString):
            raise ValueError('Input channel geometries cannot be merged into a single LineString')
        super().__init__(geometry=merged_geometry)

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


# def rasterize_channels(
#         sqlite,
#         dem,
#         output_raster,
#         profile_or_bank_level,
#         burn_in_dem,
#         higher_or_lower_only,
#         add_value,
#         proj_target,
#         ids=None
# ):
#     """
#     Main function calling other functions
#
#     First channel and cross section data is gathered
#
#     Channel in channels loops over all channels:
#         Get cross-sectional data
#         Create line-strings over length channel
#         Get interpolated heigths over these lines
#         loop loops over all channel lines in the length of the channel:
#             Loop2 loops over points in the length of channel:
#                 Interpolated height is described to point
#                 Points that are within a previously defined channel outline are skipped to prevent messy interpolation
#                 Boundary points are gathered to form the channel outline polygon (which will be used for cropping the
#                 channel raster)
#
#     After the loop over channels:
#         Dissolve and buffering (twice) of the channel outline to create a valid cropping layer
#         Points are rasterized
#         Interpolation between heights of points
#         Cropping interpolated raster to channel outline
#         Merging with dem
#         Write this to raster or write minimum/maximum to raster
#     """
#     try:
#         if os.path.exists(output_raster):
#             os.remove(output_raster)
#             logging.info("Found existing raster named " f"{output_raster}")
#             logging.info("Removed it to create a new one...")
#
#         channels = features_from_sqlite(proj_target, sqlite, "v2_channel")
#         logging.info("List of enriched shapely geometries gained for: channels")
#         cross_section_locations = features_from_sqlite(
#             proj_target, sqlite, "v2_cross_section_location"
#         )
#         logging.info(
#             "List of enriched shapely geometries gained for: cross_section_locations"
#         )
#
#         conn = create_connection(sqlite)
#         cur = conn.cursor()
#
#         count = 0
#         save_time = time.time()
#         for channel in channels:
#             if channel.id in ids or ids is None:
#                 logging.info("")
#                 logging.info("Channel id = " f"{channel.id}")
#                 count = count + 1
#                 if count != 1:  # if count == 1 polygon layer does not exist yet
#                     polygons = [
#                         pol for pol in fiona.open("/vsimem/tmp/channel_outline.shp")
#                     ]
#                 channel_xsecs = []
#                 for xsec_loc in cross_section_locations:
#                     if xsec_loc.channel_id == channel.id:
#                         xsec_loc.position = channel.project(xsec_loc, normalized=True)
#                         channel_xsecs.append(xsec_loc)
#
#                 (
#                     channel_max_widths,
#                     channel_all_widths_flat,
#                 ) = get_channel_widths_and_heigths(
#                     cur,
#                     add_value,
#                     profile_or_bank_level,
#                     channel=channel,
#                     cross_section_locations=channel_xsecs
#                 )
#                 channel_offsets = two_sided_parallel_offsets(
#                     channel, channel_all_widths_flat
#                 )
#                 all_profiles_interpolated = {}
#                 for xsec in channel_xsecs:
#                     interpolated_height = []
#                     for width in channel_all_widths_flat:
#                         interpolated_height.append(
#                             np.interp(width, xsec.widths, xsec.heights)
#                         )
#                     all_profiles_interpolated[xsec.position] = interpolated_height
#                 all_profiles_interpolated[float(0)] = all_profiles_interpolated[
#                     min(all_profiles_interpolated.keys())
#                 ]
#                 all_profiles_interpolated[float(1)] = all_profiles_interpolated[
#                     max(all_profiles_interpolated.keys())
#                 ]
#                 positions = list(all_profiles_interpolated.keys())
#                 positions.sort()
#
#                 all_points = []
#                 first_boundary_points = []
#                 last_boundary_points = []
#                 boundary_points = []
#                 loop = range(1, len(channel_offsets))
#                 for offset_counter in range(1, len(channel_offsets)):
#                     channel_offset_i = channel_offsets[offset_counter]
#                     y = []
#                     for position_counter in range(0, len(positions)):
#                         if offset_counter > len(all_profiles_interpolated[positions[0]]) - 1:
#                             chn2 = offset_counter - len(all_profiles_interpolated[positions[0]])
#                             y.append(all_profiles_interpolated[positions[position_counter]][chn2])
#                         else:
#                             y.append(all_profiles_interpolated[positions[position_counter]][offset_counter])
#                     if offset_counter > len(all_profiles_interpolated[0]):
#                         channel_offset_i = LineString(channel_offset_i.coords[::-1])
#
#                     loop2 = range(1, round(channel_offset_i.length / 2))
#                     for offset_counter2 in loop2:
#                         if profile_or_bank_level == "bank_level":
#                             if (
#                                     offset_counter2 == loop[int(len(loop) / 2 - 1.5)] or offset_counter == loop[-1]
#                             ):  # lines along banks of channel
#                                 skip_point = False
#                                 point = channel_offset_i.interpolate(
#                                     2 * offset_counter / channel_offset_i.length, normalized=True
#                                 )
#                                 point.height = np.interp(
#                                     channel.project(point, normalized=True), positions, y
#                                 )
#                                 if count != 1:
#                                     if offset_counter <= 10 or offset_counter >= (len(loop2) - 10):
#                                         for polygon in polygons:
#                                             if point.within(shape(polygon["geometry"])):
#                                                 skip_point = True
#                                 if skip_point:
#                                     logging.info(
#                                         "One of the points is within another channel outline, so is skipped"
#                                     )
#                                 else:
#                                     all_points.append(point)
#                                 if offset_counter == loop[int(len(loop) / 2 - 1.5)]:
#                                     if offset_counter == loop2[0]:
#                                         first_boundary_points.append(
#                                             Point(channel_offset_i.coords[0][0], channel_offset_i.coords[0][1])
#                                         )
#                                     first_boundary_points.append(point)
#                                     boundary_points.append(point)
#                                     if offset_counter == loop2[-1]:
#                                         first_boundary_points.append(
#                                             Point(
#                                                 channel_offset_i.coords[-1][0], channel_offset_i.coords[-1][1]
#                                             )
#                                         )
#                                 elif offset_counter == loop[-1]:
#                                     if offset_counter == loop2[0]:
#                                         last_boundary_points.append(
#                                             Point(channel_offset_i.coords[0][0], channel_offset_i.coords[0][1])
#                                         )
#                                     last_boundary_points.append(point)
#                                     boundary_points.append(point)
#                                     if offset_counter == loop2[-1]:
#                                         last_boundary_points.append(
#                                             Point(
#                                                 channel_offset_i.coords[-1][0], channel_offset_i.coords[-1][1]
#                                             )
#                                         )
#                             else:  # we do not need to gather other points than the boundary points for the bank
#                                 # level tool
#                                 continue
#                         else:
#                             skip_point = False
#                             point = channel_offset_i.interpolate(
#                                 2 * offset_counter / channel_offset_i.length, normalized=True
#                             )
#                             point.height = np.interp(
#                                 channel.project(point, normalized=True), positions, y
#                             )
#                             if count != 1:
#                                 if offset_counter <= 10 or offset_counter >= (len(loop2) - 10):
#                                     for polygon in polygons:
#                                         if point.within(shape(polygon["geometry"])):
#                                             skip_point = True
#                             if skip_point:
#                                 logging.info(
#                                     "One of the points is within another channel outline, so is skipped"
#                                 )
#                             else:
#                                 all_points.append(point)
#                             if (
#                                     offset_counter == loop[int(len(loop) / 2 - 1.5)]
#                             ):  # line along one of the banks
#                                 if offset_counter == loop2[0]:
#                                     first_boundary_points.append(
#                                         Point(channel_offset_i.coords[0][0], channel_offset_i.coords[0][1])
#                                     )
#                                 first_boundary_points.append(point)
#                                 boundary_points.append(point)
#                                 if offset_counter == loop2[-1]:
#                                     first_boundary_points.append(
#                                         Point(channel_offset_i.coords[-1][0], channel_offset_i.coords[-1][1])
#                                     )