import pygame


class TextBox:
    def __init__(self, parent, lines, position):
        self.lines = lines
        self.parent = parent
        self.position = position
        self.color = (255, 255, 255)
        self.vertical_spacing = 15
        self.font = pygame.font.SysFont(None, 14)

    def set_text(self, text):
        self.lines = text

    def get_center_x(self):
        return self.parent.rect.centerx

    def get_y(self):
        return self.parent.rect.y

    def draw(self, surface):
        center_x, start_y = self.get_center_x(), self.get_y() + 50
        for i, text_str in enumerate(self.lines):
            text_surface = self.font.render(text_str, True, self.color)
            text_rect = text_surface.get_rect(center=(center_x, start_y + i * self.vertical_spacing))
            surface.blit(text_surface, text_rect)

    def handle_event(self, event, on_button_click=None):
        pass
