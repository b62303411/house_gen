import itertools

from floor_plan_reader.model.line import Line


class IntersectionSolver:
    def __init__(self, world):
        self.world = world
        self.lines = {}

    # line_id,seg,(x1, y1),(x2, y2),line_obj
    def create_line(self, id, seg, start_point, end_point, geometry):
        l = Line(start_point, end_point, id, seg, geometry)
        if l in self.lines:
            return self.lines.get(l.__hash__())
        else:
            self.lines[l.__hash__()] = l
            return l

    def propose_edge(self, line):
        nodes = list(line.seg.nodes)
        if len(nodes) < 2:
            return  # not enough nodes to form an edge

        # Find the pair of nodes with the maximum distance between them
        max_dist = -1
        node1, node2 = None, None

        for a, b in itertools.combinations(nodes, 2):  # all pairs
            ax, ay = a.point
            bx, by = b.point
            dist_sq = (ax - bx) ** 2 + (ay - by) ** 2  # squared distance (faster)
            if dist_sq > max_dist:
                max_dist = dist_sq
                node1, node2 = a, b
        # Create the edge between the furthest-apart nodes
        self.world.create_edge(node1, node2, line)
    def something(self, merge_candidates, intersections, lineA, lineB, intersection_coordinate):
        (x, y) = intersection_coordinate

        angle_dif = lineA.seg.collision_box.rotation - lineB.seg.collision_box.rotation
        if abs(angle_dif) < 30:
            merge_candidates.append({"a": lineA.id, "b": lineB.id})
        else:
            node = self.world.create_node((x, y))
            node.lines = [lineA.id, lineB.id]
            intersections.add(node)
            lineA.seg.add_node(node)
            lineB.seg.add_node(node)
            self.propose_edge(lineA)
            self.propose_edge(lineB)

    def build_lines_and_intersections(self, collision_boxes):

        # STEP 1: Build list of lines

        for i, seg in enumerate(collision_boxes):
            cb = seg.collision_box_extended
            if cb is not None:
                line_id = f"L{i + 1}"
                seg_id = seg.id
                line_obj = cb.get_center_line_string()  # Shapely geometry
                x1, y1, x2, y2 = line_obj.bounds
                self.create_line(line_id, seg, (x1, y1), (x2, y2), line_obj)
        merge_candidates = []
        # STEP 2: Pairwise intersections
        intersections = set()
        n = len(self.lines)
        line_list = list(self.lines.values())
        for i in range(n):
            for j in range(i + 1, n):
                lineA = line_list[i]
                lineB = line_list[j]

                inter = lineA.geometry.intersection(lineB.geometry)
                if inter.is_empty:
                    continue

                # Check intersection type
                if inter.geom_type == "Point":
                    # Single-point intersection
                    ix, iy = inter.x, inter.y
                    self.something(merge_candidates, intersections, lineA, lineB, (ix, iy))
                elif inter.geom_type == "MultiPoint":
                    # Possibly multiple intersection points
                    for pt in inter.geoms:
                        self.something(merge_candidates, intersections, lineA, lineB, (pt.x, pt.y))
                elif inter.geom_type == "LineString":
                    # Overlapping line segments
                    # If you want just endpoints, can do something like:
                    coords = list(inter.coords)
                    # Example: store them or skip
                    # We'll store each coordinate as a separate intersection:
                    for (ix, iy) in coords:
                        self.something(merge_candidates, intersections, lineA, lineB, (ix, iy))
                # else: handle other geometry types if needed (Polygon, MultiLineString, etc.)
            for line in self.lines.values():
                self.propose_edge(line)
        return {
            "lines": line_list,
            "intersections": list(intersections),
            "edges": list(self.world.edges.values()),
            "merge_candidates": merge_candidates
        }
