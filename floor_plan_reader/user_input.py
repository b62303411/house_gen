import logging

import pygame


class UserInput:
    def __init__(self,simulation):
        self.simulation=simulation
        self.move_speed = 10
    def stop(self):
        self.simulation.running = False
    def run(self):
        vp  = self.simulation.vp
        move_speed = self.move_speed
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.stop()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.stop()
                elif event.key == pygame.K_LEFT:  # Move left
                    vp.move_left(move_speed)
                elif event.key == pygame.K_RIGHT:  # Move right
                    vp.move_right(move_speed)
                elif event.key == pygame.K_UP:  # Move up
                    vp.offset_y -= move_speed
                elif event.key == pygame.K_DOWN:  # Move down
                    vp.offset_y += move_speed
            elif event.type == pygame.VIDEORESIZE:
                # If the user resizes the window, we can catch the new size here if needed.
                # screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                pass
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Mouse wheel up => event.button = 4
                # Mouse wheel down => event.button = 5
                if event.button == 4:  # scroll up => zoom in
                    vp.zoom_in()
                elif event.button == 5:  # scroll down => zoom out
                    vp.zoom_out()
                if self.simulation.popup.visible:
                    self.simulation.popup.handle_event(
                        event,
                        on_button_click=lambda: self.simulation.execute_on_selected()
                    )
                else:
                    # Otherwise, handle normal events (e.g., box selection)
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        mx, my = event.pos
                        logging.debug(f"x:{mx} y:{my}")
                        mx, my = vp.convert_back(mx, my)
                        logging.debug(f"x:{mx} y:{my}")
                        self.simulation.mouse_actions.append((mx, my))
