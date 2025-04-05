############################################################
import cv2
import numpy as np
from torch import combinations

from data_clenser import DataClenser
# STEP 3B: Draw & overlay color-coded lines
############################################################
def draw_floorplan_with_overlay(vectors, objects, canvas_size=(800, 800)):
        """
        Draw the lines in color by type (exterior -> red, interior -> green).
        Mark endpoints in blue, intersections in yellow, rectangles in gray.
        """
        w, h = canvas_size
        image = np.ones((h, w, 3), dtype=np.uint8) * 255

        for vec in vectors:
            (x1, y1) = vec["start"]
            (x2, y2) = vec["end"]
            # color-code
            if vec["width"] >= 10:
                color = (0, 0, 255)  # red for exterior
            else:
                color = (0, 200, 0)  # green for interior
            cv2.line(image, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)


            # endpoints in blue
            #cv2.circle(image, (int(x1), int(y1)), radius, color, thickness)
            cv2.circle(image, (int(x1), int(y1)), 4, (255, 0, 0), -1)
            cv2.circle(image, (int(x2), int(y2)), 4, (255, 0, 0), -1)

        # rectangles
        for obj in objects:
            x, y = obj["position"]
            ww, hh = obj["width"], obj["height"]
            #cv2.rectangle(image, (x, y), (x + ww, y + hh), (128, 128, 128), 2)
            corners = [(x, y), (x + ww, y), (x, y + hh), (x + ww, y + hh)]
            for (cx, cy) in corners:
                cv2.circle(image, (cx, cy), 4, (255, 0, 0), -1)

        # intersections in yellow
        intersections = set()
        for v1, v2 in combinations(vectors, 2):
            p1, p2 = v1["start"], v1["end"]
            p3, p4 = v2["start"], v2["end"]
            inter = DataClenser.line_segment_intersection(p1, p2, p3, p4)
            if inter is not None:
                ix, iy = map(int, inter)
                intersections.add((ix, iy))

        for (ix, iy) in intersections:
            cv2.circle(image, (ix, iy), 5, (0, 255, 255), -1)

        return image



def draw_graph(graph, image):
        """
        Draws the given 'graph' on a blank canvas:
          - 'exterior' edges -> blue lines
          - 'interior' edges -> green lines
          - all node points -> yellow circles

        graph format:
          {
            "nodes": [
              { "id": "N1", "x": 100, "y": 100 },
              { "id": "N2", "x": 200, "y": 100 },
              ...
            ],
            "edges": [
              { "id": "E1", "start_node": "N1", "end_node": "N2", "wall_type": "exterior" },
              { "id": "E2", "start_node": "N2", "end_node": "N3", "wall_type": "interior" },
              ...
            ]
          }
        """


        # 1) Create a dict of node positions: { node_id: (x, y) }
        node_positions = {}
        for node in graph["nodes"]:
            node_id = node["id"]
            x = int(round(node["x"]))
            y = int(round(node["y"]))
            node_positions[node_id] = (x, y)

        # 2) Draw edges
        for edge in graph["edges"]:
            start_id = edge["start_node"]
            end_id = edge["end_node"]
            wall_type = edge.get("wall_type", "interior")  # default if missing

            if start_id not in node_positions or end_id not in node_positions:
                # In case of invalid references, skip
                continue

            (x1, y1) = node_positions[start_id]
            (x2, y2) = node_positions[end_id]

            if wall_type.lower() == "exterior":
                color = (255, 0, 0)   # Blue (BGR)
            else:
                color = (0, 255, 0)   # Green (BGR)

            #cv2.line(image, (x1, y1), (x2, y2), color, 2)

        # 3) Draw nodes as yellow circles
        for (node_id, (x, y)) in node_positions.items():
            #cv2.circle(image, (x, y), 4, (0, 255, 255), -1)  # Yellow
            pass