from collections import deque

import numpy as np
import random

from agent_factory import AgentFactory
from ants import Ant


class World:

    def __init__(self):
        self.af = AgentFactory()
        self.grid = None
        self.visited = None
        self.candidates = deque()
        self.offset_x = 0
        self.offset_y = 0
        self.zoom_factor = 1
        self.occupied = None

    def get_neighbors_8(self, x, y):
        """Returns all 8 neighboring coordinates."""
        neighbors = [(x + dx, y + dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if (dx, dy) != (0, 0)]
        return [(nx, ny) for nx, ny in neighbors if
                0 <= nx < self.grid.shape[1] and 0 <= ny < self.grid.shape[0]]

    def set_grid(self, grid):
        self.grid = grid
        self.occupied = np.zeros(self.grid.shape, dtype=np.uint64)

    def is_occupied(self, x, y):
        h, w = self.grid.shape
        if 0 <= x < w and 0 <= y < h:
            return self.occupied[int(y), int(x)] != 0
        return True  # Out of bounds is occupied

    def occupy(self, x, y, mush):
        self.occupied[int(y), int(x)] = mush.id

    def convert_coordinates(self, x, y):
        scaled_x = int((self.x + self.offset_x) * self.zoom_factor)
        scaled_y = int((self.y + self.offset_y) * self.zoom_factor)
        return scaled_x, scaled_y

    def collide_with_any(self, agent, x, y):
        for a in self.agents:
            if a is not agent:
                if a.collidepoint(x, y):
                    return True
        return False

    def find_all(self, type):
        results = []
        for a in self.agents:
            if isinstance(a, type):
                results.append(a)
        return results

    def create_mushroom(self, x, y):
        mush = self.af.create_mushroom(self, x, y)
        self.agents.append(mush)
        pass

    def get_grid_value(self, x, y):
        return self.grid[y, x]

    def is_food_at(self, location):
        return self.is_food(int(location[0]), int(location[1]))

    def is_food(self, x, y):
        """
        Return True if (x, y) is within bounds and is food (grid == 1),
        otherwise False.
        """

        if self.is_within_bounds(x,y):
            food = (self.grid[int(y), int(x)] == 1)
            return food
        return False
    def is_within_bounds(self,x,y):
        h, w = self.grid.shape
        return 0 <= x < w and 0 <= y < h
    def init_ants(self):
        # 6) Spawn ants at random empty locations
        empty_pixels = np.argwhere(self.grid == 0)
        if len(empty_pixels) == 0:
            print("No empty space found!")
            return

        chosen_indices = random.sample(range(len(empty_pixels)), min(self.num_ants, len(empty_pixels)))
        self.agents = []
        for i, idx in enumerate(chosen_indices):
            py, px = empty_pixels[idx]
            ant = Ant(px, py, i + 1, self)
            self.agents.append(ant)
            self.visited[py, px] = ant.id
