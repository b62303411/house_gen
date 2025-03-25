import cv2
import numpy as np
import math
from itertools import combinations
import json

############################################################
# STEP 0: Merge or Thicken Parallel Lines
############################################################
class DataClenser:


    @staticmethod
    def unify_close_parallel_lines2(vectors,
                                   angle_thresh_deg=5.0,
                                   dist_thresh=10.0,
                                   thick_width=15):
        """
        Merges only if lines are near horizontal or vertical,
        and they overlap on their main axis by a minimum length
        (we skip any lines that are angled or do not share a big enough overlap).

        :param vectors: list of { 'start':(x1,y1), 'end':(x2,y2), 'width':val }
        :param angle_thresh_deg: how close to 0 or 90 to treat as purely horizontal/vertical
        :param dist_thresh: how close lines can be in the minor axis to be considered the same
        :param thick_width: ignored to keep the function signature
        :return: new list with merged lines
        """
        # For each line, store a normalized representation
        lines_info = []
        for v in vectors:
            (x1, y1) = v["start"]
            id = v["id"]
            (x2, y2) = v["end"]
            dx, dy = (x2 - x1), (y2 - y1)
            angle_deg = math.degrees(math.atan2(dy, dx))
            length = math.hypot(dx, dy)

            # normalize angle to [0..180)
            if angle_deg < 0:
                angle_deg += 180

            # We'll classify lines as near-horizontal if angle in [0 ± angle_thresh] or [180 ± angle_thresh],
            # or near-vertical if angle in [90 ± angle_thresh].
            # We'll store: orientation = 'H' or 'V' or 'NONE' if it doesn't meet either criterion.
            orientation = 'NONE'
            if abs(angle_deg - 0) <= angle_thresh_deg or abs(angle_deg - 180) <= angle_thresh_deg:
                orientation = 'H'
            elif abs(angle_deg - 90) <= angle_thresh_deg:
                orientation = 'V'

            # bounding box (for overlap checks)
            xmin, xmax = (min(x1, x2), max(x1, x2))
            ymin, ymax = (min(y1, y2), max(y1, y2))

            lines_info.append({
                "start": (x1, y1),
                "end": (x2, y2),
                "orientation": orientation,  # 'H' or 'V' or 'NONE'
                "xmin": xmin, "xmax": xmax,
                "ymin": ymin, "ymax": ymax,
                "length": length,
                "id": id
            })

        merged_something = True
        while merged_something:
            merged_something = False
            new_list = []
            used = [False] * len(lines_info)

            for i in range(len(lines_info)):
                if used[i]:
                    continue
                A = lines_info[i]
                if A["orientation"] not in ['H', 'V']:
                    # We won't merge angled lines, just keep as is
                    used[i] = True
                    new_list.append(A)
                    continue

                best_j = -1
                merged_line = None

                for j in range(i + 1, len(lines_info)):
                    if used[j]:
                        continue
                    B = lines_info[j]
                    # must have same orientation to even consider merging
                    if B["orientation"] != A["orientation"]:
                        continue

                    if A["orientation"] == 'H':
                        # near horizontal -> check if y-ranges are close,
                        # and x-intervals overlap by enough
                        yA = (A["ymin"] + A["ymax"]) / 2.0  # mid-Y
                        yB = (B["ymin"] + B["ymax"]) / 2.0
                        if abs(yA - yB) <= dist_thresh:
                            # check overlap in x
                            # A has x-range [A['xmin'], A['xmax']]
                            # B has x-range [B['xmin'], B['xmax']]
                            overlap = min(A["xmax"], B["xmax"]) - max(A["xmin"], B["xmin"])
                            if overlap > 0:  # there's some overlap
                                # if the overlap is big enough to unify lines, pick a threshold
                                if overlap >= 10:  # e.g. at least 10 px
                                    # merge => the new line covers the union of X
                                    new_xmin = min(A["xmin"], B["xmin"])
                                    new_xmax = max(A["xmax"], B["xmax"])
                                    # y is the average or any consistent
                                    new_y = (yA + yB) / 2.0
                                    merged_line = {
                                        "start": (new_xmin, new_y),
                                        "end": (new_xmax, new_y),
                                        "orientation": 'H',
                                        "xmin": new_xmin,
                                        "xmax": new_xmax,
                                        "ymin": new_y,
                                        "ymax": new_y,
                                        "length": new_xmax - new_xmin,
                                        "id": str(A["id"])+"_"+str(B["id"]),
                                        "id_a": A["id"],
                                        "id_b": B["id"],
                                        "width": abs(yA - yB)
                                    }
                                    best_j = j
                                    break

                    elif A["orientation"] == 'V':
                        # near vertical -> check if x-ranges are close,
                        # and y-intervals overlap enough
                        xA = (A["xmin"] + A["xmax"]) / 2.0
                        xB = (B["xmin"] + B["xmax"]) / 2.0
                        if abs(xA - xB) <= dist_thresh:
                            # check overlap in y
                            overlap = min(A["ymax"], B["ymax"]) - max(A["ymin"], B["ymin"])
                            if overlap > 0:
                                if overlap >= 10:  # must have some minimal overlap
                                    new_ymin = min(A["ymin"], B["ymin"])
                                    new_ymax = max(A["ymax"], B["ymax"])
                                    new_x = (xA + xB) / 2.0
                                    id_a = A["id"]
                                    id_b = B["id"]
                                    merged_line = {
                                        "start": (new_x, new_ymin),
                                        "end": (new_x, new_ymax),
                                        "orientation": 'V',
                                        "xmin": new_x,
                                        "xmax": new_x,
                                        "ymin": new_ymin,
                                        "ymax": new_ymax,
                                        "length": new_ymax - new_ymin,
                                        "id": str(A["id"])+"_"+str(B["id"]),
                                        "id_a": id_a,
                                        "id_b": id_b,
                                        "width": abs(xA - xB)}
                                    best_j = j
                                    break

                if best_j >= 0 and merged_line is not None:
                    used[i] = True
                    used[best_j] = True
                    new_list.append(merged_line)
                    merged_something = True
                else:
                    used[i] = True
                    new_list.append(A)

            lines_info = new_list

        # convert back to the original data format
        final = []
        for ln in lines_info:
            x1, y1 = ln["start"]
            x2, y2 = ln["end"]
            if "width" in ln:
                width = ln["width"]
            else:
                width = 5

            if "id_a" in ln:
                id_a = ln["id_a"]
                id_b = ln["id_b"]
            else:
                id_a = "N/A"
                id_b = "N/A"

            final.append({
                "start": (x1, y1),
                "end": (x2, y2),
                "width": width,
                "id": ln["id"],
                "id_a": id_a,
                "id_b":  id_b,

            })
        return final




    ############################################################
    # STEP 1: Vectorize the floor plan
    ############################################################
    def vectorize_floorplan(
        image_path,
        invert=False,
        morph_kernel_size=5,
        canny_threshold1=15,
        canny_threshold2=80,
        hough_threshold=20,
        min_line_length=20,
        max_line_gap=5
    ):
        gray = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if gray is None:
            raise FileNotFoundError(f"Could not load image: {image_path}")

        if invert:
            gray = cv2.bitwise_not(gray)

        # Threshold
        _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)

        # Erode thick walls
        if morph_kernel_size > 0:
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (morph_kernel_size, morph_kernel_size))
            binary = cv2.erode(binary, kernel, iterations=1)

        # Canny edge detection
        edges = cv2.Canny(binary, canny_threshold1, canny_threshold2)

        # Probabilistic Hough
        lines_p = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi/180,
            threshold=hough_threshold,
            minLineLength=min_line_length,
            maxLineGap=max_line_gap
        )

        wall_vectors = []
        if lines_p is not None:
            for line in lines_p:
                x1, y1, x2, y2 = line[0]
                wall_width = 5
                wall_vectors.append({
                    "start": (x1, y1),
                    "end": (x2, y2),
                    "width": wall_width
                })

        # Thicken close parallel lines => exterior
        # unify parallel lines => single segments
        wall_vectors = DataClenser.unify_close_parallel_lines(
            wall_vectors,
            angle_thresh_deg=5.0,
            dist_thresh=3.0,
            thick_width=15  # not used
        )

        # Detect rectangles
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        objects = []
        for cnt in contours:
            approx = cv2.approxPolyDP(cnt, 0.02 * cv2.arcLength(cnt, True), True)
            if len(approx) == 4:
                x, y, w, h = cv2.boundingRect(approx)
                obj_type = "door/window" if max(w, h) < 100 else "large_feature"
                objects.append({
                    "position": (x, y),
                    "width": w,
                    "height": h,
                    "type": obj_type
                })

        return wall_vectors, objects

    ############################################################
    # HELPER: line-line intersection
    ############################################################
    def line_segment_intersection(p1, p2, p3, p4, epsilon=1e-9):
        x1, y1 = p1
        x2, y2 = p2
        x3, y3 = p3
        x4, y4 = p4

        a1 = y2 - y1
        b1 = x1 - x2
        c1 = a1*x1 + b1*y1

        a2 = y4 - y3
        b2 = x3 - x4
        c2 = a2*x3 + b2*y3

        det = a1*b2 - a2*b1
        if abs(det) < epsilon:
            return None

        x = (b2*c1 - b1*c2)/det
        y = (a1*c2 - a2*c1)/det

        def within_segment(px, py, ax, ay, bx, by):
            return (
                min(ax, bx)-epsilon <= px <= max(ax, bx)+epsilon and
                min(ay, by)-epsilon <= py <= max(ay, by)+epsilon
            )

        if (
            within_segment(x, y, x1, y1, x2, y2) and
            within_segment(x, y, x3, y3, x4, y4)
        ):
            return (x, y)
        return None





    ############################################################
    # STEP 4: Main function
    ############################################################
    @staticmethod
    def main():
        image_path = "../floor_plans/w1024.jpg"

        # 1. Vectorize
        walls, objs = DataClenser.vectorize_floorplan(
            image_path,
            invert=False,
            morph_kernel_size=5,
            canny_threshold1=15,
            canny_threshold2=80,
            hough_threshold=20,
            min_line_length=20,
            max_line_gap=5
        )

        # 2. Generate the graph metadata
        graph_data = DataClenser.generate_graph(walls)
        # Print it or save to JSON
        #json_str = json.dumps(graph_data, indent=2)
        #print("Generated Graph Data:\n", json_str)

        # 3. Draw color-coded overlay
        canvas = DataClenser.draw_floorplan_with_overlay(walls, objs, canvas_size=(1800, 1800))
        #draw_graph(graph_data,canvas)
        # 4. Show result
        cv2.imshow("Floorplan Overlay", canvas)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

if __name__ == "__main__":
    pass
    #main()
