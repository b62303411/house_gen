import json
import logging
from itertools import count

import pygame

from agent_manager import AgentManager
from floor_plan_reader.agents.blob import Blob
from floor_plan_reader.agents.mushroom_agent import Mushroom
from floor_plan_reader.agents.wall_segment import WallSegment
from floor_plan_reader.image_parser import ImageParser
from floor_plan_reader.intersections_solver import IntersectionSolver
from floor_plan_reader.json_writer import JsonWriter
from floor_plan_reader.display.simulation_view import SimulationView
from floor_plan_reader.world_factory import WorldFactory
from pygame import font

font.init()
f = font.Font(None, 36)  # Use default font with size 36
f_small = font.Font(None, 12)


class Simulation:
    def __init__(self):

        self._line_dic = None
        self.running = True
        self.wf = WorldFactory()
        self.agent_manager = AgentManager(self)
        self.world = None
        self.solver = None
        self.view = SimulationView(self)

        self.width = 0
        self.height = None
        self.floorplan_surf = None
        self.img_gray_surface = None
        self.img_colour_surface = None
        self._intersections = set()
        self._lines = set()
        self.jw = JsonWriter()
        self.tasks = [
            {
                "name": "Save Blue Print",
                "interval": 5000,  # 1 second
                "accumulator": 0,
                "command": self.save_blue_print
            }
        ]

    def get_intersections(self):
        return self._intersections

    def save_blue_print(self):
        result = self.solver.build_lines_and_intersections(self.world.wall_segments)
        self._intersections = result.get("intersections")
        self._lines = result.get("lines")
        self._line_dic = {}
        for l in self._lines:
            self._line_dic[l.id] = l
            l.seg.calculate_openings()
        for i in self._intersections:
            (ix, iy) = i.point
            blob = self.world.get_blob(ix, iy)
            if blob is not None:
                blob.add_intersection(i)
        model = self.world.model
        scaled_model = model.convert_to_scale(0.028)
        nodes = list(model.get_nodes())
        edges = list(model.get_edges())
        for e in edges:
            e.calculate_opening()
        data = {
            "nodes": nodes,
            "edges": edges
        }

        if len(edges) > 10:
            self.jw.build_floorplan_json(data, self.world.walls)

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
        self.agent_manager.run()

    def init_world(self, image):
        img_gray = image.get_black_and_white()
        self.wf.set_grid(img_gray)
        self.world = self.wf.create_World()
        self.solver = IntersectionSolver(self.world)
        self.height, self.width = self.world.grid.shape
        self.floorplan_surf = pygame.Surface((self.width, self.height))
        if image.img_colour is not None:
            img_colour = image.img_colour
            self.img_colour_surface = pygame.surfarray.make_surface(img_colour.swapaxes(0, 1))
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
        img_scanner = ImageParser()
        img_scanner.init(image_path, threshold)
        # 1) Load grayscale
        self.init_world(img_scanner)
        self.world.init_ants()

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
            dt = clock.tick(120)  # up to 30 FPS

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
