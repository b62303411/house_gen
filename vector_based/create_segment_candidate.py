import math

from shapely import LineString, Point, Polygon

from floor_plan_reader.math.vector import Vector
from vector_based.constants import DIRECTIONS_8
from vector_based.ray_trace import RayTrace


class Scanner:

    @staticmethod
    def create_segment_candidate(poly,center):
        ray_data = {}
        for direction in DIRECTIONS_8:
            seg = RayTrace.trace_ray_along_direction(poly, center, direction)
            ray_data[direction] = seg

        # Find direction with highest step count
        best_dir = max(ray_data.keys(), key=lambda d: ray_data[d][0])
        steps_stem, points_stem = ray_data[best_dir]
        stem_dir = Vector(best_dir)
        stem_norm = stem_dir.get_normal()
        steps_width, points_width = ray_data[stem_norm.direction]
        stem_start = points_stem[0]
        stem_end = points_stem[1]
        width_right = points_width[0]
        width_left = points_width[1]
        # Original stem (from ray intersections)
        stem_line = LineString([stem_start, stem_end])

        # Width line (from normal ray intersections)
        width_line = LineString([points_width[0], points_width[1]])

        # Extend lines infinitely (for accurate intersection)
        def extend_line(line, scale=1000):
            coords = list(line.coords)
            dx = coords[1][0] - coords[0][0]
            dy = coords[1][1] - coords[0][1]
            extended = LineString([
                (coords[0][0] - dx * scale, coords[0][1] - dy * scale),
                (coords[1][0] + dx * scale, coords[1][1] + dy * scale)
            ])
            return extended

        extended_stem = extend_line(stem_line)
        extended_width = extend_line(width_line)

        intersection = extended_stem.intersection(extended_width)

        if intersection.is_empty:
            raise ValueError("Stem and width lines are parallel!")

        center_point = intersection

        # Current stem midpoint (misaligned)
        current_mid = LineString([stem_start, stem_end]).centroid

        # Vector from current_mid to center_point (needs translation)
        translate_x = center_point.x - current_mid.x
        translate_y = center_point.y - current_mid.y

        # Normalize width direction for translation
        width_dx = width_right.x - width_left.x
        width_dy = width_right.y - width_left.y
        width_length = math.sqrt(width_dx ** 2 + width_dy ** 2)
        width_dx /= width_length
        width_dy /= width_length

        # Project translation onto width direction
        translation_distance = translate_x * width_dx + translate_y * width_dy

        # Current stem midpoint (misaligned)
        current_mid = LineString([stem_start, stem_end]).centroid

        # Vector from current_mid to center_point (needs translation)
        translate_x = center_point.x - current_mid.x
        translate_y = center_point.y - current_mid.y

        # Normalize width direction for translation
        width_dx = width_right.x - width_left.x
        width_dy = width_right.y - width_left.y
        width_length = math.sqrt(width_dx ** 2 + width_dy ** 2)
        width_dx /= width_length
        width_dy /= width_length

        # Project translation onto width direction
        translation_distance = translate_x * width_dx + translate_y * width_dy
        aligned_stem_start = Point(
            stem_start.x + width_dx * translation_distance,
            stem_start.y + width_dy * translation_distance
        )
        aligned_stem_end = Point(
            stem_end.x + width_dx * translation_distance,
            stem_end.y + width_dy * translation_distance
        )

        center_line = LineString([aligned_stem_start, aligned_stem_end])
        center_point = center_line.centroid
        # Half-lengths
        half_stem = aligned_stem_start.distance(aligned_stem_end) / 2
        half_width = 2
        vdir = Vector(best_dir)
        width_dx = stem_norm.dx()
        width_dy = stem_norm.dy()
        stem_dx = vdir.dx()
        stem_dy = vdir.dy()

        # Corners (relative to center_point)
        corner1 = (
            center_point.x - stem_dx * half_stem - width_dx * half_width,
            center_point.y - stem_dy * half_stem - width_dy * half_width
        )
        corner2 = (
            center_point.x + stem_dx * half_stem - width_dx * half_width,
            center_point.y + stem_dy * half_stem - width_dy * half_width
        )
        corner3 = (
            center_point.x + stem_dx * half_stem + width_dx * half_width,
            center_point.y + stem_dy * half_stem + width_dy * half_width
        )
        corner4 = (
            center_point.x - stem_dx * half_stem + width_dx * half_width,
            center_point.y - stem_dy * half_stem + width_dy * half_width
        )
        rectangle = Polygon([corner1, corner2, corner3, corner4])

        return rectangle