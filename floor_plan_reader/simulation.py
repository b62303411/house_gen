import json
import logging
from collections import deque

import cv2
import numpy as np
import pygame

from floor_plan_reader.agents.ant_mushroom import Mushroom
from floor_plan_reader.agents.wall_segment import WallSegment
from floor_plan_reader.intersections_solver import IntersectionSolver
from floor_plan_reader.json_writer import JsonWriter
from floor_plan_reader.simulation_view import SimulationView
from floor_plan_reader.world_factory import WorldFactory
from pygame import font

font.init()
f = font.Font(None, 36)  # Use default font with size 36
f_small = font.Font(None, 12)





class Simulation:
    def __init__(self):

        self.running = True
        self.wf = WorldFactory()
        self.zombie_candidates = []
        self.world = None
        self.solver = None
        self.view = SimulationView(self)

        self.width = 0
        self.height = None
        self.floorplan_surf = None
        self.img_gray_surface = None
        self.intersections = set()
        self.jw = JsonWriter()
        self.tasks = [
            {
                "name": "Save Blue Print",
                "interval": 5000,  # 1 second
                "accumulator": 0,
                "command": self.save_blue_print
            }
        ]

    def save_blue_print(self):
        result = self.solver.build_lines_and_intersections(self.world.wall_segments)
        self.intersections = result.get("intersections")

        self.jw.build_floorplan_json(result, self.world.walls)

    def get_blob_count(self):
        return len(self.world.blobs)
    def is_wall(self, a, mx, my):
        if isinstance(a, Mushroom):
            if a.is_valid():
                pass
            if a.is_valid() and a.collidepoint(mx, my):
                logging.debug(a.id)
                selection_candidate = a
                a.set_selected(True)
                return True
        return False

    def save_boxes_to_json(self, boxes, filename):
        """
        Serialize a list of CollisionBox objects to a JSON file.
        """
        # Convert each CollisionBox to a dict
        data = [box.to_dict() for box in boxes]

        # Write the list of dicts to a JSON file
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)


    def get_agent_count(self):
        return len(self.world.agents)

    def get_wall_segment_count(self):
        return len(self.world.wall_segments)


    def run(self):
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
            if zombie in self.world.blobs:
                self.world.blobs.remove(zombie)
            if zombie in self.world.wall_segments:
                self.world.wall_segments.remove(zombie)

            # else: no moves => ant stays put
        if not len(self.world.candidates) == 0:
            agent = self.world.candidates.popleft()
            if isinstance(agent, Mushroom):
                self.world.walls.add(agent)
            if isinstance(agent, WallSegment):
                self.world.wall_segments.add(agent)
            self.world.agents.add(agent)


    def init_world(self,image):
        img_gray = image.get_black_and_white()
        self.wf.set_grid(img_gray)
        self.world = self.wf.create_World()
        self.solver = IntersectionSolver(self.world)
        self.height, self.width = self.world.grid.shape
        self.floorplan_surf = pygame.Surface((self.width, self.height))
        for y in range(self.height):
            for x in range(self.width):
                if self.world.grid[y, x] == 1:
                    self.floorplan_surf.set_at((x, y), (255, 255, 255))  # white => empty
                else:
                    self.floorplan_surf.set_at((x, y), (0, 0, 0))  # black => wall

    def stop(self):
        self.running = False

    def run_ant_simulation(self,
                           image_path,
                           image_path_filtered,
                           threshold=200,  # if pixel >= threshold => empty, else wall
                           num_ants=20,
                           allow_revisit=False
                           ):
        self.wf.set_num_ants(num_ants)
        # 1) Load grayscale
        self.init_world(image_path)

        # 3) Init Pygame with the *exact* dimensions as the image
        pygame.init()
        # We make a window exactly the size of the image
        self.view.init()

        clock = pygame.time.Clock()

        # 4) Create a floorplan surface (the base image showing white/black)
        #    Then we won't re-scale it right away; we'll do that each frame based on zoom.
        self.floorplan_surf = pygame.Surface((self.width, self.height))
        for y in range(self.height):
            for x in range(self.width):
                if self.world.grid[y, x] == 1:
                    self.floorplan_surf.set_at((x, y), (255, 255, 255))  # white => empty
                else:
                    self.floorplan_surf.set_at((x, y), (0, 0, 0))  # black => wall

        # 7) Zoom parameters
        self.running = True
        while self.running:
            dt=clock.tick(120)  # up to 30 FPS

            # --- Update ants (simple example) ---
            self.run()
            self.view.run()

            self.view.draw()
            for task in self.tasks:
                task["accumulator"] += dt
                if task["accumulator"] >= task["interval"]:
                    task["command"]()
                    task["accumulator"] = 0
        pygame.quit()
        print("All done!")
