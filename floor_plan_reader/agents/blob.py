import pygame

from floor_plan_reader.agents.agent import Agent
from floor_plan_reader.cell import Cell
from floor_plan_reader.math.bounding_box import BoundingBox


class Blob(Agent):
    def __init__(self, id, world, x, y):
        super().__init__(id)
        self.world = world
        self.cells = set()
        self.growth = set()
        self.free_slot = set()
        self.origin = Cell(x, y)
        self.cells.add(self.origin)
        self.growth.add(self.origin)
        self.status = "born"
        self.alive = True
        self.len_start = 0
        self.active_mush = None
        self.walls = set()
        self.bounding_box = None

    def is_food(self, x, y):
        return self.world.is_food(x, y)

    def is_blob(self, x, y):
        return self.world.blob_grid

    def blob_size(self):
        return len(self.cells)

    def eat(self, other):
        for g in other.growth:
            if g not in self.cells:
                self.growth.add(g)
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
                            self.growth.add(candidate)
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

    def run(self):
        if self.status == "born":
            self.status = "grow"
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
        elif self.status == "mush":
            length = len(self.free_slot)
            free = self.free_slot.copy()
            for s in free:
                if self.world.is_occupied(s.x, s.y) or self.world.is_wall_occupied(s.x,s.y):
                    self.free_slot.remove(s)
            if length != len(self.free_slot) and length > 0:
                self.status = "mush"
            elif length > 0:
                if self.active_mush is None or self.active_mush.get_state() == 'done' or self.active_mush.alive == False:
                    first_element = next(iter(self.free_slot))
                    self.create_mushroom(first_element.x, first_element.y)
                if len(self.walls) > 15:
                    #x, y, width = 20, height = 20
                    x,y = self.bounding_box.get_center()
                    width ,height = self.bounding_box.get_shape()
                    self.world.print_snapshot(x,y,width+2,height+2,"blob")
            else:
                self.alive = False
            pass
        elif self.status == "cleanup":
            for c in self.cells:
                self.world.draw_at((c.x, c.y), 0)
            self.alive = False

    def create_mushroom(self, x, y):
        c = Cell(x, y)
        self.free_slot.remove(c)
        self.active_mush = self.world.create_mushroom(self, x, y)
        self.walls.add(self.active_mush)

    def draw(self, screen, vp):
        colour = (200, 0, 0)
        if self.status != "mush":
            for cell in self.cells:
                sx, sy = vp.convert(cell.x, cell.y)
                pygame.draw.rect(screen, colour, pygame.Rect(sx, sy, 1, 1))
        else:
            colour = (0, 255, 0)
            for cell in self.free_slot:
                sx, sy = vp.convert(cell.x, cell.y)
                pygame.draw.rect(screen, colour, pygame.Rect(sx, sy, 1, 1))
