import logging
from collections import deque
from PIL import Image

import numpy as np
import random

from floor_plan_reader.agents.agent_factory import AgentFactory
from floor_plan_reader.agents.ants import Ant
from floor_plan_reader.agents.blob import Blob
from floor_plan_reader.id_util import Id_Util
from floor_plan_reader.node import Node
from floor_plan_reader.agents.wall_segment import WallSegment


class World:

    def __init__(self):
        self.af = AgentFactory(self)
        self.grid = None
        self.blob_grid = None
        self.occupied_wall = None
        self.visited = None
        self.candidates = deque()

        self.occupied = None
        self.walls = set()
        self.agents = set()
        self.wall_segments = set()
        self.zombies = []
        self.blobs = set()
        self.nodes = {}

    def has_node(self, node):
        return node.getHash() in self.nodes.keys()

    def create_node(self, position):
        x = position[0]
        y = position[1]
        xi = int(x)
        yi = int(y)
        hash_ = hash((xi, yi))
        if hash_ in self.nodes.keys():
            return self.nodes.get(hash_)
        else:
            n = Node((x, y))
            self.add_node(n)
            return n

    def add_node(self, node):
        self.nodes[node.getHash()] = node

    def get_neighbors_8(self, x, y):
        """Returns all 8 neighboring coordinates."""
        neighbors = [(x + dx, y + dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if (dx, dy) != (0, 0)]
        return [(nx, ny) for nx, ny in neighbors if
                0 <= nx < self.grid.shape[1] and 0 <= ny < self.grid.shape[0]]

    def set_grid(self, grid):
        self.grid = grid
        self.occupied = np.zeros(self.grid.shape, dtype=np.uint64)
        self.blob_grid = np.zeros(self.grid.shape, dtype=np.uint64)
        self.occupied_wall = np.zeros(self.grid.shape, dtype=np.uint64)

    def print_snapshot(self, x, y, width=20, height=20, name_prefix="region"):
        x = int(x)
        y = int(y)
        grid = self.grid
        # Ensure the region is within the image boundaries
        if x - width // 2 >= 0 and x + width // 2 <= grid.shape[1] and \
                y - height // 2 >= 0 and y + height // 2 <= grid.shape[0]:
            # Extract the 10x10 region
            height = int(height)
            width = int(width)
            h1 = int(y - height // 2)
            h2 = int(y + height // 2)
            w1 = int(x - width // 2)
            w2 = int(x + width // 2)
            region = grid[h1:h2, w1:w2]
            shape = region.shape
            color_coded = np.zeros((shape[0], shape[1], 3), dtype=np.uint8)
            color_coded[region == 1] = [255, 255, 255]
            center_x, center_y = width // 2, height // 2
            color_coded[center_y, center_x] = [0, 255, 0]
            # 4) Save the extracted region as an image file
            region_image = Image.fromarray(color_coded)
            name = f"{name_prefix}_{width}x{height}_{x}_{y}.png"
            region_image.save(name)
            logging.info(f"{width}x{height} region saved as '{name}'")
        else:
            logging.info("The region is out of bounds.")

    def free(self, x, y):
        self.occupied[int(y), int(x)] = 0

    def is_any_occupied(self, x, y):
        h, w = self.grid.shape
        y, x = int(y), int(x)
        if 0 <= x < w and 0 <= y < h:
            wall_part_occupied = self.occupied[y, x] != 0
            wall_occupied = self.occupied_wall[y, x] != 0
            return wall_occupied or wall_part_occupied
        return True  # Out of bounds is occupied

    def is_wall_occupied(self, x, y):
        h, w = self.grid.shape
        if 0 <= x < w and 0 <= y < h:
            occupied_value = self.occupied_wall[int(y), int(x)]
            i_val = int(occupied_value)
            return i_val != 0
        return True  # Out of bounds is occupied

    def is_occupied(self, x, y):
        h, w = self.grid.shape
        if 0 <= x < w and 0 <= y < h:
            occupied_value = self.occupied[int(y), int(x)]
            i_val = int(occupied_value)
            return i_val != 0
        return True  # Out of bounds is occupied

    def get_shape(self):
        return self.grid.shape

    def occupy(self, x, y, mush):
        h, l = self.get_shape()
        h, l = self.occupied.shape
        if int(y) >= h or int(x) >= l:
            return

        self.occupied[int(y), int(x)] = mush.id

    def get_obj_by_id(self, id):
        for a in self.agents:
            if a.id == id:
                return a
        return None

    def get_occupied_id(self, x, y):
        return self.occupied[int(y), int(x)]

    def collide_with_any(self, agent, x, y):
        for a in self.walls:
            if a is not agent:
                if a.collidepoint(x, y):
                    return True
        return False

    def occupy_wall(self, x, y, wall):
        h, l = self.occupied.shape
        x, y = int(x), int(y)
        if y >= h or x >= l:
            return
        self.occupied_wall[y, x] = wall.id

    def find_all(self, type):
        results = []
        for a in self.agents:
            if isinstance(a, type):
                results.append(a)
        return results

    def create_wall_segment(self):
        ws = WallSegment(Id_Util.get_id(), self)
        self.candidates.append(ws)
        self.wall_segments.add(ws)
        return ws

    def create_blob(self, x, y):
        if self.is_within_bounds(x, y):
            if not self.is_blob(x, y):
                blob = self.af.create_blob(x, y)
                self.set_blob(x, y, blob)
                self.agents.add(blob)
                self.blobs.add(blob)
                return blob

    def create_mushroom(self, blob: Blob, x: int, y: int):
        if self.is_within_bounds(x, y):
            if not self.is_occupied(x, y):
                mush = self.af.create_mushroom(blob, x, y)
                self.occupy(x, y, mush)
                self.candidates.append(mush)
                return mush
        return None

    def get_grid_value(self, x, y):
        return self.grid[y, x]

    def draw_at(self, point, value):
        x = int(point[0])
        y = int(point[1])
        self.grid[y, x] = value

    def is_food_at(self, location):
        return self.is_food(int(location[0]), int(location[1]))

    def get_blob(self, x, y):
        id = self.blob_grid[int(y), int(x)]
        for b in self.blobs:
            if b.id == id:
                return b
        return None

    def is_blob(self, x, y):
        if self.is_within_bounds(x, y):
            food = (self.blob_grid[int(y), int(x)] != 0)
            return food
        return False

    def set_blob(self, x, y, blob):
        if self.is_within_bounds(x, y):
            self.blob_grid[int(y), int(x)] = blob.id

    def is_food(self, x, y):
        """
        Return True if (x, y) is within bounds and is food (grid == 1),
        otherwise False.
        """

        if self.is_within_bounds(x, y):
            value = self.grid[int(y), int(x)]
            food = (value == 1)
            return food
        return False

    def is_within_bounds(self, x: int, y: int):
        h, w = self.grid.shape
        return 0 <= x < w and 0 <= y < h

    def init_ants(self):
        # 6) Spawn ants at random empty locations
        empty_pixels = np.argwhere(self.grid == 0)
        if len(empty_pixels) == 0:
            logging.info("No empty space found!")
            return

        chosen_indices = random.sample(range(len(empty_pixels)), min(self.num_ants, len(empty_pixels)))

        for i, idx in enumerate(chosen_indices):
            py, px = empty_pixels[idx]
            ant = Ant(px, py, i + 1, self)
            self.agents.add(ant)
            self.visited[py, px] = ant.id
