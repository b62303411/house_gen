import pygame


class Button:
    def __init__(self,parent, text, position):
        self.font = pygame.font.SysFont(None, 24)
        self.text = text
        self.position = position
        btn_w, btn_h = 100, 40
        self.button_rect = pygame.Rect(
            parent.x + (parent.width - btn_w) // 2,
            parent.y + parent.height - btn_h - self.position.y,  # near bottom
            btn_w,
            btn_h
        )
        self.on_button_click=None

    def draw(self, surface):
        white = (255, 255, 255)
        pygame.draw.rect(surface, (100, 100, 200), self.button_rect)
        pygame.draw.rect(surface, white, self.button_rect, 2)
        label_text = self.font.render(self.text, True, white)
        label_rect = label_text.get_rect(center=self.button_rect.center)
        surface.blit(label_text, label_rect)

    def handle_event(self, event, on_button_click=None):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos

            if self.button_rect.collidepoint(mx, my):
                if self.on_button_click is not None:
                    self.on_button_click()
                # Check if user clicked the button
                if on_button_click:
                    on_button_click()