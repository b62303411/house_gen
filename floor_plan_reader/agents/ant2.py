import pygame
import random
import numpy as np
import cv2

################################################################################
# Ant (Rectangle) Data Structure
################################################################################

class RectAnt:
    def __init__(self, x, y, ant_id, width=5, height=3):
        """
        Each 'ant' is an axis-aligned rectangle of size (width x height).
        (x, y) is the *center* of that rectangle in grid coordinates.
        """
        self.x = x
        self.y = y
        self.ant_id = ant_id
        self.width = width
        self.height = height
        self.path = [(x, y)]
        self.state = "searching"  # We'll define states based on neighbor count

    @property
    def bbox(self):
        """
        Return the bounding box (left, top, right, bottom) of this rectangle
        in grid coordinates, based on the current center (self.x, self.y).
        """
        w, h = self.width, self.height
        half_w = w // 2
        half_h = h // 2

        left   = self.x - half_w
        top    = self.y - half_h
        right  = left + (w - 1)
        bottom = top + (h - 1)
        return (left, top, right, bottom)

    def __repr__(self):
        return f"RectAnt#{self.ant_id}({self.x},{self.y},size={self.width}x{self.height},state={self.state})"


################################################################################
# Collision Checking
################################################################################

def can_place_rect(grid, ants, nx, ny, w, h):
    """
    Checks if a rectangle of size (w x h), centered at (nx, ny), can be placed:
      1) Must not overlap walls in 'grid' (which is 1=empty, 0=wall).
      2) Must not overlap other ants' rectangles.
    Returns True if valid, False if collision.
    """
    height_img, width_img = grid.shape

    # Compute bounding box of the prospective position
    half_w = w // 2
    half_h = h // 2
    left   = nx - half_w
    top    = ny - half_h
    right  = left + (w - 1)
    bottom = top + (h - 1)

    # 1) Check out-of-bounds
    if left < 0 or top < 0 or right >= width_img or bottom >= height_img:
        return False

    # 2) Check for wall overlap (any pixel in this rectangle = 0 => wall => fail)
    for yy in range(top, bottom + 1):
        for xx in range(left, right + 1):
            if grid[yy, xx] == 0:
                return False

    # 3) Check collision with other ants
    #    We'll do a simple axis-aligned bounding box overlap test
    #    for each existing ant
    for other in ants:
        # Skip self-check if needed. But here, we assume we only call can_place_rect
        # for a *prospective* new position, so 'other' is never the same ant in this usage.
        l2, t2, r2, b2 = other.bbox
        # Overlap if:
        # left <= r2 and right >= l2 and top <= b2 and bottom >= t2
        if not (right < l2 or left > r2 or bottom < t2 or top > b2):
            # We have overlap
            return False

    return True


################################################################################
# State & Rendering Utilities
################################################################################

def state_from_neighbor_count(count):
    """
    Simple rule:
      0 => "searching" (purple)
      1 => "crumb"     (red)
      2 => "segment"   (blue)
      3+ => "corner"   (yellow)
    """
    if count == 0:
        return "searching"
    elif count == 1:
        return "crumb"
    elif count == 2:
        return "segment"
    else:
        return "corner"

def color_for_state(state):
    if state == "searching":
        return (128, 0, 128)   # purple
    elif state == "crumb":
        return (255, 0, 0)     # red
    elif state == "segment":
        return (0, 0, 255)     # blue
    else:
        return (255, 255, 0)   # yellow

def draw_rect_ant(screen, ant):
    """
    Draw the ant as a filled rectangle on the pygame surface
    using its bounding box in *image coordinates* (no scaling).
    """
    left, top, right, bottom = ant.bbox
    color = color_for_state(ant.state)
    # Since it's an axis-aligned rectangle, we can do:
    pygame.draw.rect(
        screen,
        color,
        pygame.Rect(left, top, (right - left + 1), (bottom - top + 1))
    )


################################################################################
# Main Logic for Movement
################################################################################

def get_8_neighbors(x, y, width, height):
    """Just gather the 8-connected neighbors for center (x,y)."""
    coords = []
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            if dx == 0 and dy == 0:
                continue
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height:
                coords.append((nx, ny))
    return coords

def find_valid_neighbors(grid, ants, ant):
    """
    For a rectangle-based ant, find up to 8 potential moves (8-connected),
    then filter out any that can't place the rectangle.
    """
    height_img, width_img = grid.shape
    x, y = ant.x, ant.y
    neighbors = get_8_neighbors(x, y, width_img, height_img)
    valid = []
    for (nx, ny) in neighbors:
        if can_place_rect(grid, ants, nx, ny, ant.width, ant.height):
            valid.append((nx, ny))
    return valid

def move_ant(ant, nx, ny):
    ant.x = nx
    ant.y = ny
    ant.path.append((nx, ny))


################################################################################
# Putting It All Together in a Pygame Demo
################################################################################

def run_rect_ant_simulation(image_path, threshold=200, num_ants=5, w=6, h=3):
    """
    - grid: 1=empty (white), 0=wall (dark)
    - Each ant is an axis-aligned rectangle of size (w x h) (width x height).
    - They do 8-connected moves if the rectangle doesn't collide with walls or other ants.
    """
    # 1) Load grayscale => grid
    img_gray = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img_gray is None:
        raise FileNotFoundError(f"Could not load {image_path}")
    grid = (img_gray >= threshold).astype(np.uint8)
    height_img, width_img = grid.shape

    # 2) Pygame init
    pygame.init()
    screen = pygame.display.set_mode((width_img, height_img))
    pygame.display.set_caption("Rectangle Ants (Axis-Aligned)")

    clock = pygame.time.Clock()

    # 3) Create a floorplan surface
    floorplan_surf = pygame.Surface((width_img, height_img))
    for y in range(height_img):
        for x in range(width_img):
            if grid[y, x] == 1:
                floorplan_surf.set_at((x, y), (255, 255, 255))  # empty => white
            else:
                floorplan_surf.set_at((x, y), (0, 0, 0))        # wall => black

    # 4) Spawn ants
    ants = []
    # We'll just sample random empty coords
    empty_coords = np.argwhere(grid == 1)
    random.shuffle(empty_coords)

    placed = 0
    for (py, px) in empty_coords:
        if placed >= num_ants:
            break
        # Try to place a rectangle of size (w x h) at (px, py)
        if can_place_rect(grid, ants, px, py, w, h):
            new_ant = RectAnt(px, py, ant_id=placed+1, width=w, height=h)
            ants.append(new_ant)
            placed += 1

    if not ants:
        print("No ants could be placed. Possibly no space for those rectangle sizes!")
        return

    # 5) Main loop
    running = True
    while running:
        clock.tick(10)  # slow enough to see changes

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        # Update each ant
        for ant in ants:
            neighbor_positions = find_valid_neighbors(grid, ants, ant)
            count = len(neighbor_positions)
            ant.state = state_from_neighbor_count(count)

            if neighbor_positions:
                (nx, ny) = random.choice(neighbor_positions)
                move_ant(ant, nx, ny)
            # else stays in place

        # Draw
        screen.blit(floorplan_surf, (0,0))
        for ant in ants:
            draw_rect_ant(screen, ant)

        pygame.display.flip()

    pygame.quit()
    print("Done. All ants have stopped.")


################################################################################
# Example Usage
################################################################################

if __name__ == "__main__":
    # Example:
    run_rect_ant_simulation(
        image_path="dark_tones/dark_tones_only.png",
        threshold=80,    # if your floor is bright => increase threshold
        num_ants=500,
        w=2,
        h=2
    )
