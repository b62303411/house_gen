import random

import pygame

from floor_plan_reader.agents.agent import Agent
from floor_plan_reader.cell import Cell
from floor_plan_reader.math.bounding_box import BoundingBox


class Blob(Agent):
    def __init__(self, agent_id, world, x, y):
        super().__init__(agent_id)
        self.world = world
        self.cells = set()
        self.growth = set()
        self.free_slot = set()
        self.origin = Cell(x, y)
        self.cells.add(self.origin)
        self.growth.add(self.origin)
        self.status = "born"

        self.len_start = 0
        self.active_mush = None
        self._walls = set()
        self._dead_walls = set()
        self._intersections = set()
        self.bounding_box = None

    def __lt__(self, other):
        # Compare based on the 'value' attribute
        return self.blob_size() < other.blob_size()

    def free(self, cell):
        if cell in self.cells:
            self.free_slot.add(cell)

    def is_food(self, x, y):
        return self.world.is_food(x, y)

    def get_walls(self):
        return self._walls.copy()

    def get_intersections(self):
        return self._intersections

    def get_wall_count(self):
        return len(self._walls)

    def is_blob(self, x, y):
        return self.world.is_blob(x, y)

    def blob_size(self):
        return len(self.cells)

    def get_center(self):
        return self.bounding_box.get_center()

    def get_corners(self):
        return self.bounding_box

    def get_shape(self):
        return self.bounding_box.get_shape()

    def add_growth(self, cell):
        self.growth.add(cell)

    def eat(self, other):
        for g in other.growth:
            if g not in self.cells:
                self.add_growth(g)
        for c in other.cells:
            self.world.set_blob(c.x, c.y, self)
            self.cells.add(c)
        other.alive = False

    def calculate_bounding_box(self):
        cells = self.cells
        min_x = min(cell.x for cell in cells)
        max_x = max(cell.x for cell in cells)
        min_y = min(cell.y for cell in cells)
        max_y = max(cell.y for cell in cells)
        self.bounding_box = BoundingBox(min_x, min_y, max_x, max_y)

    def germinate(self, g):
        coord_list = self.world.get_neighbors_8(g.x, g.y)
        for c in coord_list:
            x, y = c[0], c[1]
            candidate = Cell(x, y)
            if candidate not in self.cells:
                if self.world.is_within_bounds(x, y):
                    if self.is_food(x, y):
                        if not self.world.is_blob(x, y):
                            self.add_growth(candidate)
                            self.cells.add(candidate)
                            self.world.set_blob(x, y, self)
                        else:
                            blob = self.world.get_blob(x, y)
                            if blob is not None:
                                if blob.id != self.id:
                                    if self.blob_size() > blob.blob_size():
                                        self.eat(blob)
        self.growth.remove(g)

    def grow(self):
        growth = self.growth.copy()
        for g in growth:
            self.germinate(g)

        pass

    def calculate_bounding_box(self):
        self.bounding_box = BoundingBox.from_cells(self.cells)

    def add_intersection(self, i):
        self._intersections.add(i)

    def run(self):
        if self.status == "born":
            self.status = "grow"
            return
        elif self.status == "grow":
            size = self.blob_size()
            self.grow()
            size_after = self.blob_size()
            if not size_after > size:
                if size_after > 8:
                    self.status = "mush"
                    self.calculate_bounding_box()
                    for c in self.cells:
                        self.free_slot.add(c)
                else:
                    self.status = "cleanup"
            return
        elif self.status == "mush":
            length = len(self.free_slot)
            free = self.free_slot.copy()
            for s in free:
                if self.world.is_occupied(s.x, s.y) or self.world.is_wall_occupied(s.x, s.y):
                    self.free_slot.remove(s)
            if length != len(self.free_slot) and length > 0:
                self.status = "mush"
            elif length > 0:
                if self.active_mush is None or self.active_mush.get_state() == 'done' or self.active_mush.alive == False:
                    first_element = self.pick_random_free()
                    self.create_mushroom(first_element.x, first_element.y)
                if self.get_wall_count() > 15:
                    self.print_blob()
            else:
                self.status = "done"
            return
        elif self.status == "done":
            self.purge_dead_walls()
            return
        elif self.status == "cleanup":
            for c in self.cells:
                self.world.draw_at((c.x, c.y), 0)
            self.alive = False

    def pick_random_free(self):
        selected = random.choice(list(self.free_slot))
        return selected
    def print_blob(self):
        x, y = self.get_center()
        width, height = self.bounding_box.get_shape()
        self.world.print_snapshot(x, y, width + 2, height + 2, "blob")

    def get_snapshot(self):
        x, y = self.get_center()
        width, height = self.bounding_box.get_shape()
        return self.world.get_grid_snapwhot(x, y, width, height)

    def get_occupied_snapshot(self):
        x, y = self.get_center()
        width, height = self.bounding_box.get_shape()
        return self.world.get_occupied_snapshot(x, y, width, height)

    def purge_dead_walls(self):
        walls = self._walls.copy()
        for w in walls:
            if not w.alive:
                self._walls.remove(w)
                self._dead_walls.add(w)

    def full_reset(self):
        copy = self._walls.copy()
        for w in copy:
            w.kill()
            cells = w.get_cells()
            for c in cells:
                self.free_slot.add(c)
            self._walls.remove(w)
        self.alive = True
        self.status = "mush"

    def create_mushroom(self, x, y):
        c = Cell(x, y)
        self.free_slot.remove(c)

        self.active_mush = self.world.create_mushroom(self, x, y)

        wall_seg_id = self.world.get_occupied_wall_id(x, y)
        if wall_seg_id != 0:
            wall = self.world.get_occupied_wall_by_id(wall_seg_id)

            if wall is not None:
                self.active_mush.seg = wall
                wall.add(self.active_mush)
        self._walls.add(self.active_mush)

    def draw_cells(self, screen, vp, cells, colour):
        for cell in cells:
            sx, sy = vp.convert(cell.x, cell.y)
            pygame.draw.rect(screen, colour, pygame.Rect(sx, sy, 1, 1))

    def draw(self, screen, vp):
        if self.status == "done":
            return
        colour = (200, 0, 0)
        if self.status != "mush":
            self.draw_cells(screen, vp, self.cells, colour)
        else:
            colour = (0, 255, 0)
            self.draw_cells(screen, vp, self.free_slot, colour)
