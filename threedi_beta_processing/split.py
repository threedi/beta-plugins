import numpy as np
from typing import List, Sequence, Union
from shapely.geometry import LineString, Point
from shapely import wkt, wkb
from shapely import geos_version
import matplotlib.pyplot as plt


assert geos_version[0] > 3 or (geos_version[0] == 3 and geos_version[1] >= 12)


class EmptyOffsetError(ValueError):
    """Raised when the parallel offset at given offset distance results in an empty geometry"""
    pass


class InvalidOffsetError(ValueError):
    """Raised when the parallel offset at given offset distance results in a geometry that is not a LineString"""


def is_valid_offset(line, offset):
    po = line.offset_curve(offset)
    if po.is_empty:
        return False
    if type(po) != LineString:
        return False
    return True


def highest_valid_index_single_offset(line: LineString, offset: float) -> int:
    """
    Returns index of the vertex at which to split ``line`` in a (first) part for which a valid offset_curve can be made
    at given ``offset`` and a (second) part, i.e. the rest of ``line``
    """
    vertex_positions = [line.project(Point(vertex)) for vertex in line.coords]
    highest_valid_idx = 1
    lowest_invalid_idx = len(vertex_positions) - 1
    current_idx = len(vertex_positions) - 1
    while lowest_invalid_idx - highest_valid_idx > 1:
        test_line = LineString([(Point(vertex)) for vertex in line.coords[:current_idx + 1]])
        if is_valid_offset(test_line, offset):
            highest_valid_idx = current_idx
        else:
            lowest_invalid_idx = current_idx
        current_idx = int(highest_valid_idx + (lowest_invalid_idx-highest_valid_idx)/2)
    return highest_valid_idx
    # valid_part = LineString([(Point(vertex)) for vertex in line.coords[:highest_valid_idx + 1]])
    # if highest_valid_idx == len(vertex_positions) - 1:
    #     rest = None
    # else:
    #     rest = LineString([(Point(vertex)) for vertex in line.coords[highest_valid_idx:]])
    # return valid_part, rest


def highest_valid_index(line: LineString, offsets: List[float]) -> int:
    offsets.sort(key=lambda x: -1 * abs(x))  # largest offsets first, because will probably result in the lowest index
    minimum_idx = len(line.coords) - 1
    for offset in offsets:
        line = LineString([(Point(vertex)) for vertex in line.coords[:minimum_idx + 1]])
        minimum_idx = min(minimum_idx, highest_valid_index_single_offset(line, offset))
    return minimum_idx


def test_is_valid_offset():
    # VALID
    assert is_valid_offset(LineString([[0, 0], [0, 1], [0, 2], [0, 3], [1, 1]]), -.5) is True

    # EMPTY OFFSETS
    assert is_valid_offset(LineString([[-4, 4], [-4, 0], [0, 0], [0, 4]]), 2) is False
    assert is_valid_offset(LineString([[0, 0], [0, 1], [0, 2], [0, 3], [1, 1], [1, 0]]), -.5) is False

    # MULTILINESTRING
    line_coords = np.array(
        [[0, 0], [10, 10], [10, 20], [0, 30], [0, 40], [10, 50], [20, 50], [30, 40], [30, 30], [20, 20], [20, 10],
         [30, 0], [37, 0], [38, 1], [38, 2], [37, 3], [37, 4], [38, 5], [39, 5], [40, 4], [40, 3], [39, 2], [39, 1],
         [40, 0]]
    )
    line = LineString(line_coords)
    assert is_valid_offset(line, -0.5) is False
    assert is_valid_offset(line, -0.4) is True


def test_highest_valid_index_single_offset(plot: bool = False):
    line = LineString([[0, 0], [0, 1], [0, 2], [0, 3], [2, 3], [2, 2], [1, 1], [1, 0]])
    offset = -2
    print(highest_valid_index_single_offset(line, -2))
    if plot:
        offset_line = line.offset_curve(offset)
        plt.plot(line.xy[0], line.xy[1], 'b-')  # 'b-' for blue line
        if type(offset_line) == LineString:
            plt.plot(offset_line.xy[0], offset_line.xy[1], 'g-')
        else:  # Probably MultiLineString
            for offset_line_geom in offset_line.geoms:
                plt.plot(offset_line_geom.xy[0], offset_line_geom.xy[1], 'g-')
        hvi = highest_valid_index_single_offset(line, offset)
        point_x, point_y = line.coords[hvi]
        plt.plot(point_x, point_y, 'ro', label=f"HVI: {hvi}")
        plt.xlabel('X-axis')
        plt.ylabel('Y-axis')
        plt.axis('equal')  # Set equal scaling
        plt.legend()
        plt.show()


    assert highest_valid_index_single_offset(line, -2) == 4

    line = LineString([[0, 0], [0, 1], [0, 2], [0, 3], [2, 3], [4, 3], [8, 3], [10, 3]])
    assert highest_valid_index_single_offset(line, -2) == 7


# print(LineString([(Point(vertex)) for vertex in channel_geom.coords[7:]]))
def test_highest_valid_index(plot: bool = False):
    line_coords = np.array(
        [[0, 0], [10, 10], [10, 20], [0, 30], [0, 40], [10, 50], [20, 50], [30, 40], [30, 30], [20, 20], [20, 10],
         [30, 0], [37, 0], [38, 1], [38, 2], [37, 3], [37, 4], [38, 5], [39, 5], [40, 4], [40, 3], [39, 2], [39, 1],
         [40, 0]]
    )
    line = LineString(line_coords)
    offset_small = -0.5
    offset_large = -5

    if plot:
        offset_line_0_5 = line.offset_curve(offset_small)
        offset_line_5 = line.offset_curve(offset_large)
        plt.plot(line.xy[0], line.xy[1], 'b-')  # 'b-' for blue line
        for offset_line_geom in offset_line_0_5.geoms:
            plt.plot(offset_line_geom.xy[0], offset_line_geom.xy[1], 'g-')
        for offset_line_geom in offset_line_5.geoms:
            plt.plot(offset_line_geom.xy[0], offset_line_geom.xy[1], 'r-')
        hvi_small_offset = highest_valid_index(line, [offset_small])
        point_x, point_y = line.coords[hvi_small_offset]
        plt.plot(point_x, point_y, 'ro', label=f"HVI for small offset: {hvi_small_offset}")
        hvi_large_offset = highest_valid_index(line, [offset_large])
        point_x, point_y = line.coords[hvi_large_offset]
        plt.plot(point_x, point_y, 'ko', label=f"HVI for large offset: {hvi_large_offset}")
        plt.xlabel('X-axis')
        plt.ylabel('Y-axis')
        plt.axis('equal')  # Set equal scaling
        plt.legend()
        plt.show()

    assert highest_valid_index(line, [offset_small, offset_large]) == 8
    assert highest_valid_index(line, [offset_small, offset_large]) == highest_valid_index(line, [offset_large])

    assert highest_valid_index(line, [offset_small]) == 20


if __name__ == "__main__":
    test_highest_valid_index_single_offset(True)
    test_highest_valid_index()
    test_is_valid_offset()