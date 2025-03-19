import json
from collections import deque

import cv2
import numpy as np
import pygame

from floor_plan_reader.mushroom_agent import Mushroom
from floor_plan_reader.popup_menu import PopupMenu
from floor_plan_reader.world_factory import WorldFactory
from pygame import font
font.init()
f = font.Font(None, 36)  # Use default font with size 36
class ViewPoint:
    def __init__(self):
        self.offset_x = 0
        self.offset_y = 0
        self.zoom_factor=1
        self.min_zoom = 0.1  # Don’t let it go below 10%
        self.max_zoom = 5.0  # Don’t let it exceed 500%
        self.zoom_speed = 1.1

    def zoom_in(self):
        self.zoom_factor *= self.zoom_speed
        if self.zoom_factor > self.max_zoom:
            self.zoom_factor = self.max_zoom

    def zoom_out(self):
        self.zoom_factor /= self.zoom_speed
        if self.zoom_factor < self.min_zoom:
            self.zoom_factor = self.min_zoom

    def move_left(self, move_speed):
        self.offset_x -= move_speed

    def move_right(self, move_speed):
        self.offset_x += move_speed

    def convert(self, x, y):
        x = int((x + self.offset_x) * self.zoom_factor)
        y = int((y + self.offset_y) * self.zoom_factor)
        return x, y

    def convert_back(self, screen_x, screen_y):
        """
        Convert from screen coordinates back to map coordinates.
        """
        # Inverse of: (x + offset_x) * zoom_factor
        x_map = screen_x / self.zoom_factor - self.offset_x
        y_map = screen_y / self.zoom_factor - self.offset_y
        return x_map, y_map

    def get_center(self):
        return self.offset_x * self.zoom_factor, self.offset_y * self.zoom_factor



class Simulation:
    def __init__(self):
        self.popup = PopupMenu(self,300, 200, 200, 150, title="Actions")
        self.wf = WorldFactory()
        self.zombie_candidates = []
        self.world = None
        self.selected = None
        self.selections = set()
        self.mouse_actions = deque()
    def is_wall(self,a,mx,my):
        if isinstance(a, Mushroom):
            if a.is_valid():
                pass
            if a.is_valid() and a.collidepoint(mx, my):
                print(a.id)
                selection_candidate = a
                a.set_selected(True)
                return True
        return False

    def save_boxes_to_json(self,boxes, filename):
        """
        Serialize a list of CollisionBox objects to a JSON file.
        """
        # Convert each CollisionBox to a dict
        data = [box.to_dict() for box in boxes]

        # Write the list of dicts to a JSON file
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)
    def handle_visible_pupup(self):
        popup = self.popup
        if self.selected is None and popup.visible:
            # If user clicked empty space, deselect
            popup.hide()
        elif not popup.visible and self.selected is not None:
            #print("?===============================?")
            print(f"selected:{ self.selected.id}")
            popup.show()
            #self.selected = selection_candidate

    def evaluate_selected(self, mx, my):
        selection_candidate = None
        shallow = self.world.walls.copy()
        for a in shallow:
            if self.is_wall(a, mx, my):
                selection_candidate = a
                break
        self.selected = selection_candidate
        self.selections.add(selection_candidate)


    def execute_on_selected(self):
        boxes = []
        for c in self.selections:
            #if not self.selected.is_on_same_axis_as(c):
            boxes.append(c.collision_box)

        self.save_boxes_to_json(boxes,"test.json")
        self.selected.crawl_phase()
    def run_ant_simulation(self,
            image_path,
            image_path_filtered,
            threshold=200,  # if pixel >= threshold => empty, else wall
            num_ants=20,
            allow_revisit=False
    ):
        # 1) Load grayscale
        img_gray = cv2.imread(image_path_filtered, cv2.IMREAD_GRAYSCALE)
        img_colour = cv2.imread(image_path)

        if img_gray is None:
            raise FileNotFoundError(f"Cannot load image: {image_path}")

        #img_gray_rgb = cv2.cvtColor(img_colour, cv2.COLOR_GRAY2RGB)
        img_gray_surface = pygame.surfarray.make_surface(img_colour.swapaxes(0, 1))
        # 2) Create grid: 1=empty, 0=wall
        g = (img_gray >= threshold).astype(np.uint8)
        self.wf.set_grid(g)
        self.wf.set_num_ants(num_ants)
        self.world = self.wf.create_World()
        height, width = self.world.grid.shape

        # 3) Init Pygame with the *exact* dimensions as the image
        pygame.init()
        # We make a window exactly the size of the image
        screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        pygame.display.set_caption("Ant Demo (Native Resolution + Zoom)")

        clock = pygame.time.Clock()

        # 4) Create a floorplan surface (the base image showing white/black)
        #    Then we won't re-scale it right away; we'll do that each frame based on zoom.
        floorplan_surf = pygame.Surface((width, height))
        for y in range(height):
            for x in range(width):
                if self.world.grid[y, x] == 1:
                    floorplan_surf.set_at((x, y), (255, 255, 255))  # white => empty
                else:
                    floorplan_surf.set_at((x, y), (0, 0, 0))  # black => wall

        # 7) Zoom parameters
        vp = ViewPoint()


        move_speed = 10

        running = True
        while running:
            clock.tick(120)  # up to 30 FPS

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
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
                    if self.popup.visible:
                        self.popup.handle_event(
                            event,
                            on_button_click=lambda: self.execute_on_selected()
                        )
                    else:
                        # Otherwise, handle normal events (e.g., box selection)
                        if event.type == pygame.MOUSEBUTTONDOWN:
                            mx, my = event.pos
                            print(f"x:{mx} y:{my}")
                            mx,my = vp.convert_back(mx,my)
                            print(f"x:{mx} y:{my}")
                            self.mouse_actions.append((mx,my))



            # --- Update ants (simple example) ---
            agents = self.world.agents.copy()
            for agent in agents:
                if agent.alive:
                    agent.run()
                else:
                    self.zombie_candidates.append(agent)
            for zombie in self.zombie_candidates:
                if zombie in self.world.agents:
                    self.world.agents.remove(zombie)
                if zombie in self.world.walls:
                    self.world.walls.remove(zombie)

                # else: no moves => ant stays put
            if not len(self.world.candidates) == 0:
                agent = self.world.candidates.popleft()
                if isinstance(agent, Mushroom):
                    self.world.walls.add(agent)
                self.world.agents.add(agent)

            if not len(self.mouse_actions) == 0:
                x,y = self.mouse_actions.pop()
                self.evaluate_selected(x,y)
            # --- Draw ---
            screen.fill((50, 50, 50))

            # Scale the floorplan based on zoom_factor
            new_w = int(width * vp.zoom_factor)
            new_h = int(height * vp.zoom_factor)
            floorplan_scaled = pygame.transform.smoothscale(floorplan_surf, (new_w, new_h))
            img = pygame.transform.smoothscale(img_gray_surface, (new_w, new_h))

            # Blit the scaled floorplan at (0,0)
            #screen.blit(floorplan_scaled, vp.get_center())
            screen.blit(img, vp.get_center())
            # Draw ants (scaled)
            for agent in self.world.agents:
                if agent.alive:
                    agent.draw(screen, vp)
            # Render the number of agents in the top-left corner
            text_surface = f.render(f"Agents: {len(self.world.agents)}", True, (255, 255, 0))
            screen.blit(text_surface, (10, 10))  # Position (x=10, y=10)

            self.handle_visible_pupup()
            # Draw the pop-up
            self.popup.draw(screen)

            pygame.display.flip()

        pygame.quit()
        print("All done!")


