from shapely import LineString
from floor_plan_reader.line import Line


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

    def build_lines_and_intersections(self, collision_boxes):

        # STEP 1: Build list of lines

        for i, seg in enumerate(collision_boxes):
            cb = seg.collision_box_extended
            if cb is not None:
                line_id = f"L{i + 1}"
                seg_id = seg.id
                (x1, y1), (x2, y2) = cb.get_center_line()
                line_obj = LineString([(x1, y1), (x2, y2)])  # Shapely geometry
                self.create_line(line_id, seg, (x1, y1), (x2, y2), line_obj)
        merge_candidates =[]
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
                    node = self.world.create_node((ix, iy))
                    node.lines = [lineA.id, lineB.id]
                    angle_dif = lineA.seg.collision_box.rotation-lineB.seg.collision_box.rotation
                    if abs(angle_dif) < 30:
                        merge_candidates.append({"a": lineA.id, "b": lineB.id})
                        continue
                    lineA.seg.add_node(node)
                    lineB.seg.add_node(node)
                    intersections.add(node)
                elif inter.geom_type == "MultiPoint":
                    # Possibly multiple intersection points
                    for pt in inter.geoms:
                        node = self.world.create_node((pt.x, pt.y))
                        node.lines = [lineA.id, lineB.id]
                        intersections.add(node)
                        lineA.seg.add_node(node)
                        lineB.seg.add_node(node)
                elif inter.geom_type == "LineString":
                    # Overlapping line segments
                    # If you want just endpoints, can do something like:
                    coords = list(inter.coords)
                    # Example: store them or skip
                    # We'll store each coordinate as a separate intersection:
                    for (ix, iy) in coords:
                        node = self.world.create_node((ix, iy))
                        node.lines = [lineA.id, lineB.id]
                        angle_dif = lineA.seg.collision_box.rotation - lineB.seg.collision_box.rotation
                        if abs(angle_dif) < 30:
                            continue
                        intersections.add(node)
                        lineA.seg.add_node(node)
                        lineB.seg.add_node(node)
                # else: handle other geometry types if needed (Polygon, MultiLineString, etc.)

        return {
            "lines": line_list,
            "intersections": list(intersections),
            "merge_candidates": merge_candidates
        }
