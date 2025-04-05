import logging

import pygame
from shapely import Polygon, LineString


class BoundingBox:
    def __init__(self, min_x, min_y, max_x, max_y):
        self.min_x = min_x
        self.max_x = max_x
        self.min_y = min_y
        self.max_y = max_y
        self.rect = None
        self.poly = None

    @staticmethod
    def from_cells(cells):
        min_x = min(cell.x for cell in cells)
        max_x = max(cell.x for cell in cells)
        min_y = min(cell.y for cell in cells)
        max_y = max(cell.y for cell in cells)
        return BoundingBox(min_x, min_y, max_x, max_y)

    def get_poly(self):
        if self.poly is None:
            self.poly = Polygon([
                (self.min_x, self.min_y),
                (self.max_x, self.min_y),
                (self.max_x, self.max_y),
                (self.min_x, self.max_y)
            ])
        return self.poly

    def getRect(self):
        if self.rect is not None:
            return self.rect
        # Compute the rectangle's top-left corner and its width/height.
        # Typically, min_x < max_x and min_y < max_y.
        width = self.max_x - self.min_x
        height = self.max_y - self.min_y
        # Create a pygame.Rect using these dimensions
        self.rect = pygame.Rect(self.min_x, self.min_y, width, height)
        return self.rect

    def collidepoint(self, x, y):
        rect = self.getRect()
        # Use Pygame's built-in collision check
        return rect.collidepoint(x, y)

    def collide_line(self, x1, y1, x2, y2):
        # A rectangle can be represented as a polygon
        # A line can be represented as a LineString
        line = LineString([(x1, y1), (x2, y2)])
        # Check intersection
        if self.get_poly().intersects(line):
            logging.debug("Line intersects the rectangle!")
        else:
            logging.debug("No intersection.")

    def get_center(self):
        x = (self.min_x + self.max_x) / 2
        y = (self.max_y + self.min_y) / 2
        return x, y

    def get_shape(self):
        width = self.max_x - self.min_x
        height = self.max_y - self.min_y
        return width,height
