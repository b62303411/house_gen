import copy
import math
from collections import defaultdict
import faulthandler
from typing import List

import numpy as np
import pygame
from shapely import Polygon, Point
from shapely.affinity import translate, rotate


from floor_plan_reader.math.Constants import Constants
from floor_plan_reader.math.vector import Vector

from vector_based.agents.blob import Blob

from vector_based.io_util import IoUtil
from vector_based.poly_to_rect import PlyToRect
from vector_based.img_reader import ImgReader
from vector_based.draw_util import DrawUtil
from vector_based.world import World

pygame.font.init()
font = pygame.font.SysFont(None, 24)

faulthandler.enable()


def get_normalized_direction(angle_deg):
    """Convert snapped angle into a unit direction vector."""
    angle_rad = math.radians(angle_deg)
    return (round(math.cos(angle_rad), 6), round(math.sin(angle_rad), 6))


def snap_angle(dx, dy):
    """Snap a direction to the nearest 45° angle."""
    angle = (math.degrees(math.atan2(dy, dx)) + 360) % 360
    snapped = round(angle / 45) * 45 % 360
    return snapped


def create_seed_rectangle_rotated(cx, cy, width=1.0, height=1.0, angle=0):
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


def create_seed_rectangles(position, size):
    cx = position.x
    cy = position.y
    seeds = []
    angles = [0, 45, 90, 135]
    for angle in angles:
        rect = create_seed_rectangle_rotated(cx, cy, size, size, angle)
        direction = Constants.angle_to_vector(angle)
        result = (position, rect, direction)
        seeds.append(result)
    return seeds


def create_seed_rectangles_shapely(polygon, size=2.0, s=1):
    center = polygon.centroid
    cx, cy = center.x, center.y
    """
    Example: generate 8 'seed' rectangles of size×size,
    all centered at (cx, cy), each rotated by 0°,45°,90°, etc.
    """
    seeds = create_seed_rectangles(center, size)
    return seeds


def make_wall_rectangle(p1, p2, width=2.0):
    """
    Create a rectangle between two points (wall segment) with fixed width.
    Aligned along the direction vector from p1 to p2.
    """
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    length = math.hypot(dx, dy)
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
            length = math.hypot(dx, dy)
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


def extract_top_left_bottom_right(poly, center, d):
    dx, dy = d
    angle = math.degrees(math.atan2(dy, dx))  # direction angle in degrees
    rotation_angle = 90 - angle  # rotate so `d` points "up" (screen-wise: negative y)

    # Rotate polygon so desired direction aligns vertically (screen "up")
    rotated = rotate(poly, rotation_angle, origin=center)
    coords = list(rotated.exterior.coords)[:-1]

    # Step 2: Find true top-left and bottom-right in image coordinate space
    top_left_rot = min(coords, key=lambda p: (p[1], p[0]))  # min y (top), then min x (left)
    bottom_right_rot = max(coords, key=lambda p: (p[1], p[0]))  # max y (bottom), then max x (right)

    # Step 3: Rotate back to original space
    top_left = rotate(Point(top_left_rot), -rotation_angle, origin=center).coords[0]
    bottom_right = rotate(Point(bottom_right_rot), -rotation_angle, origin=center).coords[0]

    return bottom_right, top_left


def try_all_single_direction_growth(direction, rect, bounds_polygon, width=4.0, step=1.0, max_steps=50):
    v = Vector(direction).normalize().scale(.5)
    perp_v = v.get_normal().scale(.5)
    opposite = v.opposite().scale(.5)
    opposite_n = opposite.get_normal().scale(.5)

    base_line = copy.deepcopy(rect)

    center = rect.centroid

    top_left, bottom_right = extract_top_left_bottom_right(rect, center, direction)

    assert base_line.area == rect.area
    tl_v = Vector((top_left[0], top_left[1]))
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
            print("move top_left_corner front")
            print(str(direction))
            print(str(base_line.area))
            print(str(candidate.area))
            print(str(candidate))

        base_line = candidate

    # move top_left_corner left
    center = base_line.centroid
    top_left, bottom_right = extract_top_left_bottom_right(base_line, center, direction)
    corner_top_left_x_candidate = top_left[0] + opposite_n.dx()
    corner_top_left_y_candidate = top_left[1] + opposite_n.dy()

    candidate_coords = [(corner_top_left_x_candidate, corner_top_left_y_candidate),
                        (bottom_right[0], bottom_right[1])]
    candidate = rectangle_from_p1p2_direction(candidate_coords, direction)
    if bounds_polygon.buffer(-1e-6).covers(candidate):
        is_smaller = base_line.area < candidate.area
        if not is_smaller:
            print("move top_left_corner left")
            print(str(direction))
            print(str(base_line.area))
            print(str(candidate.area))
            print(str(candidate))
        else:
            base_line = candidate

    # move bottom_right_corner  botom
    center = base_line.centroid
    top_left, bottom_right = extract_top_left_bottom_right(base_line, center, direction)

    corner_bottom_right_x_candidate = bottom_right[0] + opposite.dx()
    corner_bottom_right_y_candidate = bottom_right[1] + opposite.dy()
    candidate_coords = [(top_left[0], top_left[1]),
                        (corner_bottom_right_x_candidate, corner_bottom_right_y_candidate)]
    candidate = rectangle_from_p1p2_direction(candidate_coords, direction)
    if bounds_polygon.buffer(-1e-6).covers(candidate):
        if (base_line.area < candidate.area):
            base_line = candidate
        else:
            print("move bottom_right_corner  botom")
            print(str(direction))
            print(str(base_line.area))
            print(str(candidate.area))
            print(str(candidate))

    center = base_line.centroid
    top_left, bottom_right = extract_top_left_bottom_right(base_line, center, direction)
    # move bottom_right corner right
    (corner_bottom_right_x, corner_bottom_right_y) = (base_line.bounds[2], base_line.bounds[3])
    corner_bottom_right_x_candidate = bottom_right[0] + perp_v.dx()
    corner_bottom_right_y_candidate = bottom_right[1] + perp_v.dy()
    candidate_coords = [(top_left[0], top_left[1]),
                        (corner_bottom_right_x_candidate, corner_bottom_right_y_candidate)]
    candidate = rectangle_from_p1p2_direction(candidate_coords, direction)
    if bounds_polygon.buffer(-1e-6).covers(candidate):
        if (base_line.area < candidate.area):
            base_line = candidate
        else:
            print("move bottom_right corner right")
            print(str(direction))
            print(str(base_line.area))
            print(str(candidate.area))
            print(str(candidate))

    if base_line == rect:
        return rect

    return try_all_single_direction_growth(direction, base_line, bounds_polygon)


def generate_seed_centers(polygon, direction, spacing=2.0, buffer=0.0):
    """
    Generate a grid of points inside the polygon aligned to `direction`.

    Parameters:
        polygon: Shapely Polygon
        direction: tuple (dx, dy) - main axis of rectangle
        spacing: distance between seed centers
        buffer: shrink polygon a little to avoid edge clipping

    Returns:
        List of (x, y) tuples - centers for potential seeds
    """
    # Normalize direction and compute perpendicular
    dir_vec = np.array(direction.direction) / np.linalg.norm(direction.direction)
    norm_vec = np.array([-dir_vec[1], dir_vec[0]])

    # Get bounding box in this orientation
    angle_deg = math.degrees(math.atan2(dir_vec[1], dir_vec[0]))
    center = polygon.centroid.coords[0]
    rotated_poly = rotate(polygon, -angle_deg, origin=center)
    minx, miny, maxx, maxy = rotated_poly.bounds

    # Step in rotated space, generate grid points
    points = []
    for i in np.arange(minx + spacing / 2, maxx, spacing):
        for j in np.arange(miny + spacing / 2, maxy, spacing):
            p_rot = np.array([i, j])
            # Rotate point back to original orientation
            x = (p_rot[0] - center[0]) * math.cos(math.radians(angle_deg)) - \
                (p_rot[1] - center[1]) * math.sin(math.radians(angle_deg)) + center[0]
            y = (p_rot[0] - center[0]) * math.sin(math.radians(angle_deg)) + \
                (p_rot[1] - center[1]) * math.cos(math.radians(angle_deg)) + center[1]
            pt = Point((x, y))
            if polygon.buffer(-buffer).contains(pt):
                points.append((x, y))
    return points


def generate_seed_rectangles(polygon, spacing=2.0, size=.5):
    angles = [0, 45, 90, 135]
    centers = []
    for angle in angles:
        direction = Constants.angle_to_vector(angle)
        centers += generate_seed_centers(polygon, direction, spacing=spacing, buffer=0.2)

    seeds = []

    for cx, cy in centers:
        seeds_ = create_seed_rectangles(Point(cx, cy), size=size)
        for s in seeds_:
            if polygon.contains(s[1]):
                seeds.append(s)

    filtered_seeds = filter_seeds_by_overlap(seeds, max_overlap_ratio=0.5)

    return filtered_seeds


def remove_duplicate_rectangles(rects, max_overlap_ratio=0.5):
    """
    Remove rectangles that significantly overlap (by ratio), keeping only one.

    Parameters:
        rects: List of Shapely Polygons
        max_overlap_ratio: float, overlap threshold (e.g. 0.8 = 80%)

    Returns:
        List of filtered polygons (deduplicated)
    """
    kept = []

    for candidate in rects:
        c = PlyToRect.normalize_rectangle_width(candidate)
        is_duplicate = False

        for existing in kept:
            intersection = c.intersection(existing)
            if intersection.is_empty:
                continue

            overlap1 = intersection.area / candidate.area
            overlap2 = intersection.area / existing.area

            if overlap1 > max_overlap_ratio and overlap2 > max_overlap_ratio:
                is_duplicate = True
                break

        if not is_duplicate:
            kept.append(c)

    return kept


def filter_rect_by_overlap(seeds, max_overlap_ratio=0.4):
    """
    Filters out seeds that overlap more than `max_overlap_ratio` with already accepted seeds.

    Parameters:
        seeds: list of Shapely Polygons (e.g. rotated rectangles)
        max_overlap_ratio: float between 0 and 1 (e.g., 0.5 = 50%)

    Returns:
        filtered: list of accepted seed polygons
    """
    accepted = []

    for candidate in seeds:
        c = PlyToRect.normalize_rectangle_width(candidate)
        keep_candidate = True
        to_remove = []

        for i, existing in enumerate(accepted):
            intersection = c.intersection(existing)
            if intersection.is_empty:
                continue

            # Overlap relative to each seed
            overlap_cand = intersection.area / candidate.area
            overlap_exist = intersection.area / existing.area

            if overlap_cand > max_overlap_ratio or overlap_exist > max_overlap_ratio:
                if candidate.area > existing.area:
                    to_remove.append(i)
                    print(f"r{i}")
                else:
                    keep_candidate = False
                    break

        # Remove all smaller conflicting rectangles
        for i in reversed(to_remove):
            accepted.pop(i)

        if keep_candidate:
            accepted.append(c)

    return accepted


def filter_seeds_by_overlap(seeds, max_overlap_ratio=0.5):
    """
    Filters out seeds that overlap more than `max_overlap_ratio` with already accepted seeds.

    Parameters:
        seeds: list of Shapely Polygons (e.g. rotated rectangles)
        max_overlap_ratio: float between 0 and 1 (e.g., 0.5 = 50%)

    Returns:
        filtered: list of accepted seed polygons
    """
    filtered = []

    for center, candidate, direction in seeds:
        too_much_overlap = False

        for accepted in filtered:
            intersection = candidate.intersection(accepted[1])
            if intersection.is_empty:
                continue

            overlap_ratio = intersection.area / candidate.area
            if overlap_ratio > max_overlap_ratio:
                too_much_overlap = True
                break

        if not too_much_overlap:
            filtered.append((center, candidate, direction))

    return filtered


def grow_poly(polygon, seeds):
    results = []
    for center, rect, direction in seeds:
        x = center.x
        y = center.y
        (dx, dy) = direction.direction
        best = try_all_single_direction_growth(
            direction=(dx, dy),
            rect=rect,
            bounds_polygon=polygon,
            width=4.0,
            step=1.0,
            max_steps=100
        )
        if best:
            results.append(best)
    filtered = filter_rect_by_overlap(results)
    return filtered


def read_polygons():
    blobs =  []
    img_reader = ImgReader()
    draw = DrawUtil()
    polygons, clean_mask = img_reader.read('../floor_plans/fp2.png')
    rectangles = []
    clean_view = []
    world = World()
    world.set_polygons(polygons)
    world.grid = clean_mask
    i = 0
    for p in polygons:
        #agent_id, world, x, y


        #blob_.random_seeds()
        #blob_.ray_trace()
        i = i + 1
        # rectangle_list = decompose_polygon_to_rectangles(p)  # returns a list of rects for this polygon
        # draw.draw_wall_rectangles_pygame(rectangle_list, base_polygon=p, image_shape=clean_mask.shape)
        # rectangles.extend(rectangle_list)  # += also works
        # print(f"Decomposed {len(rectangle_list)} rectangles from polygon.")
        # seed = p.centroid.coords[0]  # e.g. (x, y)
        # seeds = create_seed_rectangles(p, wall_width=4.0, step=10)
        # best_walls = []
        # all_rectangles = []
        # polygon, wall_width = 4.0, step = 10
        #seeds = generate_seed_rectangles(p, 1.0, 1)
        #IoUtil.save_blob_with_seeds(f"blob_{i}", p, seeds, f"blob_{i}")
        # rect, direction
        #filtered = grow_poly(p, seeds)
        #clean_view += filtered
        # Visualize it or add it to your structure
        #res = blob_.filter_rect_by_overlap()
        #clean_view = clean_view+res
        #draw.draw_wall_rectangles_pygame(polygons=res, base_polygon=p, image_shape=clean_mask.shape)

        world.create_blob(p)

    for i in range(1, 100):
        poly = []
        for r in world.segments:
            poly = poly + [r.collision_box.get_polygon()]
        if len(poly) > 1:
            draw.draw_wall_rectangles_pygame(polygons=poly, base_polygon=None, image_shape=clean_mask.shape)
        world.run()





def test():
    img_reader = ImgReader()
    polygons, clean_mask = img_reader.read('../floor_plans/fp2.png')
    blob_id, blob_polygon, seed_polygons = IoUtil.load_blob_with_seed_centers("blob_12")
    world = World()
    blob_ = Blob(id, world)
    blob_.poly = blob_polygon
    blob_.random_seeds()
    # blob_.partition_blob()
    blob_.test()
    #blob_.ray_trace()
    draw = DrawUtil()
    res = blob_.filter_rect_by_overlap()
    list = []
    for s in blob_.segments:
        list = list + [s]
    # filtered = grow_blob(blob_, seed_polygons)
    draw.draw_wall_rectangles_pygame(polygons=list, base_polygon=blob_polygon, image_shape=clean_mask.shape)

if __name__ == "__main__":
    test()
