from decimal import Decimal

import pygame
from pygame import font
from floor_plan_reader.agent import Agent
from floor_plan_reader.cell import Cell
from floor_plan_reader.collision_box import CollisionBox


class Scores:
    def __init__(self, id, score):
        self.id = id
        self.score = score

    def __eq__(self, other):
        if not isinstance(other, Scores):
            return False
        return self.id == other.id

    def __hash__(self):
        return hash(id)


class WallSegment(Agent):

    def __init__(self, id):
        super().__init__(id)
        self.scores = set()
        self.parts = set()
        self.set_collision_box(CollisionBox(0, 0, 1, 1, 0))  # Will be set after ray trace
        self.alive = True
        self.state = "idle"
        font.init()
        self.f = font.Font(None, 8)

    def set_collision_box(self, cb):
        if isinstance(cb, CollisionBox):
            self.collision_box = cb.copy()

    def add_part(self, part):
        self.parts.add(part)
        self.state = "negotiate"

    def run(self):
        self.process_state()

    def is_selected(self):
        for p in self.parts:
            if p.selected:
                return True
        return False

    def set_position(self,x,y):
        self.collision_box.set_position(x,y)
    def negotiate_phase(self):
        min_x = Decimal(999)
        min_y = Decimal(999)
        max_x = Decimal(0)
        max_y = Decimal(0)
        sx = Decimal(0)
        sy = Decimal(0)
        width = Decimal(0)
        cb = None
        for p in self.parts:
            ratio = p.get_covered_ratio()
            s = Scores(p.id, ratio)
            self.scores.add(s)
            if cb is None:
                cb = p.collision_box.copy()
            else:
                cb = cb.merge_aligned(p.collision_box)
            c = p.get_center()

            x = Decimal(c[0])
            y = Decimal(c[1])
            sy = Decimal(sy + y)
            sx = Decimal(sx + x)
            min_x = min(x, min_x)
            min_y = min(y, min_y)
            max_y = max(x, max_y)
            max_x = max(x, max_x)
            self.collision_box.rotation = p.collision_box.rotation
            width = max(width, p.collision_box.width)
        part_count = Decimal(len(self.parts))
        x = sx / part_count
        y = sy / part_count
        self.set_position(x, y)
        self.collision_box.set_width(width)
        self.collision_box.set_lenght(max(max_x - min_x, max_y - min_y))
        self.set_collision_box(cb)

    def process_state(self):

        wrongs =[]
        if self.state == "error":
            for n in self.parts:
                for i in self.parts:
                    if not n.collision_box.is_on_same_axis_as(i.collision_box):
                        wrongs.append(i)
            print("")
        if self.state == "negotiate":
            self.negotiate_phase()
            for n in self.parts:
                if self.collision_box.width > 2*n.collision_box.width:
                    self.state="error"
                    break
            self.state = "idle"
    def fill_box(self):
        pixels = self.collision_box.iterate_covered_pixels()
        for p in pixels:
            x = p[0]
            y = p[1]
            self.world.occupy_wall(x, y, self)

    def corners(self):
        return self.collision_box.calculate_corners()

    def get_center(self):
        return self.collision_box.get_center()

    def draw(self, screen, vp):

        if self.alive:
            colour = (255, 50, 200)
        else:
            colour = (255, 0, 200)
        if self.state=="error":
            colour = (255, 0, 0)
        corners = self.corners()
        corners_ = []

        for c in corners:
            cp = vp.convert(c[0], c[1])
            corners_.append(cp)
        size = 1
        if self.is_selected():
            size = 3
        pygame.draw.polygon(screen, colour, corners_, size)
        x, y = self.get_center()
        x, y = vp.convert(x, y)
        pygame.draw.circle(screen, colour, (x, y), 1)
        self.f = font.Font(None, int(vp.zoom_factor * 8))
        for p in self.parts:
            score = p.get_covered_ratio()
            x, y = p.get_center()
            x, y = vp.convert(x, y)
            text_surface = self.f.render(f"s: {score:.{2}f}", True, (15, 255, 0))
            screen.blit(text_surface, (x, y))  # Position (x=10, y=10)
