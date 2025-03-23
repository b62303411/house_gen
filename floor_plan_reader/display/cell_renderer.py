import numpy as np
import pygame


class CellRenderer:
    def __int__(self):
        pass



    def generate_image(self,cells):
        min_x = min(cell.x for cell in cells)
        max_x = max(cell.x for cell in cells)
        min_y = min(cell.y for cell in cells)
        max_y = max(cell.y for cell in cells)

        width = (max_x - min_x) + 1
        height = (max_y - min_y) + 1

        grid = [[(0, 0, 0, 0) for _ in range(width)] for _ in range(height)]

        for cell in cells:
            grid[cell.y - min_y][cell.x - min_x] = cell.rgba

        rgba_array = np.array(grid, dtype=np.uint8)

        self.world_surface = pygame.surfarray.make_surface(rgba_array)

        return self.world_surface