import logging
from collections import deque

import pygame

from floor_plan_reader.display.intersection import Intersection
from floor_plan_reader.display.popup_menu import PopupMenu
from floor_plan_reader.display.status_window import StatusWindow
from floor_plan_reader.display.user_input import UserInput
from floor_plan_reader.display.view_point import ViewPoint


class SimulationView:
    def __init__(self,simulation):
        self.selected = None
        self.popup = PopupMenu(self, 300, 200, 200, 350, title="Actions")
        self.sw = StatusWindow(simulation, 10, 10, 100, 100)
        self.vp = ViewPoint()
        self.user_input = UserInput(self)
        self.screen = None
        self.simulation=simulation
        self.selected = None
        self.selections = set()
        self.mouse_actions = deque()

    def init(self):
        self.screen = pygame.display.set_mode((self.simulation.width, self.simulation.height), pygame.RESIZABLE)
        pygame.display.set_caption("Ant Demo (Native Resolution + Zoom)")

    def stop(self):
        self.simulation.stop()
        
    def get_width(self):
        return self.simulation.width

    def get_height(self):
        return self.simulation.height

    def handle_visible_pupup(self):
        popup = self.popup
        if self.selected is None and popup.visible:
            # If user clicked empty space, deselect
            popup.hide()
        elif not popup.visible and self.selected is not None:
            # print("?===============================?")
            logging.debug(f"selected:{self.selected.id}")
            popup.show()
            # self.selected = selection_candidate

    def get_walls(self):
        return self.simulation.world.walls.copy()

    def execute_on_selected(self):
        boxes = []
        # create_box_image

        for c in self.selections:
            # if not self.selected.is_on_same_axis_as(c):
            boxes.append(c.collision_box)

        self.simulation.save_boxes_to_json(boxes, "test.json")
        self.selected.crawl_phase()
        self.selected.print_box()

    def run_blob(self):
        blob = self.selected.blob
        blob.print_blob()

    def evaluate_selected(self, mx, my):
        selection_candidate = None
        shallow = self.get_walls()
        for a in shallow:
            if self.simulation.is_wall(a, mx, my):
                selection_candidate = a
                break
        self.selected = selection_candidate
        if selection_candidate is not None:
            self.selections.add(selection_candidate)

    def run(self):
        self.user_input.run()
        if not len(self.mouse_actions) == 0:
            x, y = self.mouse_actions.pop()
            self.evaluate_selected(x, y)
    def draw(self):
        # --- Draw ---
        self.screen.fill((250, 250, 250))
        width = self.get_width()
        height = self.get_height()
        # Scale the floorplan based on zoom_factor
        new_w = int(width * self.vp.zoom_factor)
        new_h = int(height * self.vp.zoom_factor)
        #floorplan_scaled = pygame.transform.smoothscale(self.simulation.floorplan_surf, (new_w, new_h))
        img = pygame.transform.smoothscale(self.simulation.img_colour_surface, (new_w, new_h))

        # Blit the scaled floorplan at (0,0)
        # screen.blit(floorplan_scaled, vp.get_center())
        self.screen.blit(img, self.vp.get_center())
        # Draw ants (scaled)
        for agent in self.simulation.world.agents:
            if agent.alive:
                agent.draw(self.screen, self.vp)
        # Render the number of agents in the top-left corner

        self.sw.draw(self.screen)

        self.handle_visible_pupup()
        # Draw the pop-up
        self.popup.draw(self.screen)
        i = Intersection(self.simulation)
        i.draw(self.screen, self.vp)
        pygame.display.flip()
