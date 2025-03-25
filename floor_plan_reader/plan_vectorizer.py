import cv2
import numpy as np

############################################################
# STEP 1: Vectorize the floor plan
############################################################
def vectorize_floorplan(image_path,
                       invert=False,
                       morph_kernel_size=3,
                       canny_threshold1=50,
                       canny_threshold2=150,
                       hough_threshold=50,
                       min_line_length=30,
                       max_line_gap=10):
    # 1. Read the image in grayscale
    gray = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if gray is None:
        raise FileNotFoundError(f"Could not load image: {image_path}")

    # Optionally invert image if lines are white and background is black
    if invert:
        gray = cv2.bitwise_not(gray)

    # 2. Threshold to get a pure black-and-white mask
    # (For a well-defined black/white plan, a simple threshold works.)
    _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)

    # 3. Optional morphological operations to unify broken lines
    if morph_kernel_size > 0:
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (morph_kernel_size, morph_kernel_size))
        # Dilation helps connect thin or broken lines
        binary = cv2.dilate(binary, kernel, iterations=1)

    # 4. Edge detection
    edges = cv2.Canny(binary, canny_threshold1, canny_threshold2)

    # 5. Detect lines using Probabilistic Hough Transform
    lines_p = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi / 180,
        threshold=hough_threshold,
        minLineLength=min_line_length,
        maxLineGap=max_line_gap
    )

    wall_vectors = []
    if lines_p is not None:
        for line in lines_p:
            x1, y1, x2, y2 = line[0]
            # Estimate a default width for the wall
            wall_width = 5
            wall_vectors.append({
                "start": (x1, y1),
                "end": (x2, y2),
                "width": wall_width
            })

    # 6. Detect rectangular objects (doors, windows, etc.) using contours
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    objects = []
    for cnt in contours:
        approx = cv2.approxPolyDP(cnt, 0.02 * cv2.arcLength(cnt, True), True)
        # If the polygon has 4 corners, treat it as a rectangle
        if len(approx) == 4:
            x, y, w, h = cv2.boundingRect(approx)
            # Heuristic: If it's small, guess door/window; else, might be a large feature
            obj_type = "door/window" if max(w, h) < 100 else "large_feature"
            objects.append({
                "position": (x, y),
                "width": w,
                "height": h,
                "type": obj_type
            })

    return wall_vectors, objects

############################################################
# STEP 2: Redraw the geometry on a blank canvas
############################################################
def draw_floorplan(vectors, objects, canvas_size=(1800, 1800)):
    """Draw lines (walls) and rectangles (doors, windows, etc.) on a white canvas."""
    w, h = canvas_size
    image = np.ones((h, w, 3), dtype=np.uint8) * 255

    # Draw lines/walls
    for vector in vectors:
        start = tuple(vector["start"])
        end = tuple(vector["end"])
        width = vector["width"]
        cv2.line(image, start, end, (0, 0, 0), width)
        # Add yellow dots on line endpoints
    for vector in vectors:
            start = tuple(vector["start"])
            end = tuple(vector["end"])
            # Draw small filled circles
            cv2.circle(image, start, 4, (0, 255, 255), -1)  # BGR: (0,255,255) is yellow
            cv2.circle(image, end, 4, (0, 255, 255), -1)
    # Draw rectangular objects
    for obj in objects:
        x, y = obj["position"]
        obj_w, obj_h = obj["width"], obj["height"]
        color = (128, 128, 128)  # Gray
        cv2.rectangle(image, (x, y), (x + obj_w, y + obj_h), color, 2)
        #cv2.rectangle(image, (x, y), (x + obj_w, y + obj_h), color, -1)

    return image

############################################################
# STEP 3: Main demonstration
############################################################
def main():
    image_path = "../floor_plans/fp2_enhanced.png"  # Change to the path of your plan

    # 1. Vectorize
    walls, objs = vectorize_floorplan(
        image_path,
        invert=False,         # Set True if your lines are white on black
        morph_kernel_size=3,  # 0 for no morphological ops
        canny_threshold1=30,
        canny_threshold2=100,
        hough_threshold=30,
        min_line_length=20,
        max_line_gap=5
    )

    # 2. Draw on a blank canvas
    canvas = draw_floorplan(walls, objs, canvas_size=(1800, 1800))

    # 3. Show the result
    cv2.imshow("Vectorized Floorplan", canvas)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
