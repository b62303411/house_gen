import logging

import pygame


class Window:
    def __init__(self, x, y, width, height, title="Action Menu"):
        self.components = set()
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.visible = True
        self.rect = pygame.Rect(x, y, width, height)



    def show(self):
        """Show the pop-up."""
        self.visible = True
        logging.info("view")

    def hide(self):
        """Hide the pop-up."""
        self.visible = False

    def draw(self, surface):
        """Draw the pop-up and its button if visible."""
        if not self.visible:
            return

        # Pop-up background + border
        pygame.draw.rect(surface, (50, 50, 50), self.rect)
        pygame.draw.rect(surface, (255, 255, 255), self.rect, 2)

        for c in self.components:
            c.draw(surface)