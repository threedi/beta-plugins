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


def highest_valid_index_for_single_offset(line: LineString, offset: float) -> int:
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
        minimum_idx = min(minimum_idx, highest_valid_index_for_single_offset(line, offset))
    return minimum_idx


def test_highest_valid_index_for_single_offset():
    line = LineString([[0, 0], [0, 1], [0, 2], [0, 3], [2, 3], [2, 2], [1, 1], [1, 0]])
    assert highest_valid_index_for_single_offset(line, -2) == 5

    line = LineString([[0, 0], [0, 1], [0, 2], [0, 3], [2, 3], [4, 3], [8, 3], [10, 3]])
    assert highest_valid_index_for_single_offset(line, -2) == 7


# print(LineString([(Point(vertex)) for vertex in channel_geom.coords[7:]]))
def test_highest_valid_index():
    offsets = [0.5, 1, 2.0, 5.0, -1, -2]
    # large bend at the start, smaller bend further on
    line = LineString([[0, 0], [100, 0], [100, 2], [0, 1], [0, 3], [100, 2.5], [100, 10], [0, 10]])
    hvi = highest_valid_index(line, offsets)

    print(LineString([(Point(vertex)) for vertex in channel_geom.coords[:hvi + 1]]))

    channel_geom = LineString([[0, 0], [0, 1], [0, 2], [0, 3], [2, 3], [4, 3], [8, 3], [10, 3]])
    print(highest_valid_index_for_single_offset(channel_geom, -2))


if __name__ == "__main__":
    # test_highest_valid_index_for_single_offset()
    # EMPTY OFFSETS
    print(LineString([[-4, 4], [-4, 0], [0, 0], [0, 4]]).offset_curve(2))
    print(LineString([[0, 0], [0, 1], [0, 2], [0, 3], [1, 1], [1, 0]]).offset_curve(-.5).wkt)

    # INVALID OFFSET (MULTILINESTRING)
    line_coords_1 = np.array([[0, 0], [1, 1], [1, 2], [0, 3], [0, 4], [1, 5], [2, 5], [3, 4], [3, 3], [2, 2], [2, 1], [3, 0]])
    line_coords_2 = line_coords_1 * 10 + np.array([10, 0])
    line_coords = np.vstack([line_coords_1, line_coords_2])
    line = LineString(line_coords)
    offset_line_0_5 = line.offset_curve(-0.5)
    offset_line_5 = line.offset_curve(-5)
    plt.plot(line.xy[0], line.xy[1], 'b-')  # 'b-' for blue line
    for offset_line_geom in offset_line_0_5.geoms:
        plt.plot(offset_line_geom.xy[0], offset_line_geom.xy[1], 'g-')
    for offset_line_geom in offset_line_5.geoms:
        plt.plot(offset_line_geom.xy[0], offset_line_geom.xy[1], 'r-')
    plt.xlabel('X-axis')
    plt.ylabel('Y-axis')
    plt.axis('equal')  # Set equal scaling
    plt.show()
    print(
        is_valid_offset(
            line,
            -0.5
        )
    )
    print(len(LineString([[0, 0], [1, 1], [1, 2]]).buffer(0.5).interiors))
    wkt_geometry = "LINESTRING(182345.550177 320245.500171, 182332.750177 320251.250171, 182301.650177 320277.250171, 182283.050177 320294.600171, 182262.600177 320313.200171, 182249.000177 320333.050172, 182226.950176 320360.000172, 182213.350176 320377.050172, 182196.300176 320385.100172, 182182.050176 320393.200172, 182175.850176 320403.100172, 182175.850176 320412.400172, 182182.650176 320420.450172, 182206.200176 320447.100172, 182234.700176 320467.600172, 182245.250177 320481.250172, 182248.350177 320491.150172, 182240.300177 320501.050172, 182232.250176 320503.550172, 182213.050176 320496.100172, 182195.050176 320486.800172, 182182.650176 320478.150172, 182175.850176 320478.750172, 182152.900176 320487.450172, 182136.800176 320500.450172, 182128.750176 320509.750172, 182128.100176 320519.050172, 182136.200176 320526.500172, 182144.250176 320531.450172, 182156.000176 320534.550172, 182164.700176 320545.100172, 182163.450176 320553.750172, 182155.400176 320566.800172, 182141.750176 320582.900172, 182134.200176 320590.200172, 182121.900176 320602.150172, 182111.400176 320612.700172, 182097.150176 320616.100172, 182081.650176 320618.250172, 182068.950176 320617.650172, 182054.700176 320611.750172, 182043.200176 320608.650172, 182033.600176 320609.250172, 182024.600176 320614.850172, 182012.550176 320628.200172, 182006.350176 320642.150172, 182002.600176 320661.050172, 181997.350176 320670.050172, 181990.200176 320668.800172, 181981.850176 320662.300172, 181974.400176 320651.100172, 181965.750176 320646.450172, 181959.850176 320646.450172, 181952.400176 320647.700172, 181944.350176 320653.900172, 181936.600176 320661.350172, 181921.100176 320664.450172, 181894.450176 320669.100172, 181876.500176 320670.950172, 181863.150176 320668.500172, 181852.350176 320661.650172, 181848.350176 320648.000172, 181853.900176 320632.200172, 181865.400176 320614.250172, 181868.800176 320601.850172, 181862.000176 320598.100172, 181848.950176 320604.300172, 181838.100176 320618.550172, 181826.650176 320632.850172, 181825.400176 320671.900172, 181830.050176 320680.050172, 181836.150176 320690.700172)"
    wkb_geometry = b'\x01\x02\x00\x00\x00@\x00\x00\x00\xbb\xfe\xc2fLB\x06A4\xf1,\x00\xd6\x8b\x13A\x92\x96\\\x00\xe6A\x06A\x96\xf1,\x00\xed\x8b\x13A\x8a\xc5\x8f3\xed@\x06Ay\xf2,\x00U\x8c\x13A\xceY)\xcd\xb4?\x06A\xce\xc1\xf9\xcc\xe4\x8c\x13A \x8b\\\x00H?\x06A\xee(`34\x8d\x13A\tS)\xcd*>\x06A\xfa*`3\xe4\x8d\x13AR\xea\xc2f\xa2=\x06A\xa0^\x93f\x04\x8e\x13A_\xe8\xc2f0=\x06A|\xc5\xf9\xcc$\x8e\x13A\xeaM)\xcd\xfe<\x06A\xb8_\x93fL\x8e\x13A\xe8M)\xcd\xfe<\x06A/\x93\xc6\x99q\x8e\x13A\xc6\x1e\xf6\x99\xf1=\x06A\xaea\x93f\xfc\x8e\x13A\x93"\xf6\x99\xd5>\x06A/c\x93fN\x8f\x13Ab\x8a\\\x00*?\x06Ai\xfd,\x00\x85\x8f\x13A\x92W)\xcdB?\x06A8\x97\xc6\x99\xac\x8f\x13A\x10\xf0\xc2f\x02?\x06A\xa41`3\xd4\x8f\x13A\x95\x88\\\x00\xc2>\x06A\xb71`3\xde\x8f\x13Ae\xec\xc2f(>\x06A\xb1d\x93f\xc0\x8f\x13A\xfb\xe9\xc2f\x98=\x06A\xde0`3\x9b\x8f\x13A!\xb5\x8f35=\x06A\xf7\x96\xc6\x99x\x8f\x13A\xccM)\xcd\xfe<\x06As\xfd,\x00{\x8f\x13A\x12\xb1\x8f3G<\x06Ar\xca\xf9\xcc\x9d\x8f\x13A\x13\xe2\xc2f\xc6;\x06A\x0c\xcb\xf9\xcc\xd1\x8f\x13A\x97z\\\x00\x86;\x06A\xa8\xfe,\x00\xf7\x8f\x13AIG)\xcd\x80;\x06Ax2`3\x1c\x90\x13A+\x15\xf6\x99\xc1;\x06A\\\xff,\x00:\x90\x13A\x9e|\\\x00\x02<\x06A\xaa\xcc\xf9\xccM\x90\x13A9~\\\x00`<\x06A63`3Z\x90\x13A\xfb\x18\xf6\x99\xa5<\x06A\xe7f\x93f\x84\x90\x13A\xd2\x18\xf6\x99\x9b<\x06A\x03\x01-\x00\xa7\x90\x13AK\xb1\x8f3[<\x06A\x944`3\xdb\x90\x13A:|\\\x00\xee;\x06A:\x9c\xc6\x99\x1b\x91\x13AG\xab\x8f3\xfb:\x06A\x98\xd0\xf9\xcc\x92\x91\x13AV\xa9\x8f3\x89:\x06A\xd8j\x93f\xa0\x91\x13AA\xa7\x8f3\r:\x06AX\x04-\x00\xa9\x91\x13A\xeb\x0b\xf6\x99\xa79\x06A.\x9e\xc6\x99\xa6\x91\x13A\xfd\t\xf6\x9959\x06A\x16\x04-\x00\x8f\x91\x13As\x08\xf6\x99\xd98\x06Ax\x9d\xc6\x99\x82\x91\x13AY:)\xcd\x8c8\x06A\x10\x04-\x00\x85\x91\x13A 9)\xcdD8\x06A\x9aj\x93f\x9b\x91\x13A\x18\xd1\xc2f\xe47\x06A\x9b\xd1\xf9\xcc\xd0\x91\x13A\x9c6)\xcd\xb27\x06AV\x9f\xc6\x99\x08\x92\x13A\x136)\xcd\x947\x06A\xe09`3T\x92\x13AZ5)\xcdj7\x06A9:`3x\x92\x13A2\x01\xf6\x9917\x06A6:`3s\x92\x13AD3)\xcd\xee6\x06A\xfc9`3Y\x92\x13A\xb0\x98\x8f3\xb36\x06AWl\x93f,\x92\x13ATd\\\x00n6\x06A\xaf\xd2\xf9\xcc\x19\x92\x13AS0)\xcd>6\x06A\xae\xd2\xf9\xcc\x19\x92\x13A\xb3\x95\x8f3\x036\x06Ar\xd2\xf9\xcc\x1e\x92\x13A9.)\xcd\xc25\x06A\x96\x9f\xc6\x997\x92\x13A--)\xcd\x845\x06A\xe6l\x93fU\x92\x13A>\xf4\xf5\x9934\x06Agm\x93ft\x92\x13A5X\\\x00\xa43\x06A\xdb\xd3\xf9\xcc{\x92\x13A\xa6\x89\x8f393\x06AT\x07-\x00r\x92\x13A\xc7!)\xcd\xe22\x06A$\xa0\xc6\x99V\x92\x13AA!)\xcd\xc22\x06A\xaa\x05-\x00 \x92\x13Aj\x88\x8f3\xef2\x06A\xf6\xd1\xf9\xcc\xe0\x91\x13A\x05\x8a\x8f3K3\x06A\x0c\x04-\x00\x99\x91\x13A\xb0\xbd\xc2ff3\x06A\x05j\x93fg\x91\x13AbV\\\x0003\x06A\x9ci\x93fX\x91\x13A8\xee\xf5\x99\xc72\x06Ay6`3q\x91\x13A\xc6\x84\x8f3\x152\x06A\x82k\x93f\xe3\x91\x13A\x81\x84\x8f3\x0b2\x06A\xd5\xa0\xc6\x99\x7f\x92\x13A\xf2\x85\x8f3a2\x06A\xce\xd4\xf9\xcc\xca\x92\x13A'
    line = wkb.loads(wkb_geometry)
    offset = -11.335999999999999
    print(type(line.offset_curve(offset)))
    from shapely import geos_version
    print(geos_version)
