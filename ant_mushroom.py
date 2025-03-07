import pygame
import random
import numpy as np
import cv2
import math

class Ant:
    def __init__(self, x, y, ant_id):
        self.x = x
        self.y = y
        self.ant_id = ant_id
        self.state = "idle"  # just a placeholder
        self.path = [(x, y)]

class Mushroom:
    """
    A simple rectangle-based mushroom that can have an orientation (angle).
    For simplicity, store: center (cx, cy), angle, width, height.
    """
    def __init__(self, cx, cy, mushroom_id):
        self.cx = float(cx)
        self.cy = float(cy)
        self.angle = 0.0             # Radians or degrees, up to you
        self.width = 1              # Start small
        self.height = 1             # Start small
        self.mushroom_id = mushroom_id
        self.alive = True           # If we need to remove it or merge it

    def get_occupied_cells(self):
        """
        Return a list of (x,y) integer coordinates that this mushroom occupies.
        For demonstration, we'll do an axis-aligned rectangle ignoring angle.
        If you want diagonal orientation, you'd apply a rotation transform here.

        Let's define half-w and half-h, and round to int.
        """
        hw = self.width / 2.0
        hh = self.height / 2.0

        # top-left corner, bottom-right corner
        x_min = int(math.floor(self.cx - hw))
        x_max = int(math.floor(self.cx + hw))
        y_min = int(math.floor(self.cy - hh))
        y_max = int(math.floor(self.cy + hh))

        cells = []
        for y in range(y_min, y_max+1):
            for x in range(x_min, x_max+1):
                cells.append((x, y))
        return cells

def get_neighbors_8(x, y, width, height):
    coords = []
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            if dx == 0 and dy == 0:
                continue
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height:
                coords.append((nx, ny))
    return coords

def find_valid_neighbors(grid, visited, x, y, allow_revisit=False):
    """
    Here, grid=1 => 'food' (i.e. ants can move), 0 => wall (blocked).
    'visited' is an array where visited[ny, nx] != 0 means some ant ID is there.
    """
    height, width = grid.shape
    valid = []
    neighbors = get_neighbors_8(x, y, width, height)
    for (nx, ny) in neighbors:
        if grid[ny, nx] == 1:
            if allow_revisit or visited[ny, nx] == 0:
                valid.append((nx, ny))
    return valid

def move_ant(ant, nx, ny, visited):
    ant.x = nx
    ant.y = ny
    ant.path.append((nx, ny))
    visited[ny, nx] = ant.ant_id

def run_ant_simulation(
    image_path,
    threshold=200,     # if pixel >= threshold => food, else wall
    num_ants=20,
    allow_revisit=True
):
    # 1) Load grayscale
    img_gray = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img_gray is None:
        raise FileNotFoundError(f"Cannot load image: {image_path}")

    # 2) Create grid: 1=food (empty), 0=wall
    grid = (img_gray >= threshold).astype(np.uint8)
    height, width = grid.shape

    # 3) Init Pygame with the *exact* dimensions as the image
    pygame.init()
    screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
    pygame.display.set_caption("Ant & Mushroom Demo (Zoomable)")

    clock = pygame.time.Clock()

    # 4) Create a floorplan surface (the base image showing white/black)
    floorplan_surf = pygame.Surface((width, height))
    for y in range(height):
        for x in range(width):
            if grid[y, x] == 1:
                floorplan_surf.set_at((x, y), (255, 255, 255))  # white => food
            else:
                floorplan_surf.set_at((x, y), (0, 0, 0))        # black => wall

    # 5) Setup a visited array for ants
    visited = np.zeros((height, width), dtype=np.int32)

    # 5b) Setup an array for mushrooms
    mushroom_id_map = np.zeros((height, width), dtype=np.int32)

    # 6) Spawn ants at random "food" locations
    empty_pixels = np.argwhere(grid == 1)
    if len(empty_pixels) == 0:
        print("No empty space found!")
        return

    chosen_indices = random.sample(range(len(empty_pixels)), min(num_ants, len(empty_pixels)))
    ants = []
    for i, idx in enumerate(chosen_indices):
        py, px = empty_pixels[idx]
        ant = Ant(px, py, i+1)
        ants.append(ant)
        visited[py, px] = ant.ant_id

    # We'll store mushrooms in a list
    mushrooms = []
    mushroom_id_counter = 1

    # 7) Zoom parameters
    zoom_factor = 1.0  # Start at 1.0 (100% scale)
    min_zoom = 0.1
    max_zoom = 5.0


if __name__ == "__main__":
    run_ant_simulation(
        image_path="dark_tones_only.png",
        threshold=200,
        num_ants=2000,
        allow_revisit=True
    )