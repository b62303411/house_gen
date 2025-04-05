import pygame

from floor_plan_reader.display.arrow import Arrow
from floor_plan_reader.display.bounding_box_drawer import BoundingBoxDrawer
from floor_plan_reader.display.cell_renderer import CellRenderer


class MushroomDraw:
    def __init__(self, mushroom):
        self.cell_render = CellRenderer()
        self.bb_drawer = BoundingBoxDrawer()
        self.selected = False
        self.mushroom = mushroom

    def get_collision_box(self):
        return self.mushroom.collision_box

    def get_margins(self):
        return self.mushroom.left_margin, self.mushroom.right_margin

    def get_left_inside(self):
        return self.mushroom.left_inside

    def get_state(self):
        return self.mushroom.get_state()

    def id_alive(self):
        return self.mushroom.alive

    def get_outward_points(self):
        return self.mushroom.outward_points

    def get_root_cells(self):
        return self.mushroom.root_cells

    def get_core_cells(self):
        return self.mushroom.core_cells

    def get_crawl_points(self):
        return self.mushroom.crawl_points

    def is_outer_wall(self):
        return self.mushroom.is_outer_wall()

    def get_center(self):
        return self.mushroom.get_center()

    def draw_margin(self, surface, vp, color=(0, 255, 0), width=2):
        left_margin, right_margin = self.get_margins()
        box = self.get_collision_box()
        cx, cy = box.get_center()
        cx, cy = vp.convert(cx, cy)
        nx, ny = box.get_normal().direction
        length = 1.5 * left_margin * vp.zoom_factor
        color = (200, 0, 0)
        self.draw_arrow(cx, cy, nx, ny, vp, surface, color, length, width)
        nx, ny = -nx, -ny
        length = 1.5 * right_margin * vp.zoom_factor
        self.draw_arrow(cx, cy, nx, ny, vp, surface, color, length, width)

    def draw_normal_arrow(self, surface, vp, color=(0, 255, 0), width=2):
        box = self.get_collision_box()
        # 1) Get the center and normal from the box
        cx, cy = box.get_center()
        cx, cy = vp.convert(cx, cy)
        nx, ny = box.get_normal().direction  # might not be unit-length
        # If the user wants to draw on 'left', invert the normal
        if not self.get_left_inside():
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
        collision_box = self.get_collision_box()
        left_margin, right_margin = self.get_margins()

        if self.get_state() != "done":
            self.draw_cells(self.get_root_cells(), screen, vp)
            self.draw_cells(self.get_core_cells(), screen, vp)

        OUTER_WALL_BLUE = (50, 11, 168)
        RED = (255, 0, 0)
        colour = OUTER_WALL_BLUE

        if self.id_alive():
            if self.is_outer_wall():
                colour = OUTER_WALL_BLUE
            else:
                colour = (111, 50, 168)
        else:
            colour = RED
        if collision_box is not None:
            self.bb_drawer.draw(collision_box, screen, vp, colour)

        x, y = self.get_center()
        x, y = vp.convert(x, y)
        pygame.draw.circle(screen, colour, (x, y), 1)
        if self.is_outer_wall():
            self.draw_normal_arrow(screen, vp)
        if left_margin is not None and right_margin is not None:
            self.draw_margin(screen, vp, (0, 0, 0))
        for p in self.get_outward_points():
            x = p[0]
            y = p[1]
            x, y = vp.convert(x, y)
            colour = (0, 255, 0)
            pygame.draw.circle(screen, colour, (x, y), 1)

        if self.selected:
            for c in self.get_crawl_points():
                x = c[0]
                y = c[1]
                x, y = vp.convert(x, y)
                colour = (0, 255, 0)
                pygame.draw.circle(screen, colour, (x, y), 1)
