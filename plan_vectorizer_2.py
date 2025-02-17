import cv2
import numpy as np
import math
from itertools import combinations

############################################################
# STEP 0: Morphological Skeleton function
############################################################
def morphological_skeleton(binary):
    """
    Perform skeletonization on a binary image so that thick lines are
    reduced to a single-pixel-wide representation. This is a pure
    OpenCV approach that doesn't require ximgproc.
    """
    # Convert to an editable copy
    temp = np.copy(binary)
    # Initialize an empty image to store the final skeleton
    skeleton = np.zeros_like(temp)

    # Use a 3x3 cross-shaped kernel
    kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))

    while True:
        # Erode and then open (erode->dilate)
        eroded = cv2.erode(temp, kernel)
        opened = cv2.dilate(eroded, kernel)
        # Subtract opened from original to get the "edge" that will form part of skeleton
        temp_sub = cv2.subtract(temp, opened)
        # Combine this edge with what we already have in skeleton
        skeleton = cv2.bitwise_or(skeleton, temp_sub)
        # Update temp with the eroded image for the next iteration
        temp = eroded.copy()

        # If the image is fully eroded, we stop
        if cv2.countNonZero(temp) == 0:
            break

    return skeleton

############################################################
# STEP 1: Vectorize the floor plan
############################################################
def vectorize_floorplan(
    image_path,
    invert=False,
    morph_kernel_size=3,  # typically set to 0 if you're going to do skeletonization
    canny_threshold1=50,
    canny_threshold2=150,
    hough_threshold=50,
    min_line_length=30,
    max_line_gap=10
):
    # 1. Read the image in grayscale
    gray = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if gray is None:
        raise FileNotFoundError(f"Could not load image: {image_path}")

    # 2. Optionally invert if walls are white on black
    if invert:
        gray = cv2.bitwise_not(gray)

    # 3. Threshold to get a clean black-and-white image
    #    (Since it's typically a crisp floor plan, a fixed threshold should suffice)
    _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)

    # 4. (Optional) Morphological operations (e.g. dilation). Usually skip if doing skeleton.
    #    For instance, if you want to unify small cracks before skeletonizing, do one small dilation:
    if morph_kernel_size > 0:
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (morph_kernel_size, morph_kernel_size))
        binary = cv2.dilate(binary, kernel, iterations=1)

    # 5. Create a skeleton from the thick walls
    skeleton = morphological_skeleton(binary)

    # 6. Edge detection on the skeleton
    #    The skeleton is already mostly a single-pixel line, but Canny can help finalize edges
    edges = cv2.Canny(skeleton, canny_threshold1, canny_threshold2)

    # 7. Hough line detection on the skeleton edges
    lines_p = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi / 180,
        threshold=hough_threshold,
        minLineLength=min_line_length,
        maxLineGap=max_line_gap
    )

    # Convert Hough lines to a friendlier format
    wall_vectors = []
    if lines_p is not None:
        for line in lines_p:
            x1, y1, x2, y2 = line[0]
            # In a skeleton, 'width' is somewhat arbitrary; pick a small thickness
            wall_width = 2
            wall_vectors.append({
                "start": (x1, y1),
                "end": (x2, y2),
                "width": wall_width
            })

    # 8. (Optional) detect rectangular objects. This might require working on the original binary
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    objects = []
    for cnt in contours:
        approx = cv2.approxPolyDP(cnt, 0.02 * cv2.arcLength(cnt, True), True)
        if len(approx) == 4:
            x, y, w, h = cv2.boundingRect(approx)
            # Heuristic: "door/window" if small; otherwise "large_feature"
            obj_type = "door/window" if max(w, h) < 100 else "large_feature"
            objects.append({
                "position": (x, y),
                "width": w,
                "height": h,
                "type": obj_type
            })

    return wall_vectors, objects

############################################################
# Helper: Find intersection of two line segments
############################################################
def line_segment_intersection(p1, p2, p3, p4, epsilon=1e-9):
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4

    a1 = y2 - y1
    b1 = x1 - x2
    c1 = a1 * x1 + b1 * y1

    a2 = y4 - y3
    b2 = x3 - x4
    c2 = a2 * x3 + b2 * y3

    determinant = a1 * b2 - a2 * b1
    if abs(determinant) < epsilon:
        return None

    x = (b2 * c1 - b1 * c2) / determinant
    y = (a1 * c2 - a2 * c1) / determinant

    def within_segment(px, py, ax, ay, bx, by):
        return (min(ax, bx) - epsilon <= px <= max(ax, bx) + epsilon and
                min(ay, by) - epsilon <= py <= max(ay, by) + epsilon)

    if (within_segment(x, y, x1, y1, x2, y2) and
        within_segment(x, y, x3, y3, x4, y4)):
        return (x, y)

    return None

############################################################
# STEP 2: Redraw geometry on a blank canvas
############################################################
def draw_floorplan(vectors, objects, canvas_size=(800, 800)):
    """
    Draw lines (walls) and rectangles (doors, windows, etc.) on a white canvas
    without filling the rectangles. Then add small yellow dots for all line-line
    intersections (edge crossing).
    """
    w, h = canvas_size
    image = np.ones((h, w, 3), dtype=np.uint8) * 255

    # Draw lines
    for vector in vectors:
        start = tuple(vector["start"])
        end = tuple(vector["end"])
        width = vector["width"]
        cv2.line(image, start, end, (0, 0, 0), width)

    # Draw rectangle outlines
    for obj in objects:
        x, y = obj["position"]
        obj_w, obj_h = obj["width"], obj["height"]
        color = (128, 128, 128)  # Gray outline
        cv2.rectangle(image, (x, y), (x + obj_w, y + obj_h), color, 2)

    # Compute line-line intersections
    intersections = set()
    for (v1, v2) in combinations(vectors, 2):
        p1, p2 = v1["start"], v1["end"]
        p3, p4 = v2["start"], v2["end"]
        inter = line_segment_intersection(p1, p2, p3, p4)
        if inter is not None:
            ix, iy = map(int, inter)
            intersections.add((ix, iy))

    # Draw the intersection dots
    for (ix, iy) in intersections:
        cv2.circle(image, (ix, iy), 4, (0, 255, 255), -1)

    return image

############################################################
# STEP 3: Main demonstration
############################################################
def main():
    image_path = "w1024.jpg"  # Path to your floor plan

    # Vectorize with skeletonization
    walls, objs = vectorize_floorplan(
        image_path,
        invert=False,            # True if your plan is white lines on black
        morph_kernel_size=0,     # Usually 0 if you're doing skeletonization
        canny_threshold1=30,
        canny_threshold2=100,
        hough_threshold=30,
        min_line_length=20,
        max_line_gap=5
    )

    # Draw the final result on a canvas
    canvas = draw_floorplan(walls, objs, canvas_size=(800, 800))

    # Show
    cv2.imshow("Vectorized Floorplan", canvas)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
