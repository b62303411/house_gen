import numpy as np

from world import World


class WorldFactory:
    def __init__(self):
        self.grid = None
        self.grid_size = None
        self.num_ants = 1

    def set_num_ants(self, num_ants):
        self.num_ants = num_ants

    def set_grid(self, grid):
        self.grid = grid
        self.grid_size = self.grid.shape

    def create_World(self):
        world = World()
        world.set_grid(self.grid)
        world.visited = np.zeros(self.grid_size, dtype=np.int32)
        world.num_ants = self.num_ants
        world.init_ants()
        return world
