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


    # Reverse mapping: normalized vector (as tuple) -> angle
    VECTOR_TO_ANGLE = {
        (round(v.dx(), 6), round(v.dy(), 6)): angle
        for angle, v in DIRECTIONS_8.items()
    }

    @staticmethod
    def get_key(vector):
        return (round(vector.dx(), 6), round(vector.dy(), 6))
    @staticmethod
    def angle_to_vector(angle):
        """Convert angle (0, 45, ..., 315) to normalized Vector."""
        return Constants.DIRECTIONS_8[angle]

    @staticmethod
    def vector_to_angle(vector):
        """Convert normalized Vector to closest matching angle."""
        key = Constants.get_key(vector)
        return Constants.VECTOR_TO_ANGLE.get(key, None)