import pygame

from floor_plan_reader.display.button import Button
from floor_plan_reader.display.text_box import TextBox
from floor_plan_reader.display.window import Window


class PopupMenu(Window):
    def __init__(self, view, x, y, width, height, title="Action Menu"):
        self.view = view
        super().__init__(x, y, width, height)

        self.title = title

        # Simple single button
        self.button_run_phase = Button(self, "Run Phase")
        self.text_box = TextBox(self, [], (0, 0))
        self.components.add(self.button_run_phase)
        self.components.add(self.text_box)

        # Basic fonts for text
        self.tfont = pygame.font.SysFont(None, 14)
        self.font = pygame.font.SysFont(None, 24)
        self.big_font = pygame.font.SysFont(None, 32)

    def draw(self, surface):
        """Draw the pop-up and its button if visible."""
        if not self.visible:
            return
        super().draw(surface)
        # Title
        selected = self.view.selected
        state = selected.get_state()
        text = []
        text.append(f"{selected.id}:{state}")
        if selected.wall_segment is not None:
            text.append(f"state seg:{selected.wall_segment.state}")
        self.text_box.set_text(text)
        title_text = self.big_font.render(self.title, True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(self.rect.centerx, self.rect.y + 30))
        surface.blit(title_text, title_rect)

    def handle_event(self, event, on_button_click=None):
        for c in self.components:
            c.handle_event(event, on_button_click)
        """
        Handle Pygame events.
        If the pop-up is visible and the user clicks the button, call on_button_click (if provided).

        Args:
            event (pygame.event.Event): The event to handle.
            on_button_click (Callable): Function to call when the button is clicked.
        """
        if not self.visible:
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            # Check if user clicked the button

            # If user clicks outside the pop-up, optionally hide it
            if not self.rect.collidepoint(mx, my):
                self.hide()
                self.view.selected = None
