import math
import random

import pygame

from floor_plan_reader.agent import Agent
from floor_plan_reader.cell import Cell
from floor_plan_reader.collision_box import CollisionBox
from floor_plan_reader.id_util import Id_Util
from floor_plan_reader.sonde import Sonde
from floor_plan_reader.sonde_data import SondeData
from floor_plan_reader.vector import Vector
from floor_plan_reader.wall_scanner import WallScanner
from floor_plan_reader.wall_segment import WallSegment


class Mushroom(Agent):
    def __init__(self, start_x, start_y, world, mush_id):
        super().__init__(mush_id)
        self.wall_scanner = WallScanner(world)
        self.world = world
        self.outward_points = set()
        self.root_cells = set([Cell(start_x, start_y)])
        self.core_cells = set()
        self.collision_box = CollisionBox(start_x, start_y, 1, 1, 0)  # Will be set after ray trace
        self.alive = True
        self.state = "ray_trace"
        self.growth_cells = set()
        self.max_width = 1
        self.overlapping = set()
        self.stem_points = set()
        self.crawl_points= set()
        self.collision_box_history = set()
        self.branches = []
        self.wall_segment = None
        self.left_margin = None
        self.left_inside = None
        self.right_margin = None
        self.right_inside = None
        self.selected=False
        self.co_axial_walls=set()

    def xor_bool(self, a, b):
        return bool(a) != bool(b)

    def is_outer_wall(self):
        if self.left_inside is not None and self.right_inside is not None:
            return self.xor_bool(self.left_inside, self.right_inside)
        return False

    def set_position(self, x, y):
        self.collision_box.set_position(x, y)
    def set_selected(self,selected):
        self.selected = selected

    def get_center(self):
        return self.collision_box.get_center()

    def run(self):
        self.process_state()

    def derive_direction_and_normal(self):
        return self.collision_box.derive_direction_and_normal()

    def try_to_center(self):
        lm = None
        rm = None
        if self.left_margin is not None:
            lm = self.left_margin
        if self.right_margin is not None:
            rm = self.right_margin
        if rm is None or lm is None:
            return
        self.collision_box.width = self.left_margin + self.right_margin
        direction, normal = self.derive_direction_and_normal()
        mag = math.hypot(normal[0], normal[1])
        if mag > 0:
            nx = normal[0] / mag
            ny = normal[1] / mag
        else:
            # Degenerate case (no valid normal)
            return

        right_dist = self.right_margin
        left_dist = self.left_margin
        # 2) Compute how far we are off. If right_dist is bigger, shift center outward.
        shift = (right_dist - left_dist) / 2.0

        x, y = self.get_center()
        # 3) Shift the center to balance
        x += shift * nx
        y += shift * ny

        self.set_position(x, y)

        self.measure_margin()
        if self.left_margin is not None:
            lm_d = self.left_margin
        if self.right_margin is not None:
            rm_d = self.right_margin

        dx = lm - lm_d
        dy = rm - rm_d
        print(f"dx:{dx} dy:{dy}")

    def process_state(self):
        if self.state == "ray_trace":
            self.ray_trace_phase()
            self.fill_box()
            self.state = "recenter_phase"
        if self.state == "recenter_phase":
            if self.recenter_phase():
                self.state = "recenter_phase"
            else:
                self.state = "pruning"
        elif self.state == "pruning":
            self.prunning_phase()
            self.state = "wall_type"
        elif self.state == "overlap":
            self.overlap_phase()
            self.state = "crawl"
        elif self.state == "crawl":
            self.crawl_phase()
            self.state = "wrapup"
        elif self.state == "wall_type":
            self.wall_type_phase()
            if abs(self.left_margin - self.right_margin) > 2:
                self.state = "center"
            else:
                self.state = "overlap"
        elif self.state == "center":
            self.try_to_center()
            self.state = "overlap"
        elif self.state == "wrapup":
            if self.is_valid():
                self.forced_fill_box()
                self.state = "done"
            else:
                self.kill()

    def process_state_(self):
        """State machine for floor plan resolution."""
        if self.state == "ray_trace":
            self.ray_trace_phase()
            self.fill_box()
            self.state = "stem_growth"
        elif self.state == "stem_growth":
            self.stem_growth_phase()
            self.state = "width_assessment"
        elif self.state == "width_assessment":
            self.width_assessment_phase()
            self.state = "pruning"
        elif self.state == "width_expansion":
            self.width_ray_trace()
            self.state = "pruning"
        elif self.state == "pruning":
            self.prunning_phase()
            self.state = "overlap"
        elif self.state == "overlap":
            self.overlap_phase()
            self.state = "perimeter_reaction"
        elif self.state == "perimeter_reaction":
            self.perimeter_reaction_phase()
            self.state = "growth" if self.has_growth_cells() else "done"
        elif self.state == "growth":
            self.growth_phase()
            if self.is_valid():
                self.state = "done"
            else:
                self.kill()
        # min_x, max_x, min_y, max_y = self.ray_trace()
        # self.update_bounding_box_and_center(min_x, max_x, min_y, max_y)

    def fill_box(self):
        pixels = self.collision_box.iterate_covered_pixels()
        for p in pixels:
            x = p[0]
            y = p[1]
            if self.world.is_food(x, y) and not self.world.is_occupied(x, y):
                cell = Cell(x, y)
                self.root_cells.add(cell)
                self.world.occupy(x, y, self)
                self.stem_points.add(cell)

    def forced_fill_box(self):
        pixels = self.collision_box.iterate_covered_pixels()
        for p in pixels:
            x = p[0]
            y = p[1]
            if self.world.is_food(x, y):
                cell = Cell(x, y)
                self.root_cells.add(cell)
                self.world.occupy(x, y, self)
                self.stem_points.add(cell)

    def get_occupation_ratio(self):
        if self.collision_box.get_area() == 0:
            return 0
        return len(self.root_cells) / self.collision_box.get_area()

    def is_parallel_to(self, other):
        return self.collision_box.is_parallel_to(other.collision_box)

    def is_on_same_axis_as(self, other):
        return self.collision_box.is_on_same_axis_as(other.collision_box)

    def calculate_rotation_from_direction(self, dx, dy):
        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad)
        # Normalize angle to nearest 45 degrees
        angle_deg = round(angle_deg / 45) * 45
        return angle_deg % 360

    def evaluate_segment_agregate(self,obj):
        wall = None
        if obj is not None and obj.is_on_same_axis_as(self):
            self.co_axial_walls.add(obj)

    def crawl(self, points):
        steps = 0
        opening_lenght = 0
        measuring_opening = False

        for p in points:
            x = p[0]
            y = p[1]
            steps = steps + 1
            if measuring_opening:
                if opening_lenght > 100:
                    return
                if self.world.is_food(x, y):
                    if self.world.is_occupied(x, y):
                        id = self.world.get_occupied_id(x, y)
                        # print(f"{id}")
                        obj = self.world.get_obj_by_id(id)

                        self.evaluate_segment_agregate(obj)
                    else:
                        self.create_branche(x, y)
                else:
                    opening_lenght = opening_lenght + 1

            else:
                if self.world.is_food(x, y):
                    self.outward_points.add(p)
                    if (steps <= 1):
                        normal = self.collision_box.get_normal()
                        dir = self.get_direction()
                        directions = [normal, dir]
                        self.scan_for_walls(x, y, directions)
                        #print("hum")
                else:
                    measuring_opening = True

    def crawl_phase(self):
        h, w = self.world.get_shape()
        points_forward, points_backward = self.collision_box.get_extended_ray_trace_points(h, w)
        self.crawl_points = set()
        self.crawl_points.update(points_forward)
        self.crawl_points.update(points_backward)
        self.crawl(points_forward)
        self.crawl(points_backward)
        wall = None
        if self.wall_segment is not None:
            wall = self.wall_segment
        for coaxial in self.co_axial_walls:
            if coaxial.wall_segment is not None:
                wall = coaxial.wall_segment

        if wall is None:
            wall = WallSegment(Id_Util.get_id(),self.world)
            self.wall_segment = wall
            wall.add_part(self)
            for coaxial in self.co_axial_walls:
                coaxial.wall_segment = wall
                wall.add_part(coaxial)
            self.world.candidates.append(wall)
        else:
            if self.wall_segment is None:
                self.wall_segment=wall
                wall.add_part(self)
            for coaxial in self.co_axial_walls:
                if coaxial.wall_segment is None:
                    coaxial.wall_segment = self.wall_segment
                    self.wall_segment.add_part(coaxial)

    def measure_limit(self, list):
        in_wall = True
        steps = 1
        for p in list:
            x = p[0]
            y = p[1]
            if in_wall:
                if not self.world.is_food(x, y):
                    in_wall = False
                else:
                    steps = steps + 1
            else:
                if self.world.is_within_bounds(x, y):
                    if self.world.is_food(x, y):
                        return True, steps
                else:
                    return False, steps
        return False, steps

    def measure_margin(self):
        left, right = self.collision_box.get_normal_trace_points()
        inside, step = self.measure_limit(left)
        self.left_margin = step
        self.left_inside = inside
        inside, step = self.measure_limit(right)
        self.right_margin = step
        self.right_inside = inside

    def wall_type_phase(self):
        self.measure_margin()

    def prunning_phase(self):
        if self.center_on_food():
            pass
        else:
            self.kill()

    def kill(self):
        self.alive = False
        for r in self.root_cells:
            self.world.free(r.x, r.y)

    def is_valid(self):
        valid = self.collision_box.length > 3
        valid = self.collision_box.width > 3 and valid
        valid = self.collision_box.length > self.collision_box.width and valid
        corners = self.corners()
        invalid_corners = 0
        for c in corners:
            x = c[0]
            y = c[1]
            if not self.world.is_food(x, y):
                invalid_corners += 1
        if invalid_corners > 2:
            valid = True
        return valid

    def recenter_phase(self):
        rm = self.right_margin
        x, y = self.get_center()
        if self.center_on_food():
            self.performe_ray_trace()
            x1, y1 = self.get_center()
            if x1 != x or y != y1:
                cb = self.collision_box
                if cb not in self.collision_box_history:
                    center = cb.get_center()
                    self.collision_box_history.add(cb)
                    if not self.world.is_food(center[0], center[1]):
                        pass
                    return True
                else:
                    return False
        return False

    def overlap_phase(self):
        mushrooms = self.world.find_all(Mushroom)
        for m in mushrooms:
            if m != self and m.alive and m.is_valid():
                if self.collision_box.is_parallel_to(m.collision_box):
                    if self.collision_box.is_overlapping(m.collision_box):
                        self.overlapping.add(m)
                        ratio = self.get_occupation_ratio()
                        if ratio < m.get_occupation_ratio():
                            self.kill()
                            # self.alive = False

        pass

    def prune_overlap(self):
        pass

    def corners(self):
        return self.collision_box.calculate_corners()

    def performe_ray_trace(self):
        """Determine the longest axis."""
        result = self.ray_trace_from_center()
        if result.is_valid():
            stem_length = result.get_lenght()
            width = result.get_width()
            cx, cy = result.center
            dx, dy = result.get_dir().direction
            x, y = self.get_center()
            is_on_food = False
            if self.world.is_food(x, y):
                is_on_food = True


            self.collision_box.set_lenght(stem_length)
            self.collision_box.set_width(width)
            self.set_position(cx, cy)

            angle = self.calculate_rotation_from_direction(dx, dy)
            self.collision_box.rotation = angle
            self.corners()
            direction = (1, 0) if abs(dx) > abs(dy) and dx > 0 else (-1, 0) if abs(dx) > abs(dy) else (
                0, 1) if dy > 0 else (0, -1)
            x, y = self.get_center()
            if is_on_food and not self.world.is_food(x, y):
                area = self.collision_box.get_area()
                print(f"center out {area}?")
        else:
            self.record_stack_trace()
        # print(
        #    f"Mushroom {self.id}: Ray trace - length={self.stem_length}, direction={direction}, center=({x}, {y})")

    def ray_trace_phase(self):
        self.performe_ray_trace()

    def get_center(self):
        return self.collision_box.get_center()

    def get_direction(self):
        return self.collision_box.get_direction()

    def stem_growth_phase(self):
        """Grow a stem along the longest axis."""
        x, y = self.get_center()

        for i in range(self.stem_length + 1):
            sx = int(x + self.get_direction()[0] * i)
            sy = int(y + self.get_direction()[1] * i)
            if self.world.is_food(sx, sy) and not self.world.is_occupied(sx, sy):
                cell = Cell(sx, sy)
                self.root_cells.add(cell)
                self.world.occupied[sy, sx] = self.id
                self.stem_points.append(cell)
        print(f"Mushroom {self.id}: Stem grown - {len(self.stem_points)} points")

    def width_assessment_phase(self):
        """Assess available width at each stem point."""
        self.widths = {}
        perpendicular = (-self.get_direction()[1], self.get_direction()[0])
        for point in self.stem_points:
            width = 0
            for offset in range(1, self.max_width + 1):
                wx_plus = point.x + perpendicular[0] * offset
                wy_plus = point.y + perpendicular[1] * offset
                wx_minus = point.x - perpendicular[0] * offset
                wy_minus = point.y - perpendicular[1] * offset
                if (self.can_grow(wx_plus, wy_plus) and
                        self.can_grow(wx_minus, wy_minus)):
                    width = offset
                else:
                    break
            self.widths[point] = width
        print(f"Mushroom {self.id}: Width assessed - {len(self.widths)} points")

    def width_ray_trace(self):
        points = self.collision_box.get_ray_trace_points()

        min_candidate = MinMax()
        for p in points:
            min_x, max_x, min_y, max_y = self.ray_trace(p[0], p[1])
            min_candidate.evaluate(min_x, max_x, min_y, max_y)

    def trace_food_boundary(self, x, y, dx, dy):
        """Trace in a direction while food is present, return steps taken."""
        steps = 0
        # Check the next cell before moving
        while self.world.is_within_bounds(x + dx, y + dy) and self.world.is_food(x + dx, y + dy):
            x += dx
            y += dy
            steps += 1
        return steps  # Return the number of steps, not coordinates

    def width_expansion_phase(self):
        direction = self.get_direction()
        """Expand stem to full available width."""
        perpendicular = (-direction[1], direction[0])
        for point, width in self.widths.items():
            for offset in range(-width, width + 1):
                wx = point.x + perpendicular[0] * offset
                wy = point.y + perpendicular[1] * offset
                if self.can_grow(wx, wy):
                    cell = Cell(wx, wy)
                    self.root_cells.add(cell)
                    self.world.occupied[wy, wx] = self.id
        print(f"Mushroom {self.id}: Width expanded - {len(self.root_cells)} cells")

    def perimeter_reaction_phase(self):
        """Mark perimeter and identify growth cells by walking the edge of root_cells."""
        perimeter = set()
        growth_cells = set()
        h, w = self.world.grid.shape

        for cell in self.root_cells:
            neighbors = self.world.get_neighbors_8(cell.x, cell.y)
            if any(not self.world.is_occupied(nx, ny) for nx, ny in neighbors):
                perimeter.add(cell)

            for nx, ny in neighbors:
                if (self.world.is_food(nx, ny) and
                        self.world.is_occupied(nx, ny) and
                        Cell(nx, ny) not in self.root_cells):
                    neighbor_cell = Cell(nx, ny)
                    neighbor_neighbors = self.world.get_neighbors_8(nx, ny)
                    is_perimeter = any(not self.world.is_occupied(nnx, nny) for nnx, nny in neighbor_neighbors)
                    if is_perimeter:
                        perimeter.add(neighbor_cell)
                    else:
                        growth_cells.add(neighbor_cell)

        self.perimeter = perimeter
        self.growth_cells = growth_cells
        print(f"Mushroom {self.id}: Perimeter - {len(perimeter)} cells, Growth cells - {len(growth_cells)}")

    def get_covered_ratio(self):
        if self.collision_box.get_area() == 0:
            return 0
        return len(self.stem_points) / self.collision_box.get_area()

    def growth_phase(self):
        """Spawn a new mushroom from an occupied food cell not in this stem, limit to one per cycle."""
        if not self.growth_cells:
            return
        candidate = None
        for cell in self.growth_cells:
            if self.world.is_food(cell.x, cell.y) and self.world.is_occupied(cell.x, cell.y):
                candidate = cell
                break
        if candidate:
            self.world.create_mushroom(candidate.x, candidate.y)
            self.growth_cells = set()  # Clear all growth cells after spawning one mushroom
            print(
                f"Mushroom {self.id}: Spawned new mushroom at ({candidate.x}, {candidate.y}), new agent count={len(self.world.agents)}")
        else:
            self.growth_cells.clear()

    def has_growth_cells(self):
        return bool(self.growth_cells)

    def can_grow(self, x, y):
        h, w = self.world.grid.shape
        return (0 <= x < w and 0 <= y < h and
                self.world.is_food(x, y) and
                not self.world.is_occupied(x, y) and
                not self.world.collide_with_any(self, x, y))

    def ray_trace_from_center(self):
        center_x, center_y = self.get_center()
        values = self.ray_trace(center_x, center_y)
        return values

    def ray_trace(self, x, y):
        values = self.scan_for_walls(x, y)
        return values

    def is_3_wide_food(self,cx, cy):
        nx,ny = self.collision_box.get_normal()
        # For offset in [-1, 0, 1], check (cx + offset*nx, cy + offset*ny)
        for offset in [-1, 0, 1]:
            test_x = int(cx + offset * nx)
            test_y = int(cy + offset * ny)
            # Check bounds + food
            if not self.world.is_within_bounds(test_x,test_y):
                return False
            if not self.world.is_food(test_x, test_y):
                return False
        return True
    def measure_extent(self, x, y, dx, dy):
        """Measure extent along a given direction vector (dx, dy) properly.
       - First, crawl backward to find the start.
       - Then, count forward to find the total steps.
        """
        height, width = self.world.grid.shape
        min_x = None
        min_y = None
        max_x = None
        max_y = None
        # Step 1: Crawl backward until hitting a boundary
        if self.world.is_food(int(x), int(y)):
            min_x = x
            min_y = y
        else:
            pass
        while 0 <= x < width and 0 <= y < height and self.world.is_food(int(x), int(y)) and self.is_3_wide_food(x,y):
            x -= dx
            y -= dy
            min_x = x
            min_y = y
        if min_x is None:
            print(f"{x} {y}  {width} {height}")
        # Step 2: Move one step forward to set the actual starting point
        x += dx
        y += dy
        steps = 0

        # Step 3: Count steps moving forward until hitting another boundary
        while 0 <= x < width and 0 <= y < height and self.world.is_food(int(x), int(y)):
            x += dx
            y += dy
            steps += 1  # Count steps only in the forward direction
            max_x = x
            max_y = y
        if min_x is None or min_y is None:
            pass
        data = SondeData(steps,min_x,min_y,max_x,max_y)
        return data  # The total step count along this direction

    def scan_for_walls(self, x, y, directions=list(
        map(lambda direction: Vector(direction), [(1, 0), (0, 1), (0.5, 0.5), (0.5, -0.5)]))):
        return self.wall_scanner.scan_for_walls(x,y,directions)
    def scan_for_walls2(self, x, y, directions=list(map(lambda direction: Vector(direction), [(1, 0), (0, 1), (0.5, 0.5), (-0.5, -0.5)]))):


        lengths = []
        vectors = []
        min_x = 900
        min_y = 900
        max_x = 0
        max_y = 0
        sondes = []
        sonde_dic = {}
        for d in directions:
            s = Sonde(d,None)
            sonde_dic[d] = s
            sonde_dic[d.opposite()] = s
            test = sonde_dic.get(d.opposite())
            #v = Vector()
            #v.direction = d
            #v.position = (x, y)
            #vectors.append(v)
            data = self.measure_extent(x, y, d.dx(), d.dy())
            s.data = data
            sondes.append(s)
            if data.min_x is None or data.max_x is None:
                pass
            else:
                min_x = min(data.min_x + 1, min_x)
                min_y = min(data.min_y + 1, min_y)
                max_x = max(data.max_x - 1, max_x)
                max_y = max(data.max_y - 1, max_y)
                lengths.append(data)
        # Step 3: Compute floating-point center
        center_x = (min_x + max_x) / 2.0
        center_y = (min_y + max_y) / 2.0
        if(len(lengths)>2):
            max_steps = 0
            winer = None
            for f in sondes:
                max_steps= max(max_steps,f.data.steps)
            for f in sondes:
                if f.data.steps == max_steps:
                    winner = f
                    win_dir = winner.direction
                    normal = win_dir.get_normal()
                    width = sonde_dic.get(normal)
                    if width is None:
                        width = sonde_dic.get(normal.opposite())

                    pass


            lenght_x = lengths[0].steps
            lenght_y = lengths[1].steps
        else:
            lenght_x=1
            lenght_y=1
        return (lenght_x, lenght_y, center_x, center_y)

    def scan_for_blockages(self, dx, dy):
        steps = 0
        height, width = self.world.grid.shape
        x_curr, y_curr = self.get_center()
        while True:
            x_next = x_curr + dx
            y_next = y_curr + dy
            if x_next < 0 or x_next >= width or y_next < 0 or y_next >= height:
                break
            if not self.world.is_food(int(x_next), int(y_next)) or self.world.is_occupied(int(x_next), int(y_next)):
                break
            steps += 1
            x_curr, y_curr = x_next, y_next
        return steps

    def update_bounding_box_and_center(self, min_x, max_x, min_y, max_y):
        if not self.root_cells:
            return
        self.set_position((min_x + max_x) / 2.0, (min_y + max_y) / 2.0)

    def draw_margin(self, surface, vp, color=(0, 255, 0), width=2):
        box = self.collision_box
        cx, cy = box.get_center()
        cx, cy = vp.convert(cx, cy)
        nx, ny = box.get_normal().direction
        length = 1.5 * self.left_margin * vp.zoom_factor
        color = (200, 0, 0)
        self.draw_arrow(cx, cy, nx, ny, vp, surface, color, length, width)
        nx, ny = -nx, -ny
        length = 1.5 * self.right_margin * vp.zoom_factor
        self.draw_arrow(cx, cy, nx, ny, vp, surface, color, length, width)

    def draw_normal_arrow(self, surface, vp, color=(0, 255, 0), width=2):

        box = self.collision_box
        # 1) Get the center and normal from the box
        cx, cy = box.get_center()
        cx, cy = vp.convert(cx, cy)
        nx, ny = box.get_normal().direction  # might not be unit-length
        # If the user wants to draw on 'left', invert the normal
        if self.left_inside == False:
            nx, ny = -nx, -ny
        # 2) Normalize the normal vector
        mag = math.hypot(nx, ny)
        if mag == 0:
            return  # No valid direction to draw
        nx /= mag
        ny /= mag
        length = 15
        self.draw_arrow(cx, cy, nx, ny, vp, surface, color, length, width)

    def draw_arrow(self, cx, cy, nx, ny, vp, surface, color, length, width=2):
        # 3) Calculate the end of the arrow line
        end_x = cx + nx * vp.zoom_factor * length
        end_y = cy + ny * vp.zoom_factor * length

        # 4) Draw the main arrow line
        pygame.draw.line(surface, color, (cx, cy), (end_x, end_y), width)

        # 5) Draw an arrowhead (small lines angled ~30° off the main direction)
        arrow_size = 10  # length of each arrowhead side
        arrow_angle_deg = 30  # how wide the arrowhead angle is
        arrow_angle_rad = math.radians(arrow_angle_deg)

        # We'll rotate the normalized vector +/- arrow_angle_rad
        # to get two lines forming the arrowhead
        # Vector rotation formula: (x*cosθ - y*sinθ, x*sinθ + y*cosθ)

        # Left arrowhead direction
        left_dx = nx * math.cos(arrow_angle_rad) - ny * math.sin(arrow_angle_rad)
        left_dy = nx * math.sin(arrow_angle_rad) + ny * math.cos(arrow_angle_rad)

        # Right arrowhead direction (negative angle)
        right_dx = nx * math.cos(-arrow_angle_rad) - ny * math.sin(-arrow_angle_rad)
        right_dy = nx * math.sin(-arrow_angle_rad) + ny * math.cos(-arrow_angle_rad)

        # Convert those directions into the tip coordinates
        left_x = end_x - left_dx * arrow_size
        left_y = end_y - left_dy * arrow_size
        right_x = end_x - right_dx * arrow_size
        right_y = end_y - right_dy * arrow_size

        # Draw lines for the arrowhead
        pygame.draw.line(surface, color, (end_x, end_y), (left_x, left_y), width)
        pygame.draw.line(surface, color, (end_x, end_y), (right_x, right_y), width)

    def draw(self, screen, vp):

        for cell in self.root_cells:
            sx, sy = vp.convert(cell.x, cell.y)
            if cell.is_root:
                colour = (100, 200, 160)
            elif cell.is_stem:
                colour = (200, 0, 0)
            else:
                if self.is_outer_wall():
                    colour = (0, 0, 100)
                else:
                    colour = (25, 25, 255)
            if self.selected:
                colour = (255,0,0)
            pygame.draw.rect(screen, colour, pygame.Rect(sx, sy, 1, 1))
        for cell in self.core_cells:
            sx, sy = vp.convert(cell.x, cell.y)
            pygame.draw.rect(screen, (100, 200, 160), pygame.Rect(sx, sy, 1, 1))

        if self.alive:
            if self.is_outer_wall():
                colour = (200, 200, 20)
            else:
                colour = (255, 255, 0)
        else:
            colour = (255, 0, 0)

        corners = self.corners()
        corners_ = []

        for c in corners:
            cp = vp.convert(c[0], c[1])
            corners_.append(cp)
        pygame.draw.polygon(screen, colour, corners_, 1)
        x, y = self.get_center()
        x, y = vp.convert(x, y)
        pygame.draw.circle(screen, colour, (x, y), 1)
        if self.is_outer_wall():
            self.draw_normal_arrow(screen, vp)
        if self.left_margin is not None and self.right_margin is not None:
            self.draw_margin(screen, vp, (0, 0, 0))
        for p in self.outward_points:
            x = p[0]
            y = p[1]
            x, y = vp.convert(x, y)
            colour = (0, 255, 0)
            pygame.draw.circle(screen, colour, (x, y), 1)

        if self.selected:
            for c in self.crawl_points:
                x = c[0]
                y = c[1]
                x, y = vp.convert(x, y)
                colour = (0, 255, 0)
                pygame.draw.circle(screen, colour, (x, y), 1)

    def center_on_food(self):
        x, y = self.get_center()
        return self.world.is_food(x, y)

    def can_merge_with(self, other):
        if not isinstance(other, Mushroom) or self is other:
            return False
        if self.collidepoint(other.center_x, other.center_y):
            tolerance = 0.1
            same_x = abs(self.center_x - other.center_x) < tolerance
            same_y = abs(self.center_y - other.center_y) < tolerance
            return same_x or same_y
        return False

    def merge_with(self, other):
        print(f"Merging Mushroom {self.id} with {other.id}")
        self.root_cells.update(other.root_cells)
        self.core_cells.update(other.core_cells)
        self.branches.extend(other.branches)
        for cell in other.root_cells | other.core_cells:
            self.world.occupied[cell.y, cell.x] = self.id
        min_x, max_x, min_y, max_y = self.ray_trace_from_center()
        self.update_bounding_box_and_center(min_x, max_x, min_y, max_y)
        self.kill()
        # other.alive = False

    def create_branche(self, x, y):
        if self.world.is_occupied(x, y):
            return
        if self.world.is_within_bounds(x, y):
            branch = self.world.create_mushroom(x, y)
            if branch is not None:
                self.branches.append(branch)
        else:
            pass

    def collidepoint(self, x, y):
        rect = self.get_world_rect()
        return rect.is_point_inside(int(x), int(y))

    def get_world_rect(self):
        return self.collision_box

    def record_stack_trace(self):
        y = self.collision_box.center_y
        x = self.collision_box.center_x
        self.world.print_snapshot(x,y)
