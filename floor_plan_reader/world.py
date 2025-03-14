from collections import deque

import numpy as np
import random

from floor_plan_reader.agent_factory import AgentFactory
from floor_plan_reader.ants import Ant


class World:

    def __init__(self):
        self.af = AgentFactory()
        self.grid = None
        self.visited = None
        self.candidates = deque()

        self.occupied = None
        self.walls = set()
        self.agents = []
        self.zombies = []

    def get_neighbors_8(self, x, y):
        """Returns all 8 neighboring coordinates."""
        neighbors = [(x + dx, y + dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if (dx, dy) != (0, 0)]
        return [(nx, ny) for nx, ny in neighbors if
                0 <= nx < self.grid.shape[1] and 0 <= ny < self.grid.shape[0]]

    def set_grid(self, grid):
        self.grid = grid
        self.occupied = np.zeros(self.grid.shape, dtype=np.uint64)

    def free(self,x,y):
        self.occupied[int(y), int(x)] =0
    def is_occupied(self, x, y):
        h, w = self.grid.shape
        if 0 <= x < w and 0 <= y < h:
            return self.occupied[int(y), int(x)] != 0
        return True  # Out of bounds is occupied
    def get_shape(self):
        return self.grid.shape
    def occupy(self, x, y, mush):
        h, l = self.get_shape()
        h, l = self.occupied.shape
        if int(y) >= h or int(x) >= l:
            return

        self.occupied[int(y), int(x)] = mush.id

    def get_obj_by_id(self,id):
        for a in self.agents:
            if a.id == id:
                return a
        return None

    def get_occupied_id(self,x,y):
        return self.occupied[int(y),int(x)]

    def collide_with_any(self, agent, x, y):
        for a in self.walls:
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
        if self.is_within_bounds(x,y):
            if not self.is_occupied(x,y):
                mush = self.af.create_mushroom(self, x, y)
                self.occupy(x,y,mush)
                self.candidates.append(mush)
                return mush
        return None

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

        for i, idx in enumerate(chosen_indices):
            py, px = empty_pixels[idx]
            ant = Ant(px, py, i + 1, self)
            self.agents.append(ant)
            self.visited[py, px] = ant.id
