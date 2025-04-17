import copy
import math

import cv2
import numpy as np
import pygame
from matplotlib import pyplot as plt

pygame.font.init()



class DrawUtil:
    def __init__(self):
        self.font = pygame.font.SysFont(None, 24)

    def preview_polygons(self, polygons, image_shape):
        blank = np.zeros(image_shape, dtype=np.uint8)

        for poly in polygons:
            simplified = poly.simplify(tolerance=1.5, preserve_topology=True)
            pts = np.array(simplified.exterior.coords, np.int32).reshape((-1, 1, 2))
            cv2.polylines(blank, [pts], isClosed=True, color=255, thickness=1)
            pts = np.array(poly.exterior.coords, np.int32).reshape((-1, 1, 2))
            cv2.polylines(blank, [pts], isClosed=True, color=255, thickness=1)
            edges = list(poly.exterior.coords)
            segments = [(edges[i], edges[i + 1]) for i in range(len(edges) - 1)]

        plt.imshow(blank, cmap="gray")
        plt.title("Detected Wall Polygons")
        plt.axis("off")
        plt.show()


    def draw_wall_rectangles_pygame(self, polygons, base_polygon=None, image_shape=(800, 800), bg_color=(30, 30, 30),
                                    wall_color=(100, 200, 255)):
        pygame.init()
        screen = pygame.display.set_mode((image_shape[1], image_shape[0]))  # shape is (rows, cols) = (h, w)
        pygame.display.set_caption("Wall Rectangle Viewer")

        def to_screen_coords(pt, scale=1.0, offset=(0, 0)):
            return int(pt[0] * scale + offset[0]), int(pt[1] * scale + offset[1])

        all_x = [pt[0] for poly in polygons for pt in poly.exterior.coords]
        all_y = [pt[1] for poly in polygons for pt in poly.exterior.coords]

        if base_polygon:
            all_x += [pt[0] for pt in base_polygon.exterior.coords]
            all_y += [pt[1] for pt in base_polygon.exterior.coords]

        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)

        padding = 20
        scale_x = (image_shape[1] - 2 * padding) / (max_x - min_x + 1e-5)
        scale_y = (image_shape[0] - 2 * padding) / (max_y - min_y + 1e-5)
        scale = min(scale_x, scale_y)
        offset = (padding - min_x * scale, padding - min_y * scale)

        running = True
        while running:
            screen.fill(bg_color)

            # Draw wall rectangles
            for poly in polygons:
                pts = [to_screen_coords(p, scale=scale, offset=offset) for p in poly.exterior.coords]
                pygame.draw.polygon(screen, wall_color, pts, width=0)

            # Draw original base polygon outline (optional)
            if base_polygon:
                outline_pts = [to_screen_coords(p, scale=scale, offset=offset) for p in base_polygon.exterior.coords]
                copied_list = copy.deepcopy(outline_pts)
                pygame.draw.polygon(screen, (255, 0, 0), copied_list, width=1)
                for point in copied_list:
                    # Draw each point with its label
                    (sx, sy) = point
                    if (
                            isinstance(sx, (int, float)) and
                            isinstance(sy, (int, float)) and
                            math.isfinite(sx) and math.isfinite(sy)
                    ):
                        x = max(0, sx)
                        y = max(0, sy)
                        #try:
                            #print("")
                            #label = self.font.render(f"x:{x:.1f},y:{y:.1f}", True, (255, 0, 0))
                            #screen.blit(label, (sx + 5, sy - 5))
                        #except Exception as e:
                        #    print(f"Failed to render or blit text at ({x},{y}):", e)


            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    running = False

        pygame.quit()
