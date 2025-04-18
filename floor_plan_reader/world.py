import logging
from collections import deque
from itertools import count

from PIL import Image

import numpy as np
import random

from floor_plan_reader.agents.agent_factory import AgentFactory
from floor_plan_reader.agents.wall_segment import WallSegment
from floor_plan_reader.id_util import IdUtil
from floor_plan_reader.model.edge import Edge
from floor_plan_reader.model.model import Model
from floor_plan_reader.model.node import Node


class World:

    def __init__(self):
        self.num_ants = 0
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
        self.model = Model()

    def has_node(self, node):
        return self.model.has_node(node)

    def create_node(self, position):
        return self.model.create_node(position)

    def add_node(self, node):
        self.model.add_node(node)

    def create_edge(self, node_a, node_b, line):
        return self.model.create_edge(node_a, node_b, line)

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

    def get_occupied_snapshot(self, x, y, width, height):
        grid = self.occupied
        return self.get_snapshot(x, y, width, height, grid, self.encode_occupied)

    def get_grid_snapwhot(self, x, y, width, height):
        grid = self.grid
        return self.get_snapshot(x, y, width, height, grid, self.encode_grid)

    def encode_grid(self, color_coded, region, width, height):
        color_coded[region == 1] = [255, 255, 255]
        center_x, center_y = width // 2, height // 2
        color_coded[center_y, center_x] = [0, 255, 0]

    def encode_occupied(self, color_coded, region, width, height):
        min_id = np.min(region)
        max_id = np.max(region)
        norm = (region - min_id) / (max_id - min_id)  # floats in [0..1]

        # Create an RGB gradient (example: from blue (0,0,255) to red (255,0,0))
        r = (norm * 255).astype(np.uint8)
        g = region % 255
        b = (255 - r).astype(np.uint8)

        # 2) Fill the color_coded array in place
        # color_coded expected shape is [H, W, 3]
        color_coded[..., 0] = r  # Red channel
        color_coded[..., 1] = g  # Green channel
        color_coded[..., 2] = b  # Blue channel

    def get_nodes(self):
        return self.model.get_nodes()

    def get_edges(self):
        return self.model.get_edges()

    def get_clampt_region(self, x, y, width, height, grid):
        color_coded = None
        x = int(x)
        y = int(y)

        # Calculate the boundaries with clamping
        h1 = max(0, y - height // 2)
        h2 = min(grid.shape[0], y + height // 2)
        w1 = max(0, x - width // 2)
        w2 = min(grid.shape[1], x + width // 2)

        # Clamping the boundaries to ensure they are within the valid range
        if h1 >= grid.shape[0]:
            h1 = grid.shape[0] - 1
        if h2 > grid.shape[0]:
            h2 = grid.shape[0]
        if w1 >= grid.shape[1]:
            w1 = grid.shape[1] - 1
        if w2 > grid.shape[1]:
            w2 = grid.shape[1]

        # Extract the clamped region
        region = grid[h1:h2, w1:w2]
        return region

    def get_snapshot(self, x, y, width, height, grid, encode):
        color_coded = None
        region = self.get_clampt_region(x, y, width, height, grid)

        # Get the shape of the region
        shape = region.shape
        color_coded = np.zeros((shape[0], shape[1], 3), dtype=np.uint8)

        encode(color_coded, region, width, height)
        # 4) Save the extracted region as an image file
        return color_coded
        # Ensure the region is within the image boundaries

        return color_coded

    def print_occupancy_status(self, x, y, width, height, name_prefix="occupancy"):
        wall_grid = self.get_clampt_region(x, y, width, height, self.grid)
        occ = self.get_clampt_region(x, y, width, height, self.occupied)
        occ_binary = (occ > 0).astype(np.uint8)
        h, l = occ.shape
        out = np.zeros((h, l, 3), dtype=np.uint8)
        for i in range(h):
            for j in range(l):
                wall = wall_grid[i, j]
                occ = occ_binary[i, j]
                if wall == 0:
                    out[i, j] = [0, 0, 0]  # black
                elif wall == 1 and occ == 0:
                    out[i, j] = [255, 0, 0]  # red
                elif wall == 1 and occ == 1:
                    out[i, j] = [0, 255, 0]  # green

        region_image = Image.fromarray(out)
        if region_image is not None:
            name = f"debug_output\\occupancy_{name_prefix}_{width}x{height}_{x}_{y}.png"
            region_image.save(name)
            logging.info(f"{width}x{height} region saved as '{name}'")

    def print_snapshot(self, x, y, width=20, height=20, name_prefix="region"):
        x = int(x)
        y = int(y)
        # Ensure the region is within the image boundaries
        color_coded = self.get_grid_snapwhot(x, y, width, height)
        if color_coded is None:
            return
        region_image = Image.fromarray(color_coded)
        if region_image is not None:
            name = f"debug_output\\{name_prefix}_{width}x{height}_{x}_{y}.png"
            region_image.save(name)
            logging.info(f"{width}x{height} region saved as '{name}'")

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
            occupided_value = self.occupied_wall[int(y), int(x)]
            i_val = int(occupided_value)
            return i_val != 0
        return True  # Out of bounds is occupied

    def is_occupied(self, x, y):
        h, w = self.grid.shape
        if 0 <= x < w and 0 <= y < h:
            occupided_value = self.occupied[int(y), int(x)]
            i_val = int(occupided_value)
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
        if self.is_within_bounds(x, y):
            return self.occupied[int(y), int(x)]
        return 0

    def get_occupied_wall_id(self, x, y):
        if self.is_within_bounds(x, y):
            return self.occupied_wall[int(y), int(x)]
        return 0

    def collide_with_any(self, agent, x, y):
        return False
        # for a in self.blobs:
        #    if a is not agent:
        #        if a.collidepoint(x, y):
        #            return True
        # return False

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
        ws = WallSegment(IdUtil.get_id(), self)
        self.candidates.append(ws)
        self.wall_segments.add(ws)
        return ws

    def create_blob(self, x, y):
        if self.is_within_bounds(x, y):
            if not self.is_blob(x, y):
                blob = self.af.create_blob(x, y)
                self.set_blob(x, y, blob)
                self.candidates.append(blob)
                self.blobs.add(blob)
                return blob

    def create_mushroom(self, blob, x, y):
        if self.is_within_bounds(x, y):
            if not self.is_occupied(x, y):
                mush = self.af.create_mushroom(blob, x, y)
                self.occupy(x, y, mush)
                self.candidates.append(mush)
                return mush
        return None

    def get_wall(self, x, y):
        wall_id = self.get_occupied_wall_id(x, y)
        if wall_id == 0:
            return None
        for w in self.walls:
            if w.id == wall_id:
                return w
        return None

    def get_grid_value(self, x, y):
        return self.grid[y, x]

    def draw_at(self, point, value):

        x = int(point[0])
        y = int(point[1])
        if self.is_within_bounds(x, y):
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

    def is_within_bounds(self, x, y):
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
            ant = self.af.create_ant(px, py)

            self.agents.add(ant)
            self.visited[py, px] = ant.id
