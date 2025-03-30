import cv2
import numpy as np
import pygame

from floor_plan_reader.world import World


class WorldFactory:
    def __init__(self):
        self.grid = None
        self.grid_size = None
        self.num_ants = 1

    def set_img(self,img_path,threshold=5):
        # 1) Load grayscale
        img_gray = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        if img_gray is None:
            raise FileNotFoundError(f"Cannot load image: {img_path}")
        g = (img_gray >= threshold).astype(np.uint8)
        self.set_grid(g)
    def set_num_ants(self, num_ants):
        self.num_ants = num_ants

    def set_grid(self, grid):
        self.grid = grid
        self.grid_size = self.grid.shape

    def create_World(self):
        world = World()
        world.set_grid(self.grid)
        world.visited = np.zeros(self.grid_size, dtype=np.int32)

        return world


