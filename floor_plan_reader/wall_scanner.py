import logging
import math

from floor_plan_reader.scan_result import ScanResult
from floor_plan_reader.sonde import Sonde
from floor_plan_reader.sonde_data import SondeData
from floor_plan_reader.math.vector import Vector



class WallScanner:
    def __init__(self, world):
        self.world = world

    def is_food(self, x, y):
        return self.world.is_food(int(x), int(y))

    def is_3_wide_food(self, cx, cy, direction):
        normal = direction.get_normal()
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
        if steps >= 3:
            return True

        return False

    def is_within_bounds(self, x, y):
        return self.world.is_within_bounds(x, y)

    def ping(self, x, y, d, mush):
        is_within_bounds = self.is_within_bounds(x, y)
        if not is_within_bounds:
            return False
        is_food = self.is_cell_valid(x, y, d, mush)

        is_wide_enough = self.is_3_wide_food(x, y, d)
        return is_food and is_wide_enough

    def is_cell_valid(self, x, y, d=None, mush=None):
        food = self.is_food(x, y)
        value = self.world.get_occupied_id(x, y)
        has_wall = self.world.is_wall_occupied(x, y)
        free = value == 0 or value == mush.id
        occupied = not free
        value = food and not occupied and not has_wall
        return value

        # 2) Walk backward to find the first boundary
        #    We'll use a small helper function that returns
        #    the last valid coordinate plus how many steps it walked.

    def is_ok(self, x, y, d=None, mush=None):
        return self.is_food(x, y)

    def walk_until_invalid(self, mush, x, y, d, ping):
        dx, dy = d.dx(), d.dy()
        steps_walked = 0
        last_valid_x = x
        last_valid_y = y
        while ping(x, y, d, mush):
            last_valid_x = x
            last_valid_y = y
            steps_walked += 1
            x += dx
            y += dy
        return last_valid_x, last_valid_y, steps_walked

    def measure_extent(self, mush, x, y, d):
        """Measure extent along a given direction vector (dx, dy) properly.
       - First, crawl backward to find the start.
       - Then, count forward to find the total steps.
        """
        dx, dy = d.dx(), d.dy()
        height, width = self.world.grid.shape
        min_x = None
        min_y = None
        max_x = None
        max_y = None
        # Step 1: Crawl backward until hitting a boundary
        if self.is_cell_valid(x, y, d, mush):
            min_x = x
            min_y = y
        else:
            pass
        d_reverse = d.copy()
        d_reverse.scale(-1)
        back_x, back_y, _ = self.walk_until_invalid(mush, x, y, d_reverse, self.ping)

        # 3) Walk forward from that backward boundary
        #    to find the forward boundary
        forward_x, forward_y, forward_steps = self.walk_until_invalid(mush, back_x, back_y, d, self.ping)

        if min_x is None:
            logging.info(f"{x} {y}  {width} {height}")
        # Step 2: Move one step forward to set the actual starting point

        data = SondeData(forward_steps, back_x, back_y, forward_x, forward_y)
        return data  # The total step count along this direction

    def scan_for_walls(self, mush, x, y, directions=list(
        map(lambda direction: Vector(direction), [(1, 0), (0, 1), (0.5, 0.5), (0.5, -0.5)]))):
        results = ScanResult()
        for d in directions:
            data = self.measure_extent(mush, x, y, d)
            s = Sonde(d, data)

            results.add_sonde(d, s)
        results.calculate_result()

        return results

    def detect_bleed_along_collision_box(self, mush, cb, bleed_threshold=4):
        """
        Given a CollisionBox (cb), analyze each step along its stem to detect 1-pixel-thick bleeding in either
        normal direction. If the bleed persists without exceeding 1 pixel of thickness for at least `bleed_threshold`
        points, adjust the box width and center accordingly. If any bleed exceeds 1 pixel in width at any point,
        it's marked for potential wall division.

        Args:
            cb: CollisionBox instance
            walk_until_invalid: function(x, y, direction) -> (last_x, last_y, steps)
            bleed_threshold: Minimum number of consecutive bleed points to trigger boundary expansion

        Returns:
            new_cb: CollisionBox - updated with shifted center and expanded width if needed
            division_points: List of (x, y) tuples where wall division is suggested
        """
        direction, normal = cb.derive_direction_and_normal()
        dx, dy = direction.direction
        ndx, ndy = normal.direction
        cx, cy = cb.get_center()
        half_len = cb.length / 2.0

        resolution = int(cb.length)
        left_bleed = 0
        right_bleed = 0
        division_points = []
        half_width = cb.width / 2.0

        for i in range(-resolution // 2, resolution // 2 + 1):
            x = int(cx + i * dx + .5)
            y = int(cy + i * dy + .5)

            normal_vector = Vector((ndx, ndy))
            left_vector = normal_vector.opposite()

            # Walk until invalid in both normal directions
            _, _, left_depth = self.walk_until_invalid(mush, x, y, left_vector, self.is_cell_valid)
            _, _, right_depth = self.walk_until_invalid(mush, x, y, normal_vector, self.is_cell_valid)
            _, _, right_depth = self.walk_until_invalid(mush, x, y, normal_vector, self.is_ok)
            left_diff = int(abs(left_depth - half_width))
            right_diff = int(abs(right_depth - half_width))
            # Check if the bleed goes beyond the current half-width
            if left_diff > 1 or right_diff > 1:
                division_points.append((x, y))
            else:
                if math.isclose(left_diff, 1.0, abs_tol=0.5):
                    left_bleed += 1
                if math.isclose(right_diff, 1.0, abs_tol=0.5):
                    right_bleed += 1

        # Adjust width and center if persistent 1-pixel bleed exists
        shift_x = 0
        shift_y = 0
        width_adjustment = 0

        if left_bleed >= bleed_threshold:
            shift_x -= ndx * 0.5
            shift_y -= ndy * 0.5
            width_adjustment += 1
        if right_bleed >= bleed_threshold:
            shift_x += ndx * 0.5
            shift_y += ndy * 0.5
            width_adjustment += 1

        if width_adjustment > 0:
            new_center_x = cb.center_x + shift_x
            new_center_y = cb.center_y + shift_y
            new_width = cb.width + width_adjustment
            from copy import deepcopy
            new_cb = deepcopy(cb)
            new_cb.set_position(new_center_x, new_center_y)
            new_cb.set_width(new_width)
            return new_cb, division_points

        return cb, division_points
