import cv2
import numpy as np
from itertools import combinations
from data_clenser import DataClenser
from pygame_floor_display import FloorDisplay


def compute_wall_rectangle(start, end, width):
    x1 = start[0]
    y1 = start[1]
    x2 = end[0]
    y2 = end[1]
    """
    Computes the axis-aligned rectangle that represents a thick wall.

    :param x1, y1: Start point of the wall
    :param x2, y2: End point of the wall
    :param width: Thickness of the wall
    :return: (top-left corner, bottom-right corner) for cv2.rectangle
    """
    if abs(x1 - x2) > 1:  # Vertical Wall
        min_x = x1 - width // 2
        max_x = x1 + width // 2
        min_y = min(y1, y2)
        max_y = max(y1, y2)

    elif abs(y1 - y2)>1:  # Horizontal Wall
        min_x = min(x1, x2)
        max_x = max(x1, x2)
        min_y = y1 - width // 2
        max_y = y1 + width // 2

    else:
        raise ValueError("All walls should be strictly horizontal or vertical!")

    return (min_x, min_y), (max_x, max_y)
def detect_lines_and_rectangles(
    image_path,
    invert=False,
    canny_threshold1=10,
    canny_threshold2=60,
    hough_threshold=15,
    min_line_length=3,
    max_line_gap=20,
    angle_tolerance_deg=10.0
):
    """
    1) Loads the original floor plan in color (BGR).
    2) Creates a grayscale copy for Canny + Hough line detection (no erosion).
    3) Also uses threshold + contours to detect rectangular objects (outline only, no fill).
    4) Draws everything on the original plan so you see all lines.
    """
    # 1. Load the original image (color) for final drawing
    original_color = cv2.imread(image_path)
    if original_color is None:
        raise FileNotFoundError(f"Could not load image: {image_path}")

    # 2. Convert to grayscale for edge detection
    gray = cv2.cvtColor(original_color, cv2.COLOR_BGR2GRAY)

    # Optionally invert if lines are white on black
    if invert:
        gray = cv2.bitwise_not(gray)

    # 3. Threshold (so black = walls, white = background/room)
    _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)

    # 4. Canny edge detection (no morphological ops)
    edges = cv2.Canny(binary, canny_threshold1, canny_threshold2)

    # 5. Probabilistic Hough Transform to detect line segments
    lines_p = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi / 180,
        threshold=hough_threshold,
        minLineLength=min_line_length,
        maxLineGap=max_line_gap
    )

    wall_vectors = []
    id = 0
    # 6. Draw detected lines on the color image (with no fill anywhere)
    #    We'll just use black lines for these Hough segments, or any color you want.
    if lines_p is not None:
        for line in lines_p:
            x1, y1, x2, y2 = line[0]
            # Compute angle in degrees relative to horizontal
            dx, dy = (x2 - x1), (y2 - y1)
            angle_degs = abs(np.degrees(np.arctan2(dy, dx)))
            # Make sure angle is in [0..180]
            if angle_degs < 0:
                angle_degs += 180

            # Filter out lines if the angle is not near 0/90/180 within tolerance
            # We'll check near 0 or near 90 or near 180
            def within_tolerance(a, center, tol):
                    return abs(a - center) <= tol

            if (within_tolerance(angle_degs, 0, angle_tolerance_deg) or
                    within_tolerance(angle_degs, 90, angle_tolerance_deg) or
                    within_tolerance(angle_degs, 180, angle_tolerance_deg)):
                # Keep this line
                wall_width = 3  # guessed width
                wall_vectors.append({
                    "start": (x1, y1),
                    "end": (x2, y2),
                    "width": wall_width,
                    "id": id
                })
                id = id + 1
            #cv2.line(original_color, (x1, y1), (x2, y2), (0, 0, 255), 2)
            middle = tuple((s + e) / 2 for s, e in zip((x1, y1), (x2, y2)))
            middle_i = (int(middle[0]+8), int(middle[1]+8))
            text = str(id)
            font = cv2.FONT_HERSHEY_SIMPLEX
            #cv2.putText(original_color, text, middle_i, font, .5, (0, 0, 0), 1, cv2.LINE_AA)

    wall_vectors_1 = DataClenser.unify_close_parallel_lines2(wall_vectors,angle_thresh_deg=5.0,
            dist_thresh=10.0,
            thick_width=15 )

    for wall in wall_vectors:
        start = wall["start"]
        end = wall["end"]
        width = wall["width"]
        start_i = (int(start[0]), int(start[1]))
        end_i =(int(end[0]+width), int(end[1]))
        try:
            si, ei = compute_wall_rectangle(start_i,end_i,width)
            #cv2.rectangle(original_color,si,ei , (250, 150, 155), int(1))
            font = cv2.FONT_HERSHEY_SIMPLEX
            middle = tuple((s + e) / 2 for s, e in zip(start, end))
            middle_i = (int(middle[0]),int(middle[1]))
            text = str(wall["id"])
            #cv2.putText(original_color, text, middle_i, font, .4, (0,255,0), 1, cv2.LINE_AA)
        except Exception as e:
            print(f"Something went wrong: {e}")

    fd = FloorDisplay()
    fd.display(wall_vectors,wall_vectors_1, original_color)

    # 7. (Optional) detect rectangular shapes (like doors/windows) using contours
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        approx = cv2.approxPolyDP(cnt, 0.02 * cv2.arcLength(cnt, True), True)
        if len(approx) == 4:  # treat 4-corner shapes as rectangles
            x, y, w, h = cv2.boundingRect(approx)
            # Outline-only rectangle in green, thickness=2
            cv2.rectangle(original_color, (x, y), (x + w, y + h), (0, 255, 0), 2)

    return original_color

def main():
    image_path = "w1024.jpg"  # Adjust to your floor plan
    # Detect and draw lines (no fill) on top of the original image
    result = detect_lines_and_rectangles(
        image_path,
        invert=False,        # Set True if walls are white on black
        canny_threshold1=30,
        canny_threshold2=100,
        hough_threshold=30,
        min_line_length=20,
        max_line_gap=5
    )

    # Show
    cv2.imshow("Floor Plan with Detected Lines (No Fill)", result)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
