import math
import random
from typing import Tuple

from shapely import box, GeometryCollection, Point, LineString, Polygon

from floor_plan_reader.id_util import IdUtil
from floor_plan_reader.math.vector import Vector
from vector_based.agents.segment import Segment
from vector_based.constants import DIRECTIONS_8
from vector_based.create_segment_candidate import Scanner
from vector_based.poly_to_rect import PlyToRect
from vector_based.ray_trace import RayTrace


class Blob:
    def __init__(self, id, world):
        self.poly = None
        self.segments = []
        self.seeds_centers = []
        self.covered = GeometryCollection()
        self.id = id
        self.world = world
        self.state = "born"
        self.active_wall = None

    import random
    from shapely.geometry import Point, Polygon

    def random_seeds(self):
        points = self.generate_random_points_in_polygon(1000)
        self.seeds_centers += points

    def generate_random_points_in_polygon(self, num_points: int) -> list[Point]:
        """
        Generate a list of random points that lie within the given polygon.

        Args:
            polygon: A Shapely Polygon
            num_points: Number of random points to generate

        Returns:
            List of Shapely Point objects inside the polygon
        """
        points = []
        minx, miny, maxx, maxy = self.poly.bounds

        attempts = 0
        max_attempts = num_points * 10  # Prevent infinite loop

        while len(points) < num_points and attempts < max_attempts:
            rand_x = random.uniform(minx, maxx)
            rand_y = random.uniform(miny, maxy)
            point = Point(rand_x, rand_y)

            if self.poly.contains(point):
                points.append(point)

            attempts += 1

        return points

    def get_rectangle_length(self, rect: Polygon, direction: Tuple[float, float]) -> float:
        coords = list(rect.exterior.coords)[:-1]
        if len(coords) != 4:
            return 0

        v_dir = Vector(direction).normalize()

        # Use the diagonal as the base vector (p1 → p3)
        diag = Vector(coords[0]) - Vector(coords[2])
        length = abs(diag.dot_product(v_dir))
        return length

    def partition_blob(self, tile_size=8.0):
        minx, miny, maxx, maxy = self.poly.bounds

        x = minx
        while x < maxx:
            y = miny
            while y < maxy:
                tile = box(x, y, x + tile_size, y + tile_size)
                clipped = tile.intersection(self.poly)
                if not clipped.is_empty and clipped.area > 1.0:
                    self.seeds_centers.append(clipped.centroid)
                y += tile_size
            x += tile_size

        return self.seeds_centers

    def test(self):
        center = Point(228, 361)
        best_seg = None
        best_lenght = 0
        rectangle = Scanner.create_segment_candidate(self.poly,center)

        self.segments.append(rectangle)
        self.covered = self.covered.union(rectangle).buffer(0)

    def ray_trace(self):
        for center in self.seeds_centers:
            if self.covered.contains(center):
                continue  # already covered

            candidates = []

            # Step 1: Try all directions first
            for direction in DIRECTIONS_8:
                seg = RayTrace.trace_ray_along_direction(self.poly, center, direction)
                if seg:
                    seg = PlyToRect.normalize_rectangle_width(seg)
                    candidates.append((seg, seg.area, direction))

            # Step 2: Sort by area (or length, or some score)
            candidates.sort(key=lambda x: x[1], reverse=True)  # largest area first

            # Step 3: Pick first non-overlapping candidate
            for seg, area, direction in candidates:
                self.segments.append(seg)
                if not seg.intersects(self.covered):
                    # self.segments.append(seg)
                    self.covered = self.covered.union(seg).buffer(0)
                    break

    @staticmethod
    def get_direction_deg(rect):
        """Get the angle of a rotated rectangle in degrees (0-180 range)."""
        coords = list(rect.exterior.coords)
        dx = coords[1][0] - coords[0][0]
        dy = coords[1][1] - coords[0][1]
        angle = math.degrees(math.atan2(dy, dx)) % 180
        return angle

    @staticmethod
    def angles_close(angle1, angle2, tolerance=1.0):
        return abs(angle1 - angle2) < tolerance or abs(abs(angle1 - angle2) - 180) < tolerance

    def filter_rect_by_overlap(self, max_overlap_ratio=0.4, angle_tolerance=1.0):
        """
        Filters overlapping rectangles:
        - If same angle and they overlap → keep only the larger one.
        - If different angles, allow overlap up to `max_overlap_ratio`.

        Returns:
            List of accepted rectangles (filtered).
        """
        accepted = []
        min_area = 4
        min_inside_ratio = 0.5
        for candidate in self.segments:
            c = PlyToRect.normalize_rectangle_width(candidate)
            cand_angle = Blob.get_direction_deg(c)
            keep_candidate = True
            to_remove = []
            # Skip too small
            if c.area < min_area:
                continue
            parent_intersection = c.intersection(self.poly)
            intersection = c.intersection(self.poly)
            inside_ratio = intersection.area / c.area if not intersection.is_empty else 0.0
            if inside_ratio < min_inside_ratio:
                # print(f"Skipped: only {inside_ratio:.2%} inside parent")
                continue

            for i, existing in enumerate(accepted):
                exist_angle = Blob.get_direction_deg(existing)
                intersection = c.intersection(existing)
                if intersection.is_empty:
                    continue

                if Blob.angles_close(cand_angle, exist_angle, angle_tolerance):
                    # Same angle, any overlap means keep the larger one
                    if c.area > existing.area:
                        to_remove.append(i)
                    else:
                        keep_candidate = False
                        break
                else:
                    # Different angle, check overlap ratio
                    overlap_cand = intersection.area / candidate.area
                    overlap_exist = intersection.area / existing.area
                    if overlap_cand > max_overlap_ratio or overlap_exist > max_overlap_ratio:
                        if c.area > existing.area:
                            to_remove.append(i)
                        else:
                            keep_candidate = False
                            break

            # Remove any smaller rectangles that conflict
            for i in reversed(to_remove):
                accepted.pop(i)

            if keep_candidate:
                accepted.append(c)

        return accepted

    def create_wall(self, x, y):
        # world, blob, start_x, start_y, id
        self.world.create_segment(self, x, y)

    def grow(self):
        for point in self.seeds_centers:
            for s in self.segments:
                if s.contains(point):
                    self.seeds_centers.remove(point)

        length = len(self.seeds_centers)
        free = self.seeds_centers.copy()
        for s in free:
            if self.is_occupied(s.x, s.y):
                self.seeds_centers.remove(s)
        if length != len(self.seeds_centers) and length > 0:
            self.status = "mush"
        elif length > 0:
            if self.active_wall is None or self.active_wall.get_state() == 'done' or self.active_wall.alive == False:
                first_element = self.pick_random_free()
                self.create_wall(first_element.x, first_element.y)
            if self.get_wall_count() > 15:
                self.print_blob()
        else:
            self.status = "done"
        return

    def run(self):
        if self.state == "born":
            self.random_seeds()
            self.state = "grow"
            return
        if self.state == "grow":
            self.grow()

    def get_wall_count(self):
        return len(self.segments)

    def pick_random_free(self):
        selected = random.choice(list(self.seeds_centers))
        return selected

    def print_blob(self):
        pass

    def is_occupied(self, x, y):
        for seg in self.segments:
            if seg.intersects(Point(x, y)):
                return True
        return False

    def free(self, o):
        pass

    def get_walls(self):
        return self.segments
