import pygame

from floor_plan_reader.agent.agent import Agent
from floor_plan_reader.cell import Cell
from floor_plan_reader.display.arrow import Arrow
from floor_plan_reader.display.bounding_box_drawer import BoundingBoxDrawer
from floor_plan_reader.display.cell_renderer import CellRenderer
from floor_plan_reader.math.collision_box import CollisionBox
from floor_plan_reader.math.min_max import MinMax
from floor_plan_reader.math.vector import Vector
from floor_plan_reader.agent.mush_agent_state_machine import MushAgentStateMachine
from floor_plan_reader.wall_scanner import WallScanner


class Mushroom(Agent):
    def __init__(self,world, blob,start_x, start_y,mush_id):
        super().__init__(mush_id)
        self.perimeter = None
        self.wall_scanner = WallScanner(world)
        self.world = world
        self.outward_points = set()
        self.root_cells = set([Cell(start_x, start_y)])
        self.core_cells = set()
        self.collision_box = CollisionBox(start_x, start_y, 1, 1, 0)  # Will be set after ray trace
        self.alive = True

        self.growth_cells = set()
        self.max_width = 1
        self.overlapping = set()
        self.stem_points = set()
        self.crawl_points = set()
        self.collision_box_history = set()
        self.branches = []
        self.wall_segment = None
        self.left_margin = None
        self.left_inside = None
        self.right_margin = None
        self.right_inside = None
        self.selected = False
        self.co_axial_walls = set()
        self.state_machine = MushAgentStateMachine(self)
        self.cell_render = CellRenderer()
        self.bb_drawer = BoundingBoxDrawer()
        self.blob = blob

    def xor_bool(self, a, b):
        return bool(a) != bool(b)

    def is_outer_wall(self):
        if self.left_inside is not None and self.right_inside is not None:
            return self.xor_bool(self.left_inside, self.right_inside)
        return False

    def set_position(self, x, y):
        self.collision_box.set_position(x, y)

    def set_selected(self, selected):
        self.selected = selected

    def get_center(self):
        return self.collision_box.get_center()

    def run(self):
        self.process_state()

    def get_state(self):
        return self.state_machine.state

    def derive_direction_and_normal(self):
        return self.collision_box.derive_direction_and_normal()

    def is_centered(self):
        return abs(self.left_margin - self.right_margin) > 2

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

        right_dist = self.right_margin
        left_dist = self.left_margin
        # 2) Compute how far we are off. If right_dist is bigger, shift center outward.
        shift = (right_dist - left_dist) / 2.0
        nx = normal.direction[0]
        ny = normal.direction[1]
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
        self.state_machine.process_state()

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
        self.cell_render.generate_image(self.root_cells)

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

    def evaluate_segment_agregate(self, obj):
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
                        # print("hum")
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
            wall = self.world.create_wall_segment()
            self.wall_segment = wall
            wall.add_part(self)
            for coaxial in self.co_axial_walls:
                coaxial.wall_segment = wall
                wall.add_part(coaxial)
        else:
            if self.wall_segment is None:
                self.wall_segment = wall
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
        x, y = self.get_center()
        on_food = self.world.is_food(x, y)
        if not on_food:
            return False
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
        mushrooms = self.blob.mushrooms
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

            angle = self.collision_box.calculate_rotation_from_direction(dx, dy)
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

    def scan_for_walls(self, x, y, directions=list(
        map(lambda direction: Vector(direction), [(1, 0), (0, 1), (0.5, 0.5), (0.5, -0.5)]))):
        return self.wall_scanner.scan_for_walls(x, y, directions)

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

        length = 15
        self.draw_arrow(cx, cy, nx, ny, vp, surface, color, length, width)

    def draw_arrow(self, cx, cy, nx, ny, vp, surface, color, length, width=2):
        arrow = Arrow(cx, cy, nx, ny, length, width, color)

        arrow.draw(surface, vp)

    def draw_cells(self, cells, screen, vp):
        for cell in cells:
            sx, sy = vp.convert(cell.x, cell.y)
            pygame.draw.rect(screen, (100, 200, 160), pygame.Rect(sx, sy, 1, 1))

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
                colour = (255, 0, 0)
            pygame.draw.rect(screen, colour, pygame.Rect(sx, sy, 1, 1))

        self.draw_cells(self.core_cells,screen, vp)

        if self.alive:
            if self.is_outer_wall():
                colour = (200, 200, 20)
            else:
                colour = (255, 255, 0)
        else:
            colour = (255, 0, 0)
        if self.collision_box is not None:
            self.bb_drawer.draw(self.collision_box,screen,vp, colour)

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
        if not self.world.is_blob(x, y):
            self.world.create_blob(x, y)

    def collidepoint(self, x, y):
        rect = self.get_world_rect()
        return rect.is_point_inside(int(x), int(y))

    def get_world_rect(self):
        return self.collision_box

    def record_stack_trace(self):
        y = self.collision_box.center_y
        x = self.collision_box.center_x
        # self.world.print_snapshot(x, y)

    def print_box(self):
        y = self.collision_box.center_y
        x = self.collision_box.center_x
        height = self.collision_box.width
        width = self.collision_box.length
        self.world.print_snapshot(x, y, width + 10, height + 10, "debug")
