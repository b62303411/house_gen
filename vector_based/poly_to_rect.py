from shapely.geometry import Polygon

import math

from floor_plan_reader.math.vector import Vector


class PlyToRect:

    @staticmethod
    def snap_to_nearest_width(width, choices=(4.0, 8.0)):
        return min(choices, key=lambda c: abs(c - width))
    @staticmethod
    def infer_primary_direction_from_rect(poly):
        coords = list(poly.exterior.coords)[:-1]
        if len(coords) != 4:
            raise ValueError("Expected rectangle with 4 corners")

        edges = []
        for i in range(4):
            a = Vector(coords[i])
            b = Vector(coords[(i + 1) % 4])
            edge = b - a
            length = edge.calculate_length()
            edges.append((length, edge.normalize()))

        edges.sort(reverse=True, key=lambda x: x[0])
        return edges[0][1]  # Longest direction vector
    @staticmethod
    def normalize_rectangle_width(poly, choices=(4.0, 8.0)):
        coords = list(poly.exterior.coords)[:-1]
        if len(coords) != 4:
            return poly  # Not a rectangle or invalid shape

        center_x = sum(p[0] for p in coords) / 4
        center_y = sum(p[1] for p in coords) / 4
        center = Vector((center_x, center_y))

        v_dir = PlyToRect.infer_primary_direction_from_rect(poly)
        v_norm = v_dir.get_normal()

        # Get current half-length and half-width
        p1 = Vector(coords[0])
        p2 = Vector(coords[2])
        diagonal = p2 - p1

        half_length = abs(diagonal.dot_product(v_dir)) / 2
        half_width = abs(diagonal.dot_product(v_norm)) / 2

        # Snap the width to desired options
        snapped_width = PlyToRect.snap_to_nearest_width(half_width * 2, choices)
        half_width = snapped_width / 2

        # Rebuild from center
        corner1 = center + v_dir * half_length + v_norm * half_width
        corner2 = center + v_dir * half_length - v_norm * half_width
        corner3 = center - v_dir * half_length - v_norm * half_width
        corner4 = center - v_dir * half_length + v_norm * half_width

        return Polygon([
            (corner1.dx(), corner1.dy()),
            (corner2.dx(), corner2.dy()),
            (corner3.dx(), corner3.dy()),
            (corner4.dx(), corner4.dy())
        ])