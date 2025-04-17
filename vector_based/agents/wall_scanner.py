import logging
import math
from copy import deepcopy

from shapely import LineString, Point

from floor_plan_reader.math.Constants import Constants


from vector_based.agents.DataPoint import DataPoint
from vector_based.agents.scan_result import ScanResult


class Key:
    def __init__(self, d, x, y):
        self.direction = d
        self.x = x
        self.y = y

    def __hash__(self):
        """Hash the vector based on its direction."""
        return hash((self.direction, self.x, self.y))

    def __eq__(self, other):
        """Compare two vectors for equality based on their direction."""
        if isinstance(other, Key):
            return self.direction == other.direction and self.x == other.x and self.y == other.y

        return False


class SondeExtra:
    def __init__(self):
        self.results = {}

    def add_result(self, key, result):
        self.results[key] = result


class WallScanner:
    def __init__(self, world):
        self.world = world

    def is_food(self, x, y):
        return self.world.is_food(int(x), int(y))

    def is_3_wide_food(self, k, threshold=0, strategy=None):
        cx = k.x
        cy = k.y
        normal = k.direction.get_normal()
        nx, ny = normal.direction
        x, y = cx, cy
        while self.is_food(x, y):
            x -= nx
            y -= ny
        x += nx
        y += ny
        steps = 0
        while self.is_food(x, y):
            x += nx
            y += ny
            steps += 1
        if strategy is not None:
            strategy.add_result(k, steps)
        if steps > 2:
            return True

        return False

    def is_within_bounds(self, x, y):
        return self.world.is_within_bounds(x, y)

    def is_food_and_free(self, x, y, mush):
        food = self.is_food(x, y)
        if not food:
            return False

        mush_id = self.world.get_occupied_id(x, y)
        if mush_id == 0:
            return True

        if mush_id == mush.id:
            return True

        return False

    def ping(self, k, mush, threshold=3, strategy=None):
        x = k.x
        y = k.y
        d = k.direction
        is_within_bounds = self.is_within_bounds(x, y)
        if not is_within_bounds:
            return False
        is_food = self.is_cell_valid(k, mush)

        is_wide_enough = self.is_3_wide_food(k, threshold, strategy)
        return is_food and is_wide_enough

    def is_cell_valid(self, k, mush=None, treshold=3, strategy=None):
        return self.is_food_and_free(k.x, k.y, mush)

    def is_cell_valid_(self, k, mush=None, treshold=3, strategy=None):
        x = k.x
        y = k.y
        food = self.is_food(x, y)
        value = self.world.get_occupied_id(x, y)
        has_wall = self.world.is_wall_occupied(x, y)

        wall_free = True
        if mush is not None:
            if has_wall:
                wall_id = self.world.get_occupied_wall_id(x, y)
                if mush.wall_segment is not None:
                    wall_free = mush.wall_segment.id == wall_id
                    if not wall_free:
                        logging.debug("other wall ?")
        elif has_wall:
            wall_free = False

        free = (value == 0 or value == mush.id) and wall_free
        occupied = not free
        value = food and not occupied
        return value

        # 2) Walk backward to find the first boundary
        #    We'll use a small helper function that returns
        #    the last valid coordinate plus how many steps it walked.

    def is_ok(self, x, y, d=None, mush=None):
        return self.is_food(x, y)

    def walk_until_invalid(self, mush, k, ping, strategy=None):
        d = k.direction
        x = k.x
        y = k.y
        dx, dy = d.dx(), d.dy()
        steps_walked = 0
        last_valid_x = x
        last_valid_y = y
        while ping(Key(d, x, y), mush, 3, strategy):
            last_valid_x = x
            last_valid_y = y
            steps_walked += 1
            x += dx
            y += dy
        return last_valid_x, last_valid_y, steps_walked

    def measure_extent(self, mush, k):
        max_distance = 300
        """Measure extent along a given direction vector (dx, dy) properly.
       - First, crawl backward to find the start.
       - Then, count forward to find the total steps.
        """
        d = k.direction
        x = k.x
        y = k.y

        d_reverse = d.copy()
        d_r = d_reverse.opposite()

        end = Point(x + d.dx() * max_distance, y + d.dy() * max_distance)
        origin = Point(x + d_r.dx() * max_distance, y + d_r.dy() * max_distance)

        ray = LineString([origin, end])
        intersection = ray.intersection(mush.blob.poly.exterior)
        #intersection.coords
        steps = 0
        if intersection.geom_type == 'Point':
            return intersection

        elif intersection.geom_type in ['MultiPoint', 'LineString', 'MultiLineString']:
            # For MultiPoint: return closest one
            points = []
            if intersection.geom_type == 'MultiPoint':
                points = list(intersection.geoms)
                steps = points[0].distance(points[1])
            elif intersection.geom_type == 'LineString':
                points = [Point(c) for c in intersection.coords]
                steps = points[0].distance(points[1])
            elif intersection.geom_type == 'MultiLineString':
                for line in intersection.geoms:
                    points.extend([Point(c) for c in line.coords])

            points.sort(key=lambda p: origin.distance(p))

            min_x = min(pt.x for pt in points)
            max_x = max(pt.x for pt in points)
            min_y = min(pt.y for pt in points)
            max_y = max(pt.y for pt in points)


            data = DataPoint(steps, min_x, max_x, min_y, max_y,k)


            return data  # The total step count along this direction

    def scan_for_walls(self, mush, x, y, directions=Constants.DIRECTIONS_8.values()):
        results = ScanResult()
        for d in directions:
            k = Key(d, x, y)
            data = self.measure_extent(mush, k)
            results.add_sonde(d,data)
        results.calculate_result()

        return results

    def detect_bleed_along_collision_box(self, mush, cb, bleed_threshold=4):
        direction, normal = cb.derive_direction_and_normal()
        dx, dy = direction.direction
        ndx, ndy = normal.direction

        cx, cy = cb.get_center()
        corners = cb.calculate_corners()
        # following the vector
        # Each edge of the box
        edges = {
            "left": LineString([corners[2], corners[1]]),
            "front": LineString([corners[3], corners[2]]),
            "right": LineString([corners[3], corners[0]]),
            "back": LineString([corners[1], corners[0]])
        }

        bleed_directions = {
            "left": normal.opposite(),  # normal-
            "right": normal,  # normal+
            "front": direction,  # direction+
            "back": direction.opposite()  # direction-
        }

        detected_bleed_edges = []

        for name, line in edges.items():
            bleed_vec = bleed_directions[name].normalize()
            length = line.length
            samples = int(length) + 1

            for i in range(samples):
                pt = line.interpolate(i / samples, normalized=True)
                bleed_x = pt.x + bleed_vec.dx()
                bleed_y = pt.y + bleed_vec.dy()
                k = Key(bleed_vec, int(round(bleed_x)), int(round(bleed_y)))
                if self.is_cell_valid(k, mush):
                    bleed_x = bleed_x + bleed_vec.dx()
                    bleed_y = bleed_y + bleed_vec.dy()
                    k_plus_one = Key(bleed_vec, int(round(bleed_x)), int(round(bleed_y)))
                    if not self.is_cell_valid(k_plus_one, mush):
                        detected_bleed_edges.append(name)
                        break  # One is enough to expand that side

        # Now decide how to grow the box
        shift_x = shift_y = 0
        grow_length = 0
        grow_width = 0

        if "left" in detected_bleed_edges:
            shift_x -= ndx * 0.5
            shift_y -= ndy * 0.5
            grow_width += 1
        if "right" in detected_bleed_edges:
            shift_x += ndx * 0.5
            shift_y += ndy * 0.5
            grow_width += 1
        if "front" in detected_bleed_edges:
            shift_x += dx * 0.5
            shift_y += dy * 0.5
            grow_length += 1
        if "back" in detected_bleed_edges:
            shift_x -= dx * 0.5
            shift_y -= dy * 0.5
            grow_length += 1

        if grow_length or grow_width:
            from copy import deepcopy
            new_cb = deepcopy(cb)
            new_cb.set_position(cb.center_x + shift_x, cb.center_y + shift_y)
            new_cb.set_length(cb.length + grow_length)
            new_cb.set_width(cb.width + grow_width)

            # Ensure stem is longer than width
            if new_cb.width > new_cb.length:
                new_cb.swap_direction()

            return new_cb , None

        division_points = None
        return cb, division_points
