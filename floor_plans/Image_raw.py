import copy
import math
from collections import defaultdict
from math import radians, cos, sin, degrees, atan2, hypot
from math import hypot

from pygame import font
from shapely.affinity import translate, rotate
from shapely.geometry import Point
import cv2
import numpy as np
import pygame
from matplotlib.collections import PatchCollection
from shapely import Polygon, box, LineString

from matplotlib.patches import Polygon as MplPolygon

from floor_plan_reader.math.Constants import Constants
from floor_plan_reader.math.collision_box import CollisionBox
from floor_plan_reader.math.vector import Vector


def extract_wall_polygons(image_path, darkness_threshold=30, min_area=20):
    """
    Extract wall shapes (drawn in black) from an image, even if blurred or low-res.

    Args:
        image_path (str): Path to the input image.
        darkness_threshold (int): Max brightness to consider a pixel part of a wall (0–255).
        min_area (int): Minimum area (in pixels) for a polygon to be considered valid.

    Returns:
        List[Polygon]: List of Shapely polygons representing wall contours.
    """
    # Step 1: Load and convert to grayscale
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Step 2: Threshold to detect "almost black"
    _, mask = cv2.threshold(gray, darkness_threshold, 255, cv2.THRESH_BINARY_INV)

    # Step 3: Morphological closing to absorb bleed
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    closed = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    # Step 4: Find contours
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Step 5: Convert contours to Shapely polygons
    polygons = []
    for contour in contours:
        if len(contour) >= 3:
            coords = [(int(pt[0][0]), int(pt[0][1])) for pt in contour]
            poly = Polygon(coords)
            if poly.is_valid and poly.area >= min_area:
                polygons.append(poly)

    return polygons


image = cv2.imread('fp2.png')  # Color image
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# Define threshold for "almost black"
_, wall_mask = cv2.threshold(gray, 30, 255, cv2.THRESH_BINARY_INV)

kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
closed_mask = cv2.morphologyEx(wall_mask, cv2.MORPH_CLOSE, kernel)

num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(closed_mask)
min_area = 20  # discard small dots

clean_mask = np.zeros_like(closed_mask)
for i in range(1, num_labels):  # skip background
    if stats[i, cv2.CC_STAT_AREA] >= min_area:
        clean_mask[labels == i] = 255

cv2.imshow("Wall Mask", clean_mask)
cv2.waitKey(0)

polygons = extract_wall_polygons('fp2.png')

import matplotlib.pyplot as plt


def preview_polygons(polygons, image_shape):
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


preview_polygons(polygons, clean_mask.shape)


def snap_angle(dx, dy):
    """Snap a direction to the nearest 45° angle."""
    angle = (degrees(atan2(dy, dx)) + 360) % 360
    snapped = round(angle / 45) * 45 % 360
    return snapped


def get_normalized_direction(angle_deg):
    """Convert snapped angle into a unit direction vector."""
    angle_rad = radians(angle_deg)
    return (round(cos(angle_rad), 6), round(sin(angle_rad), 6))


def make_wall_rectangle(p1, p2, width=2.0):
    """
    Create a rectangle between two points (wall segment) with fixed width.
    Aligned along the direction vector from p1 to p2.
    """
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    length = hypot(dx, dy)
    if length == 0:
        return None

    # Normalize direction and normal
    dir_x, dir_y = dx / length, dy / length
    ndx, ndy = -dir_y, dir_x
    hw = width / 2

    # Four corners
    p1_left = (p1[0] + ndx * hw, p1[1] + ndy * hw)
    p1_right = (p1[0] - ndx * hw, p1[1] - ndy * hw)
    p2_left = (p2[0] + ndx * hw, p2[1] + ndy * hw)
    p2_right = (p2[0] - ndx * hw, p2[1] - ndy * hw)

    return Polygon([p1_left, p2_left, p2_right, p1_right])


def decompose_polygon_to_rectangles(polygon, wall_width=2.0, angle_snap=True):
    """
    Decompose a simplified polygon into a list of rotated rectangles,
    assuming the wall is composed of 45°-aligned segments.

    Args:
        polygon (Polygon): Shapely polygon (already simplified)
        wall_width (float): Fixed wall width (in pixels)
        angle_snap (bool): Whether to snap segments to 45° increments

    Returns:
        List[Polygon]: List of rectangular wall segments
    """
    coords = list(polygon.exterior.coords)
    segments_by_direction = defaultdict(list)

    for i in range(len(coords) - 1):
        p1 = coords[i]
        p2 = coords[i + 1]
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]

        if angle_snap:
            angle = snap_angle(dx, dy)
            dir_vec = get_normalized_direction(angle)
        else:
            length = hypot(dx, dy)
            dir_vec = (round(dx / length, 6), round(dy / length, 6))

        # Group by direction
        segments_by_direction[dir_vec].append((p1, p2))

    rectangles = []

    # Build rectangles from segments
    for dir_vec, segs in segments_by_direction.items():
        for p1, p2 in segs:
            # ollisionBox.create_from_line()
            rect = make_wall_rectangle(p1, p2, width=wall_width)
            if rect and rect.is_valid:
                rectangles.append(rect)

    return rectangles


pygame.font.init()
font = pygame.font.SysFont(None, 24)


def draw_wall_rectangles_pygame(polygons, base_polygon=None, image_shape=(800, 800), bg_color=(30, 30, 30),
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
            pygame.draw.polygon(screen, (255, 0, 0), outline_pts, width=1)
            for point in outline_pts:
                # Draw each point with its label
                (sx, sy) = point

                coords = point
                x, y = coords[0], coords[1]
                x = max(0, x)
                y = max(0, y)
                try:
                    label = font.render(f"x:{x:.1f},y:{y:.1f}", True, (255, 0, 0))
                except:
                    pass
                screen.blit(label, (sx + 5, sy - 5))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False

    pygame.quit()


def grow_rectangle(seed_rect, bounds_poly, step=1.0, max_iter=100):
    """
    Grows a rectangle outward symmetrically until it no longer fits inside the bounding shape.

    Args:
        seed_rect: a shapely Polygon representing the starting rectangle
        bounds_poly: the polygon representing the full wall/room boundary
        step: how much to grow per direction
        max_iter: safety limit to avoid infinite loops

    Returns:
        Polygon: the largest grown rectangle that fits inside the shape
    """
    minx, miny, maxx, maxy = seed_rect.bounds

    for _ in range(max_iter):
        expanded = box(minx - step, miny - step, maxx + step, maxy + step)
        if bounds_poly.contains(expanded):
            minx -= step
            miny -= step
            maxx += step
            maxy += step
        else:
            break

    return box(minx, miny, maxx, maxy)


rectangles = []


def generate_directions_45():
    angles = [math.radians(a) for a in range(0, 360, 45)]
    return [(round(math.cos(a), 6), round(math.sin(a), 6)) for a in angles]


DIRECTIONS_8 = generate_directions_45()


def grow_polygon_along_direction(poly, direction, step, bounds_poly):
    """
    Grows a polygon in a specified direction (dx, dy) by 'step',
    as long as it remains inside the bounds.
    """
    from shapely.affinity import translate

    dx, dy = direction
    scale = step
    grown = poly

    while True:
        candidate = translate(grown, xoff=dx * scale, yoff=dy * scale)
        union = grown.union(candidate)

        if bounds_poly.contains(union):
            grown = union
            scale += step
        else:
            break

    return grown


def grow_wall_segment(seed_point, direction, bounds_polygon, width=4.0, max_steps=100, step_size=1.0):
    """
    Grows a wall rectangle from a seed point in the given direction until it hits the edge of the bounding polygon.
    """
    from shapely.geometry import Polygon
    from shapely.affinity import translate

    dx, dy = direction
    current_length = step_size
    best_polygon = None

    for _ in range(max_steps):
        # End point of the line segment
        p2 = (seed_point[0] + dx * current_length, seed_point[1] + dy * current_length)
        wall = make_wall_rectangle(seed_point, p2, width)

        if wall is not None and bounds_polygon.contains(wall):
            best_polygon = wall
            current_length += step_size
        else:
            break

    return best_polygon


def grow_all_edges(rect, bounds_polygon, step_size=1.0, max_steps=100):
    """
    Attempts to grow each edge of the given rectangle in its outward direction.
    Returns the best (largest-area) rectangle that still fits within bounds_polygon.

    Args:
        rect: A shapely Polygon (must be a rectangle with 4 points)
        bounds_polygon: The wall mask to grow within
        step_size: Distance to move the edge per iteration
        max_steps: Max growth steps per edge

    Returns:
        A Polygon representing the largest valid grown rectangle
    """
    best_rect = rect
    best_area = rect[0].area

    coords = list(rect[0].exterior.coords)[:-1]  # drop closing point
    count = len(coords)
    assert count == 4, "Expected a 4-point rectangle"

    # Edges: 0–1, 1–2, 2–3, 3–0
    for edge_index in range(4):
        # Compute direction vector (edge normal)
        p1 = coords[edge_index]
        p2 = coords[(edge_index + 1) % 4]
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        length = hypot(dx, dy)

        # Normal vector (perpendicular to edge)
        ndx = -dy / length
        ndy = dx / length

        grown = grow_rectangle_by_extruding_edge(rect, edge_index, (ndx, ndy), bounds_polygon, max_steps, step_size)

        if grown and grown.area > best_area:
            best_area = grown.area
            best_rect = grown

    return best_rect


def make_wall_rectangle_from_direction(center, direction, length, width):
    """
    Creates a rectangle (wall candidate) from a center point and a given direction.

    Args:
        center: (x, y) center of the rectangle
        direction: normalized (dx, dy) vector along the wall stem
        length: total stem length (along direction)
        width: total wall width (perpendicular to direction)

    Returns:
        A shapely Polygon with 4 corners
    """
    from shapely.geometry import Polygon
    from math import hypot

    cx, cy = center
    dx, dy = direction
    norm = hypot(dx, dy)
    if norm == 0:
        return None

    ux, uy = dx / norm, dy / norm  # stem direction (unit vector)
    nx, ny = -uy, ux  # normal direction (perpendicular)

    hl = length / 2
    hw = width / 2

    # Generate points
    p1 = (cx - ux * hl, cy - uy * hl)
    p2 = (cx + ux * hl, cy + uy * hl)

    p1_left = (p1[0] + nx * hw, p1[1] + ny * hw)
    p1_right = (p1[0] - nx * hw, p1[1] - ny * hw)
    p2_left = (p2[0] + nx * hw, p2[1] + ny * hw)
    p2_right = (p2[0] - nx * hw, p2[1] - ny * hw)

    return Polygon([p1_left, p2_left, p2_right, p1_right])


def create_seeds(polygon, wall_width=4.0, step=10):
    center = polygon.centroid
    cx, cy = center.x, center.y
    diagonal_length = math.hypot(2, 2)

    # We'll define half_diagonal = diagonal_length / 2
    half_diag = diagonal_length / 2
    seeds = []
    # Try each direction
    for (dx, dy) in DIRECTIONS_8:
        center = Vector((cx, cy))
        v_dir = Vector((dx, dy))
        n_vec = v_dir.get_normal()  # assumed normalized & perpendicular to (p1->p2)
        on_vec = n_vec.opposite()
        o_dir = v_dir.opposite()
        p1 = center + v_dir + n_vec
        p2 = center + o_dir + on_vec
        seed_poly = rectangle_from_p1p2_direction((p1, p2), (dx, dy))

        # Check if valid
        if seed_poly.area > 0:
            # optional: we can check if it lies partially in polygon
            # or we keep them all
            seeds.append((center, seed_poly, (dx, dy)))

    return seeds


# polygon, wall_width=4.0, step=10
def create_seed_rectangles(polygon, wall_width=4.0, step=10):
    """
    Seeds small wall rectangles across the polygon, using all 8 orientations.
    """
    center = polygon.centroid
    cx, cy = center.x, center.y

    seeds = []
    centroid = polygon.centroid
    x = centroid.x
    y = centroid.y
    for direction in DIRECTIONS_8:
        dx, dy = direction
        p2 = (x + dx, y + dy)
        line = LineString([centroid, p2])
        # center, direction, length, width
        rect = CollisionBox.make_wall_rectangle_from_direction(centroid, direction, wall_width, wall_width)
        # rect = cb.get_polygon()
        if len(rect.bounds) == 4 and rect.area > 0:
            seeds.append((centroid, rect, direction))
        else:
            print("wtf")

    return seeds


def grow_wall_from_center(x, y, dx, dy, bounds_polygon, width=4.0, step=1.0, max_steps=100):
    length = 4.0
    last_valid = make_wall_rectangle_from_direction((x, y), (dx, dy), length, width)

    for _ in range(max_steps):
        length += step
        candidate = make_wall_rectangle_from_direction((x, y), (dx, dy), length, width)
        if candidate and bounds_polygon.buffer(-1e-6).covers(candidate):
            last_valid = candidate
        else:
            break

    return last_valid


def grow_rectangle_by_extruding_edge(rect: Polygon, edge_index: int, direction: tuple, bounds_polygon: Polygon,
                                     max_steps=100, step_size=1.0):
    """
    Extrudes one edge of a rectangle polygon outward along a direction vector
    while the polygon remains inside bounds_polygon.

    edge_index: 0-3 (edge between point i and i+1)
    direction: (dx, dy) extrusion direction
    """
    coords = list(rect.exterior.coords)[:-1]  # drop duplicate closing point
    assert len(coords) == 4, "Expected a rectangle with 4 sides"

    last_valid = Polygon(coords)
    steps = 0

    while steps < max_steps:
        # Move only the two points that make up the edge
        new_coords = coords[:]
        i1 = edge_index
        i2 = (edge_index + 1) % 4

        for i in [i1, i2]:
            new_coords[i] = (
                new_coords[i][0] + direction[0] * step_size,
                new_coords[i][1] + direction[1] * step_size
            )

        # Reconnect into polygon
        candidate = Polygon(new_coords)

        if candidate.is_valid and bounds_polygon.covers(candidate):
            coords = new_coords
            last_valid = candidate
            steps += 1
        else:
            break

    return last_valid


def grow_wall_segment_bidirectional(seed_point, direction, bounds_polygon, width=4.0, max_steps=100, step_size=1.0):
    """
    Grows a wall rectangle symmetrically in both directions from a seed point along a given direction.
    Returns the largest valid rectangle within bounds.
    """
    from shapely.geometry import Polygon
    from math import hypot

    dx, dy = direction
    length_fwd = 0
    length_back = 0
    best_polygon = None

    for _ in range(max_steps):
        p1 = (seed_point[0] - dx * length_back, seed_point[1] - dy * length_back)
        p2 = (seed_point[0] + dx * length_fwd, seed_point[1] + dy * length_fwd)

        wall = make_wall_rectangle(p1, p2, width)

        if wall and bounds_polygon.covers(wall):
            best_polygon = wall
            length_fwd += step_size
            length_back += step_size
        else:
            break

    return best_polygon


def grow_in_all_directions(seed_point, bounds_polygon, width=4.0):
    best_wall = None
    best_area = 0

    for direction in DIRECTIONS_8:
        wall = grow_wall_segment_bidirectional(seed_point, direction, bounds_polygon, width=width)
        if wall and wall.area > best_area:
            best_area = wall.area
            best_wall = wall

    return best_wall


def grow_wall_from_center_directional(center, direction, bounds_polygon, width=4.0, step=1.0, max_steps=100,
                                      grow_back=True, grow_front=True):
    """
    Grows a wall rectangle by increasing length from a center point in a given direction.

    Args:
        center: (x, y)
        direction: normalized (dx, dy)
        bounds_polygon: polygon to constrain growth
        width: wall width
        step: how much to grow per iteration
        max_steps: limit iterations
        grow_back: whether to grow in -direction
        grow_front: whether to grow in +direction

    Returns:
        The final grown polygon
    """

    cx, cy = center
    dx, dy = direction
    norm = hypot(dx, dy)
    if norm == 0:
        return None
    ux, uy = dx / norm, dy / norm

    # Initialize with short rectangle
    length_back = step if grow_back else 0
    length_front = step if grow_front else 0
    best_polygon = make_wall_rectangle_from_direction(center, (ux, uy), length_back + length_front, width)

    for _ in range(max_steps):
        if grow_back:
            length_back += step
        if grow_front:
            length_front += step

        total_length = length_back + length_front
        cx_shifted = cx + (length_front - length_back) * ux / 2
        cy_shifted = cy + (length_front - length_back) * uy / 2

        candidate = make_wall_rectangle_from_direction((cx_shifted, cy_shifted), (ux, uy), total_length, width)

        if candidate and bounds_polygon.buffer(-1e-6).covers(candidate):
            best_polygon = candidate
        else:
            break

    return best_polygon


def recursive_grow_rectangle(center, direction, rect, bounds_polygon,
                             width=4.0, step=1.0, max_steps=50, depth=0):
    """
    Recursively tries moving each corner of 'rect' in certain directions.
    Returns the largest valid rectangle found.

    center:   not used directly here, but you said it's part of the signature
    direction: (dx, dy) vector to push corners
    rect:    the current oriented rectangle (or bounding box)
    bounds_polygon: the shape in which rect must stay
    width, step, max_steps: growth parameters
    depth:   recursion depth to avoid infinite loops
    """

    if depth >= max_steps:
        return rect  # we've recursed enough, stop

    minx, miny, maxx, maxy = rect.bounds
    best_rect = rect
    best_area = rect.area

    # We'll define small helpers to build a bounding-box Polygon from corners:
    def make_box(x1, y1, x2, y2):
        from shapely.geometry import box
        if x1 > x2:  # ensure left < right
            x1, x2 = x2, x1
        if y1 > y2:  # ensure bottom < top
            y1, y2 = y2, y1
        return box(x1, y1, x2, y2)

    # 1) Move top-left corner "forward" (along 'direction')
    #    top-left corner = (minx, miny)
    tlx_candidate = minx + direction[0] * step
    tly_candidate = miny + direction[1] * step
    candidate_1 = make_box(tlx_candidate, tly_candidate, maxx, maxy)

    # If valid => recurse
    if bounds_polygon.buffer(-1e-6).covers(candidate_1):
        grown_1 = try_all_single_direction_growth(
            center, direction, candidate_1, bounds_polygon,
            width, step, max_steps, depth + 1
        )
        if grown_1.area > best_area:
            best_area = grown_1.area
            best_rect = grown_1

    # 2) Move top-left corner "left" (perp to 'direction', for example)
    #    Let’s compute a perpendicular: if direction=(dx,dy), then perp=(-dy,dx)
    perp = (-direction[1], direction[0])
    tlx_candidate_2 = minx + perp[0] * step
    tly_candidate_2 = miny + perp[1] * step
    candidate_2 = make_box(tlx_candidate_2, tly_candidate_2, maxx, maxy)

    if bounds_polygon.buffer(-1e-6).covers(candidate_2):
        grown_2 = try_all_single_direction_growth(
            center, direction, candidate_2, bounds_polygon,
            width, step, max_steps, depth + 1
        )
        if grown_2.area > best_area:
            best_area = grown_2.area
            best_rect = grown_2

    # 3) Move bottom-right corner "forward"
    #    bottom-right corner = (maxx, maxy)
    brx_candidate = maxx + direction[0] * step
    bry_candidate = maxy + direction[1] * step
    candidate_3 = make_box(minx, miny, brx_candidate, bry_candidate)

    if bounds_polygon.buffer(-1e-6).covers(candidate_3):
        grown_3 = try_all_single_direction_growth(
            center, direction, candidate_3, bounds_polygon,
            width, step, max_steps, depth + 1
        )
        if grown_3.area > best_area:
            best_area = grown_3.area
            best_rect = grown_3

    # 4) Move bottom-right corner "right" (perp to direction but from bottom-right)
    #    We'll do a second perpendicular with sign reversed, e.g. (dy, -dx)
    perp2 = (direction[1], -direction[0])
    brx_candidate_2 = maxx + perp2[0] * step
    bry_candidate_2 = maxy + perp2[1] * step
    candidate_4 = make_box(minx, miny, brx_candidate_2, bry_candidate_2)

    if bounds_polygon.buffer(-1e-6).covers(candidate_4):
        grown_4 = try_all_single_direction_growth(
            center, direction, candidate_4, bounds_polygon,
            width, step, max_steps, depth + 1
        )
        if grown_4.area > best_area:
            best_area = grown_4.area
            best_rect = grown_4

    # If none grew, or all fails, we just return best so far
    return best_rect


def create_seed_rectangle_rotated(cx, cy, width=2.0, height=2.0, angle=0):
    """
    Creates a rectangle of size width×height, centered at (cx, cy),
    then rotates it by 'angle' degrees around that same center.

    Returns a Shapely Polygon.
    """
    # 1) Define a base rectangle centered at (0,0)
    #    corners: (-width/2, -height/2), (width/2, -height/2), ...
    base_rect = Polygon([
        (-width / 2, -height / 2),
        (width / 2, -height / 2),
        (width / 2, height / 2),
        (-width / 2, height / 2)
    ])

    # 2) Translate so center is at (cx, cy)
    moved = translate(base_rect, xoff=cx, yoff=cy)

    # 3) Rotate around (cx, cy) by 'angle' degrees
    rotated_poly = rotate(moved, angle, origin=(cx, cy))

    return rotated_poly


def create_seed_rectangles_shapely(polygon, size=2.0, s=1):
    center = polygon.centroid
    cx, cy = center.x, center.y
    """
    Example: generate 8 'seed' rectangles of size×size,
    all centered at (cx, cy), each rotated by 0°,45°,90°, etc.
    """
    seeds = []
    angles = [0, 45, 90, 135]

    for angle in angles:
        rect = create_seed_rectangle_rotated(cx, cy, size, size, angle)
        direction = Constants.angle_to_vector(angle)
        result = (center, rect, direction)
        seeds.append(result)
    return seeds
def local_coordinates(pt, center, d):
    """
    Converts the global point pt into local coordinates relative to center,
    where d is the desired normalized direction (local x-axis) and
    n = (-d.y, d.x) is the local y-axis.
    Returns (lx, ly).
    """
    cx= center.x
    cy= center.y
    x, y = pt
    # Make sure d is normalized
    d = Vector(d).normalize()
    n = Vector((-d.dy(), d.dx()))
    vec = Vector((x - cx, y - cy))
    local_x = vec.dot_product(d)
    local_y = vec.dot_product(n)
    return local_x, local_y


def sort_corners_local(corners, center, d):
    """
    Given a list of 2D points 'corners', sort them in a consistent order
    based on the local coordinate system defined by center and direction d.
    Returns the sorted list.
    """
    # Compute local coordinates for each candidate corner.
    pts_with_angle = []
    for pt in corners:
        lx, ly = local_coordinates(pt, center, d)
        # You can combine the criteria: for example, using the tuple (lx, -ly)
        # so that lower lx (more to the left) and higher ly (more "top") come first.
        pts_with_angle.append((pt, (lx, -ly)))

    # Sort by the tuple
    pts_with_angle.sort(key=lambda item: item[1])
    sorted_pts = [item[0] for item in pts_with_angle]
    return sorted_pts
def sort_corners_from_list(corners, center, d):
    # corners is a list of four points (tuples)
    return sort_corners_local(corners, center, d)


def extract_top_left_bottom_right(poly, center, d):
    dx, dy = d
    angle = math.degrees(math.atan2(dy, dx))  # direction angle in degrees
    rotation_angle = 90 - angle  # rotate so `d` points "up" (screen-wise: negative y)

    # Rotate polygon so desired direction aligns vertically (screen "up")
    rotated = rotate(poly, rotation_angle, origin=center)
    coords = list(rotated.exterior.coords)[:-1]


    # Step 2: Find true top-left and bottom-right in image coordinate space
    top_left_rot = min(coords, key=lambda p: (p[1], p[0]))       # min y (top), then min x (left)
    bottom_right_rot = max(coords, key=lambda p: (p[1], p[0]))   # max y (bottom), then max x (right)

    # Step 3: Rotate back to original space
    top_left = rotate(Point(top_left_rot), -rotation_angle, origin=center).coords[0]
    bottom_right = rotate(Point(bottom_right_rot), -rotation_angle, origin=center).coords[0]

    return  bottom_right, top_left

def try_all_single_direction_growth(direction, rect, bounds_polygon, width=4.0, step=1.0, max_steps=50):
    v = Vector(direction).normalize()
    perp_v = v.get_normal()
    opposite = v.opposite()
    opposite_n = opposite.get_normal()


    base_line = copy.deepcopy(rect)

    center = rect.centroid

    top_left, bottom_right = extract_top_left_bottom_right(rect, center,direction)


    assert base_line.area == rect.area
    tl_v = Vector((top_left[0],top_left[1]))
    tl_c = tl_v + v

    # move top_left_corner front
    corner_top_left_x_candidate = tl_c.dx()
    corner_top_left_y_candidate = tl_c.dy()
    candidate_coords = [(corner_top_left_x_candidate, corner_top_left_y_candidate),
                        (bottom_right[0], bottom_right[1])]
    candidate = rectangle_from_p1p2_direction(candidate_coords, direction)

    if bounds_polygon.buffer(-1e-6).covers(candidate):
        is_smaller = base_line.area < candidate.area
        if not is_smaller:
            print("")

        base_line = candidate

    # move top_left_corner left
    center =  base_line.centroid
    top_left, bottom_right = extract_top_left_bottom_right(base_line, center, direction)
    corner_top_left_x_candidate = top_left[0] + opposite_n.dx()
    corner_top_left_y_candidate = top_left[1] + opposite_n.dy()


    candidate_coords = [(corner_top_left_x_candidate, corner_top_left_y_candidate),
                        (bottom_right[0], bottom_right[1])]
    candidate = rectangle_from_p1p2_direction(candidate_coords, direction)
    if bounds_polygon.buffer(-1e-6).covers(candidate):
        is_smaller = base_line.area < candidate.area
        if not is_smaller:
            print("")
        assert (base_line.area < candidate.area)
        base_line = candidate

    # move bottom_right_corner  botom
    center =  base_line.centroid
    top_left, bottom_right = extract_top_left_bottom_right(base_line, center, direction)



    corner_bottom_right_x_candidate = bottom_right[0] +opposite.dx()
    corner_bottom_right_y_candidate = bottom_right[1] + opposite.dy()
    candidate_coords = [(top_left[0], top_left[1]),
                        (corner_bottom_right_x_candidate, corner_bottom_right_y_candidate)]
    candidate = rectangle_from_p1p2_direction(candidate_coords, direction)
    if bounds_polygon.buffer(-1e-6).covers(candidate):
        assert (base_line.area < candidate.area)
        base_line = candidate
    center = base_line.centroid
    top_left, bottom_right = extract_top_left_bottom_right(base_line, center, direction)
    # move bottom_right corner right
    (corner_bottom_right_x, corner_bottom_right_y) = (base_line.bounds[2], base_line.bounds[3])
    corner_bottom_right_x_candidate = bottom_right[0]+ perp_v.dx()
    corner_bottom_right_y_candidate = bottom_right[1] + perp_v.dy()
    candidate_coords = [(top_left[0], top_left[1]),
                        (corner_bottom_right_x_candidate, corner_bottom_right_y_candidate)]
    candidate = rectangle_from_p1p2_direction(candidate_coords, direction)
    if bounds_polygon.buffer(-1e-6).covers(candidate):
        assert (base_line.area < candidate.area)
        base_line = candidate

    if base_line == rect:
        return rect

    return try_all_single_direction_growth(direction, base_line, bounds_polygon)


def fix_rectangle_order(bounds):
    """
    Attempt to build a rectangle from diagonal corners p1,p2 and offset corners p3,p4.
    We'll try two permutations:
       A) [p1, p2, p3, p4]
       B) [p1, p3, p2, p4]
    and pick the first that yields a nonzero area polygon.

    Returns a Shapely Polygon or None if both fail.
    """
    p1 = bounds[0]
    p2 = bounds[1]
    p3 = bounds[2]
    p4 = bounds[3]
    corners_a = [(bounds[0], bounds[1]),( bounds[2], bounds[3])]
    poly_a = Polygon(corners_a)
    if poly_a.area > 1e-9 and not poly_a.is_empty and not poly_a.is_valid:
        # is_valid checks self-intersections, but for a rectangle we usually just check area
        return poly_a
    if poly_a.area > 1e-9:
        return poly_a

    # If that fails, swap p2 <-> p3 in the sequence
    corners_b = [p1, p3, p2, p4]
    poly_b = Polygon(corners_b)
    if poly_b.area > 1e-9:
        return poly_b


def polygon_from_unsorted_points(pts):
    """
    Takes a list of 2D points ([(x1,y1),(x2,y2),...])
    Sorts them in ascending angle around their centroid,
    and returns a Shapely Polygon in consistent winding order.
    """
    # 1) Compute centroid
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)

    # 2) Sort points by angle around centroid
    def angle_from_center(pt):
        return math.atan2(pt[1] - cy, pt[0] - cx)

    sorted_pts = sorted(pts, key=angle_from_center)

    # 3) Build polygon from sorted corners
    poly = Polygon(sorted_pts)

    if poly.area < 1:
        poly = poly.envelope
    return poly


def rectangle_from_p1p2_direction(coords, direction):
    (p1, p2) = coords
    v_dir = Vector(direction)
    """
    p1, p2: diagonal (hypotenuse) corners (x,y).
    n: a normalized vector that points from p2 to p3 (perpendicular to p1->p2).
    
    Returns: Shapely Polygon of the rectangle corners [p1, p2, p3, p4].
      - p3 is the right-angle corner
      - p4 is the last corner opposite p3
    """
    if isinstance(p1, Vector):
        p1_vec = p1
        p2_vec = p2
    else:
        p1_vec = Vector(p1)
        p2_vec = Vector(p2)

    n_vec = v_dir.get_normal()  # assumed normalized & perpendicular to (p1->p2)
    on_vec = n_vec.opposite()
    # 1) Find p3 so angle at p3 is 90°
    #    L = (p1 - p2) dot n
    L = (p1_vec - p2_vec).dot_product(n_vec)
    p3_vec = p2_vec + n_vec * L

    # 2) Find p4 by parallelogram rule
    #    p4 = p1 + (p3 - p2)
    p4_vec = p1_vec + on_vec * L

    poly = polygon_from_unsorted_points([
        (p1_vec.dx(), p1_vec.dy()),
        (p3_vec.dx(), p3_vec.dy()),
        (p2_vec.dx(), p2_vec.dy()),
        (p4_vec.dx(), p4_vec.dy())
    ])

    if poly.area == 0:
        print("")
    return poly


for p in polygons:
    rectangle_list = decompose_polygon_to_rectangles(p)  # returns a list of rects for this polygon
    draw_wall_rectangles_pygame(rectangle_list, base_polygon=p, image_shape=clean_mask.shape)
    rectangles.extend(rectangle_list)  # += also works
    print(f"Decomposed {len(rectangle_list)} rectangles from polygon.")
    seed = p.centroid.coords[0]  # e.g. (x, y)
    # seeds = create_seed_rectangles(p, wall_width=4.0, step=10)
    best_walls = []
    all_rectangles = []
    # polygon, wall_width = 4.0, step = 10
    seeds = create_seed_rectangles_shapely(p, 2.0, 48)
    # rect, direction
    results = []
    for center, rect, direction in seeds:
        x = center.x
        y = center.y
        (dx, dy) = direction.direction
        best = try_all_single_direction_growth(
            direction=(dx, dy),
            rect=rect,
            bounds_polygon=p,
            width=4.0,
            step=1.0,
            max_steps=100
        )
        if best:
            results.append(best)

    # Visualize it or add it to your structure
    draw_wall_rectangles_pygame(polygons=results, base_polygon=p, image_shape=clean_mask.shape)
