import pygame


class PopupMenu:
    def __init__(self,simulation ,x, y, width, height, title="Action Menu"):
        self.simulation=simulation
        """
        A simple pop-up menu overlay with a single button.

        Args:
            x, y (int): Top-left position of the pop-up.
            width, height (int): Dimensions of the pop-up.
            title (str): Optional title text displayed at the top.
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.visible = False
        self.title = title

        # Simple single button
        btn_w, btn_h = 100, 40
        self.button_rect = pygame.Rect(
            x + (width - btn_w) // 2,
            y + height - btn_h - 10,  # near bottom
            btn_w,
            btn_h
        )

        # Basic fonts for text
        self.tfont = pygame.font.SysFont(None, 14)
        self.font = pygame.font.SysFont(None, 24)
        self.big_font = pygame.font.SysFont(None, 32)

    def show(self):
        """Show the pop-up."""
        self.visible = True
        print("view")

    def hide(self):
        """Hide the pop-up."""
        self.visible = False

    def draw_vertical_text(self,surface,  lines, color=(255,255,255), vertical_spacing=30):
        center_x ,start_y=self.rect.centerx, self.rect.y +50
        for i, text_str in enumerate(lines):
            text_surface = self.tfont.render(text_str, True, color)
            text_rect = text_surface.get_rect(center=(center_x, start_y + i * vertical_spacing))
            surface.blit(text_surface, text_rect)

    def draw(self, surface):
        """Draw the pop-up and its button if visible."""
        if not self.visible:
            return

        # Pop-up background + border
        pygame.draw.rect(surface, (50, 50, 50), self.rect)
        pygame.draw.rect(surface, (255, 255, 255), self.rect, 2)

        # Title
        selected= self.simulation.selected
        state = selected.state
        text = []
        text.append(f"{selected.id}:{state}")
        if selected.wall_segment is not None:
            text.append(f"state seg:{selected.wall_segment.state}")


        title_text = self.big_font.render(self.title, True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(self.rect.centerx, self.rect.y + 30))
        surface.blit(title_text, title_rect)

        # Button
        pygame.draw.rect(surface, (100, 100, 200), self.button_rect)
        pygame.draw.rect(surface, (255, 255, 255), self.button_rect, 2)
        #print("view")
        label_text = self.font.render("Run Phase", True, (255, 255, 255))
        label_rect = label_text.get_rect(center=self.button_rect.center)
        surface.blit(label_text, label_rect)
        self.draw_vertical_text(surface, text)

    def handle_event(self, event, on_button_click=None):
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
            if self.button_rect.collidepoint(mx, my) and on_button_click:
                on_button_click()
            else:
                # If user clicks outside the pop-up, optionally hide it
                if not self.rect.collidepoint(mx, my):
                    self.hide()
                    self.simulation.selected=None
