from copy import deepcopy
from operator import attrgetter
from pathlib import Path
from typing import List, Union

import numpy as np
from osgeo import ogr, osr, gdal
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import linemerge, nearest_points
import sqlite3


class WidthsNotIncreasingError(ValueError):
    """Raised when one a width of a tabular cross section < than the previous width of that crosssection"""
    pass


class CrossSectionLocation:
    def __init__(self, reference_level: float, bank_level: float, widths: List[float], heights: List[float],
                 geometry: Point, parent=None):
        self.reference_level = reference_level
        self.bank_level = bank_level
        self.widths = np.array(widths)
        self.heights = np.array(heights)
        self.geometry = geometry
        self.parent = parent

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
    def __init__(self, geometry: LineString, srs: osr.SpatialReference):
        self.cross_section_locations = []
        self.geometry = geometry
        self.srs = srs
        self.parallel_offsets = []

    @classmethod
    def from_spatialite(cls, spatialite: ogr.DataSource, channel_id):
        pass

    @classmethod
    def from_geopackage(cls, geopackage: ogr.DataSource, channel_id):
        pass

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
            self.parallel_offsets.append(ParallelOffset(parent=self, offset_distance= - width / 2))
        self.parallel_offsets.reverse()
        for width in self.unique_widths:
            self.parallel_offsets.append(ParallelOffset(parent=self, offset_distance=width / 2))

    def as_xyz_points(self):
        outline = self.outline
        all_points = []
        for po in self.parallel_offsets:
            all_points += po.as_xyz_points()
        result = [point for point in all_points if outline.intersects(point)]
        return result


class ChannelGroup(Channel):
    """One or more Channels of which the geometry can be linemerged to a single linestring"""
    def __init__(self, channels: List[Channel]):
        geometries = [channel.geometry for channel in channels]
        merged_geometry = linemerge(geometries)
        if not isinstance(self.geometry, LineString):
            raise ValueError('Input channel geometries cannot be merged into a single LineString')
        super().__init__(geometry=merged_geometry, srs=channels[0].srs)  # assume all channels have same srs

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
        self.width = offset_distance
        cross_section_location_points = []
        for pos in self.parent.cross_section_location_positions:
            location_xy = self.parent.geometry.interpolate(pos, normalized=True)
            cross_section_location_points.append(nearest_points(location_xy, self.geometry)[0])
        cross_section_location_positions = [self.geometry.project(point) for point in cross_section_location_points]
        heights_at_cross_sections = [xsec.height_at(self.width) for xsec in self.parent.cross_section_locations]
        vertex_positions = [self.geometry.project(Point(vertex), normalized=True) for vertex in self.geometry.coords]
        self.heights_at_vertices = np.interp(
            vertex_positions,
            cross_section_location_positions,
            heights_at_cross_sections
        )

    def as_xyz_points(self):
        result = []
        for i, vertex in enumerate(self.geometry.coords):
            result.append(Point(vertex[0], vertex[1], self.heights_at_vertices[i]))
        return result


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