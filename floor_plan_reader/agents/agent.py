import pygame


class Agent:
    def __init__(self, agent_id):
        self.id = agent_id

    def __eq__(self, other):
        """Check equality based on x and y values."""
        if isinstance(other, Agent):
            return self.id == other.id
        return False

    def __hash__(self):
        return hash(self.id)

    def run(self):
        pass

    def draw(self, screen, zoom_factor, offset_x, offset_y):
        pass

    def collidepoint(self, x, y):
        rect = self.get_world_rect()
        collide = rect.collidepoint(x, y)
        return collide

    def get_world_rect(self):
        return pygame.Rect(0, 0, 1, 1)

    def get_rect(self, zoom_factor=1.0):
        """
        Return a pygame.Rect that represents this agents's
        axis-aligned bounding box in *screen space* (after zoom).
        By default, we treat the agents's (x,y) as its center or top-left.
        We'll implement it in child classes.
        """
        return pygame.Rect(0, 0, 0, 0)
