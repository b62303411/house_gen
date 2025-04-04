from math import sqrt

from floor_plan_reader.math.vector import Vector


class Constants:
    SQRT2_OVER_2 = sqrt(2) / 2
    raw_directions = {
        0: (1, 0),
        45: (1, 1),
        90: (0, 1),
        135: (-1, 1),
        180: (-1, 0),
        225: (-1, -1),
        270: (0, -1),
        315: (1, -1),
    }

    DIRECTIONS_8 = {angle: Vector(v).normalize() for angle, v in raw_directions.items()}
