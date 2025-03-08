import math
import random
from collections import deque

import pygame

from agent import Agent
from cell import Cell
from collision_box import CollisionBox


class Mushroom(Agent):
    def __init__(self, start_x, start_y, world, mush_id):
        super().__init__(mush_id)
        self.world = world
        self.root_cells = set([Cell(start_x, start_y)])
        self.core_cells = set()
        self.collision_box = CollisionBox(start_x, start_y, 1, 1, 0)  # Will be set after ray trace
        self.alive = True
        self.state = "ray_trace"
        self.growth_cells = set()
        self.max_width = 1

    def get_center(self):
        return self.collision_box.get_center()

    def run(self):
        self.process_state()

    def process_state(self):
        """State machine for floor plan resolution."""
        if self.state == "ray_trace":
            self.ray_trace_phase()
            self.state = "stem_growth"
        elif self.state == "stem_growth":
            self.stem_growth_phase()
            self.state = "width_assessment"
        elif self.state == "width_assessment":
            self.width_assessment_phase()
            self.state = "width_expansion"
        elif self.state == "width_expansion":
            self.width_ray_trace()
            self.state = "pruning"
        elif self.state == "pruning":
            self.prunning_phase()
        elif self.state == "perimeter_reaction":
            self.perimeter_reaction_phase()
            self.state = "growth" if self.has_growth_cells() else "done"
        elif self.state == "growth":
            self.growth_phase()
            self.state = "ray_trace" if self.has_growth_cells() else "done"
        # min_x, max_x, min_y, max_y = self.ray_trace()
        # self.update_bounding_box_and_center(min_x, max_x, min_y, max_y)

    def calculate_rotation_from_direction(self, dx, dy):
        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad)
        # Normalize angle to nearest 45 degrees
        angle_deg = round(angle_deg / 45) * 45
        return angle_deg % 360

    def prunning_phase(self):
        if self.center_on_food():
            pass
        else:
            self.alive = False

    def ray_trace_phase(self):
        """Determine the longest axis."""
        dx, dy, cx, cy = self.ray_trace()

        self.stem_length = int(max(abs(dx), abs(dy)))
        self.collision_box.length = self.stem_length
        self.collision_box.width = int(min(abs(dx), abs(dy)))
        self.collision_box.center_y = cy
        self.collision_box.center_x = cx
        angle = self.calculate_rotation_from_direction(dx, dy)
        self.collision_box.rotation = angle
        direction = (1, 0) if abs(dx) > abs(dy) and dx > 0 else (-1, 0) if abs(dx) > abs(dy) else (
            0, 1) if dy > 0 else (0, -1)
        x, y = self.collision_box.get_center()

        print(
            f"Mushroom {self.id}: Ray trace - length={self.stem_length}, direction={direction}, center=({x}, {y})")

    def stem_growth_phase(self):
        """Grow a stem along the longest axis."""
        x, y = self.collision_box.get_center()
        self.stem_points = []
        for i in range(self.stem_length + 1):
            sx = int(x + self.collision_box.default_direction[0] * i)
            sy = int(y + self.collision_box.default_direction[1] * i)
            if self.world.is_food(sx, sy) and not self.world.is_occupied(sx, sy):
                cell = Cell(sx, sy)
                self.root_cells.add(cell)
                self.world.occupied[sy, sx] = self.id
                self.stem_points.append(cell)
        print(f"Mushroom {self.id}: Stem grown - {len(self.stem_points)} points")

    def width_assessment_phase(self):
        """Assess available width at each stem point."""
        self.widths = {}
        perpendicular = (-self.collision_box.default_direction[1], self.collision_box.default_direction[0])
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
        # Compute normalized direction and normal vector
        dx, dy = self.collision_box.default_direction
        magnitude = (dx ** 2 + dy ** 2) ** 0.5
        norm_dir = (dx / magnitude, dy / magnitude)
        normal = (-norm_dir[1], norm_dir[0])  # Unit normal vector

        # Track min/max points along the normal direction
        min_parallel = float('inf')
        max_parallel = float('-inf')
        min_thikness = float('inf')
        for cell in self.root_cells:
            # Left direction: opposite of the normal vector
            left_dx, left_dy = -normal[0], -normal[1]
            left_steps = self.trace_food_boundary(cell.x, cell.y, left_dx, left_dy)

            # Right direction: along the normal vector
            right_dx, right_dy = normal[0], normal[1]
            right_steps = self.trace_food_boundary(cell.x, cell.y, right_dx, right_dy)

            thickness = left_steps + right_steps
            min_thikness = min(min_thikness, thickness)
            # Calculate boundary points using displacement vectors
            left_point = (
                cell.x + left_dx * left_steps,
                cell.y + left_dy * left_steps
            )
            right_point = (
                cell.x + right_dx * right_steps,
                cell.y + right_dy * right_steps
            )

            # Project points onto the normal vector to find width
            # (dot product with normal gives signed distance)
            left_projection = left_point[0] * normal[0] + left_point[1] * normal[1]
            right_projection = right_point[0] * normal[0] + right_point[1] * normal[1]

            min_parallel = min(min_parallel, left_projection, right_projection)
            max_parallel = max(max_parallel, left_projection, right_projection)

        # Stem width is the difference between max and min projections
        stem_width = max_parallel - min_parallel

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
        """Expand stem to full available width."""
        perpendicular = (-self.direction[1], self.direction[0])
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
            new_mushroom = Mushroom(candidate.x, candidate.y, self.world, random.randint(1, 2 ** 31 - 1))
            self.world.agents.append(new_mushroom)
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

    def ray_trace(self):
        center_x, center_y = self.get_center()
        values = self.scan_for_walls(center_x, center_y, self.collision_box.get_direction())
        return values

    def measure_extent(self, x, y, dx, dy):
        """Measure extent along a given direction vector (dx, dy) properly.
       - First, crawl backward to find the start.
       - Then, count forward to find the total steps.
        """
        height, width = self.world.grid.shape

        # Step 1: Crawl backward until hitting a boundary
        while 0 <= x < width and 0 <= y < height and self.world.is_food(int(x), int(y)):
            x -= dx
            y -= dy
            min_x = x
            min_y = y

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

        return (steps, min_x, min_y, max_x, max_y)  # The total step count along this direction

    def scan_for_walls(self, x, y, direction):
        lengths = []
        directions = [(1, 0), (0, 1)]
        min_x = 900
        min_y = 900
        max_x = 0
        max_y = 0
        for d in directions:
            data = self.measure_extent(x, y, d[0], d[1])
            min_x = min(data[1] + 1, min_x)
            min_y = min(data[2] + 1, min_y)
            max_x = max(data[3] - 1, max_x)
            max_y = max(data[4] - 1, max_y)
            lengths.append(data)
        # Step 3: Compute floating-point center
        center_x = (min_x + max_x) / 2.0
        center_y = (min_y + max_y) / 2.0
        lenght_x = lengths[0][0]
        lenght_y = lengths[1][0]

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
        self.collision_box.center_x = (min_x + max_x) / 2.0
        self.collision_box.center_y = (min_y + max_y) / 2.0

    def draw(self, screen, vp):
        for cell in self.root_cells:
            sx, sy = vp.convert(cell.x, cell.y)
            if cell.is_root:
                colour = (100, 200, 160)
            elif cell.is_stem:
                colour = (200, 0, 0)
            else:
                colour = (0, 0, 255)
            pygame.draw.rect(screen, colour, pygame.Rect(sx, sy, 1, 1))
        for cell in self.core_cells:
            sx, sy = vp.convert(cell.x, cell.y)
            pygame.draw.rect(screen, (100, 200, 160), pygame.Rect(sx, sy, 1, 1))
        corners = self.collision_box.calculate_corners()
        corners_ = []
        for c in corners:
            cp = vp.convert(c[0], c[1])
            corners_.append(cp)
        pygame.draw.polygon(screen, (255, 200, 0), corners_, 1)

    def center_on_food(self):
        x, y = self.collision_box.get_center()
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
        min_x, max_x, min_y, max_y = self.ray_trace()
        self.update_bounding_box_and_center(min_x, max_x, min_y, max_y)
        other.alive = False

    def create_branche(self, x, y):
        if self.world.is_occupied(x, y):
            return
        branch_id = random.randint(1, 2 ** 31 - 1)
        branche = Mushroom(x, y, self.world, branch_id)
        self.branches.append(branche)
        self.world.candidates.append(branche)
        self.world.occupied[y, x] = branch_id

    def collidepoint(self, x, y):
        rect = self.get_world_rect()
        return rect.is_point_inside(x, y)

    def get_world_rect(self):
        return self.collision_box
