import logging
import math
from decimal import Decimal
from itertools import combinations

import pygame
from pygame import font
from shapely import Point, LineString

from floor_plan_reader.agents.agent import Agent
from floor_plan_reader.display.bounding_box_drawer import BoundingBoxDrawer
from floor_plan_reader.math.collision_box import CollisionBox
from floor_plan_reader.math.vector import Vector
from floor_plan_reader.model.opening import Opening
from floor_plan_reader.pruning_util import PruningUtil
from shapely.affinity import rotate
from shapely.geometry import Point, LineString


class Scores:
    def __init__(self, id, score):
        self.id = id
        self.score = score

    def __eq__(self, other):
        if not isinstance(other, Scores):
            return False
        return self.id == other.id

    def __hash__(self):
        return hash(id)


class WallSegment(Agent):

    def __init__(self, agent_id, world):
        super().__init__(agent_id)
        self.collision_box = None
        self.collision_box_extended = None
        self.world = world
        self.scores = set()
        self.parts = set()
        self.set_collision_box(CollisionBox(0, 0, 1, 1, 0))  # Will be set after ray trace
        self.alive = True
        self.state = "idle"
        font.init()
        self.f = font.Font(None, 8)
        self.openings = set()
        self.overlapping = set()
        self.nodes = set()
        self.cb_drawer = BoundingBoxDrawer()
        self.wall_dic = {}

    def __hash__(self):
        return hash(self.id)

    def add_node(self, node):
        self.nodes.add(node)

    def set_collision_box(self, cb):
        if isinstance(cb, CollisionBox):
            self.collision_box = cb.copy()

    def add_part(self, part):
        self.wall_dic[part.id] = part
        self.parts.add(part)
        self.state = "negotiate"

    def run(self):
        self.process_state()

    def is_selected(self):
        for p in self.parts:
            if p.selected:
                return True
        return False

    def merge(self, seg):
        for p in seg.parts:
            p.wall_scanner = self
            self.add_part(p)
        for n in seg.nodes:
            self.add_node(n)

    def set_position(self, x, y):
        self.collision_box.set_position(x, y)

    def calculate_if_external(self):
        pass

    def dot2(self, ax, ay, bx, by):
        """2D dot product."""
        return ax * bx + ay * by

    def length2(self, ax, ay):
        """2D vector length."""
        return math.sqrt(ax * ax + ay * ay)

    def _validate_part_within_parent(self, part, tolerance=2):

        parent_line = self.collision_box_extended.get_center_line_string()
        parent_coords = parent_line.coords
        start = Point(parent_coords[0])
        end = Point(parent_coords[-1])
        center = Point(
            (start.x + end.x) / 2,
            (start.y + end.y) / 2
        )

        max_allowed_distance = center.distance(start) + tolerance

        part_line = part.collision_box.get_center_line_string()
        for x, y in part_line.coords:
            p = Point(x, y)
            d = p.distance(center)
            if d > max_allowed_distance:
                raise ValueError(
                    f"Point ({x:.2f}, {y:.2f}) of child is too far from parent center "
                    f"(distance {d:.2f} > max {max_allowed_distance:.2f})"
                )

    def get_sorted_lines(self):

        class Sortable:
            def __init__(self, line, dist):
                self.line = line
                self.dist = dist

            # Needed so that a_list.sort() knows how to compare two Sortable objects
            def __lt__(self, other):
                return self.dist < other.dist

        # 1) The line for the entire wall (or overall bounding shape):
        center_line = self.collision_box_extended.get_center_line_string()
        # 2) Grab the first coordinate as our reference "start" point.
        #    (Alternatively, you could choose the midpoint, or something else
        #     that represents the "anchor" point of your main geometry.)
        ref_start_x, ref_start_y = center_line.coords[0]
        ref_start = Point(ref_start_x, ref_start_y)

        a_list = []
        for p in self.parts:

            candidate = p.collision_box.get_center_line_string()

            # --- Instead of using center_line.bounds, use candidate.bounds ---
            c_bounds = candidate.bounds
            candidate_start = Point(c_bounds[0], c_bounds[1])
            candidate_end = Point(c_bounds[2], c_bounds[3])

            if p.collision_box.rotation != self.collision_box.rotation:
                logging.debug(f"{p.collision_box.rotation} vs {self.collision_box.rotation}")

            # Distances from our reference_start to the candidate's two endpoints
            dist_start = ref_start.distance(candidate_start)
            dist_end = ref_start.distance(candidate_end)

            # If the “start” is actually further away than the “end,”
            # that implies we might want to flip/reverse the line so
            # it consistently starts from the side that’s closer to ref_start.

            # As-is is okay
            a_list.append(Sortable(candidate, dist_start))

        # Sort by the stored distance
        a_list.sort()

        # Return just the lines, now sorted from closest to farthest
        return [sortable.line for sortable in a_list]

    def project_along_wall_direction(self, vec_to_point, wall_direction):
        """
        Projects the vector `vec_to_point` onto the `wall_direction`.

        Both should be instances of your Vector class.
        Assumes `wall_direction` is already normalized.
        Returns a scalar (float): the signed distance along the wall's axis.
        """
        return vec_to_point.dot_product(wall_direction)

    def calculate_openings(self):

        if len(self.parts) < 2:
            return
        if not self.is_segment_fully_occupied():
            self.print_occupancy()
            parts = self.parts.copy()
            for p in parts:
                p.re_compute()
                p.performe_ray_trace(self.collision_box.get_direction())
                p.absorb_bleading_out()
                p.fill_box()
                p.crawl_phase()
            return
        self.openings = set()

        center_lines = self.get_sorted_lines()
        center = self.get_center()
        center_p = Point(center)
        for i in range(len(center_lines) - 1):
            current_line = center_lines[i]

            # End of line i
            end_i = center_lines[i].coords[-1]

            # Start of line i+1
            start_i1 = center_lines[i + 1].coords[0]
            end = Point(end_i)
            start = Point(start_i1)

            # Midpoint
            mid_x = (end.x + start.x) / 2
            mid_y = (end.y + start.y) / 2
            mid_point = Point(mid_x, mid_y)
            vec_to_mid = Vector((mid_point.x - center_p.x, mid_point.y - center_p.y))
            direction = self.collision_box.get_direction()
            offset = self.project_along_wall_direction(vec_to_mid, direction)
            # offset = mid_point.distance(center_p)
            # Euclidean distance between these two points
            gap_distance = end.distance(start)
            print(f"Gap = {gap_distance:.2f}")
            o = Opening(offset, gap_distance)
            self.add_opening(o)

        return self.openings

    def is_segment_fully_occupied(self):
        """
        Validates whether the full axis of a wall segment is covered by its collision boxes.

        Args:
            segment (List[CollisionBox]): List of aligned boxes forming a wall segment.
            world: The world object with a method `is_occupied(x, y)` -> bool

        Returns:
            bool: True if the full axis is covered, False if there are any gaps.
        """

        direction, _ = self.collision_box.derive_direction_and_normal()
        dx, dy = direction.direction

        # Project all start/end points to get full coverage range
        projections = []
        for cb in self.parts:
            p1, p2 = cb.collision_box.get_center_line()
            projections.extend([
                (p1[0], p1[1]),
                (p2[0], p2[1])
            ])

        # Sort all by projection along wall axis
        def project(pt):
            return pt[0] * dx + pt[1] * dy

        projections = sorted(projections, key=project)

        start_pt = projections[0]
        end_pt = projections[-1]

        # Step along wall axis pixel by pixel
        distance = int(math.hypot(end_pt[0] - start_pt[0], end_pt[1] - start_pt[1]))
        for i in range(distance + 1):
            x = int(round(start_pt[0] + dx * i))
            y = int(round(start_pt[1] + dy * i))
            if self.world.is_food(x, y) and not self.world.is_occupied(x, y):
                for p in self.parts:
                    if p.collidepoint(x, y):
                        logging.error("wtf")
                logging.info("not fully compliant")
                return False  # There's a gap

        return True

    def print_occupancy(self):
        center = self.get_center()
        width = 250
        height = 250
        x = center[0]
        y = center[1]
        self.world.print_occupancy_status(x, y, width + 2, height + 2, self.id)

    def print_snapshot(self):
        center = self.get_center()
        width = 250
        height = 250
        x = center[0]
        y = center[1]
        self.world.print_snapshot(x, y, width + 2, height + 2, self.id)

    def add_opening(self, o):
        if o.width > 120:
            logging.info("wtf")
            self.print_snapshot()
        self.openings.add(o)

    def merge_alighned(self, cb, p):
        if isinstance(cb, CollisionBox):
            cb = cb.merge_aligned(p.collision_box)
        return cb

    def negotiate(self):
        cb = None
        for p in self.parts:
            ratio = p.get_covered_ratio()
            s = Scores(p.id, ratio)
            self.scores.add(s)
            if cb is None:
                cb = p.collision_box.copy()
            else:
                cb = self.merge_alighned(cb, p)

        self.set_collision_box(cb)

    def fitting_phase(self):
        self.state="opening"
        return
        self.recalculate_parent_box_from_parts()
        self.calculate_extended_bounding_box()

        if self.is_segment_fully_occupied():
            for p in self.parts:
                try:
                    self._validate_part_within_parent(p)
                except:
                    logging.error("")
                    return
            self.state = "opening"

    def negotiate_phase(self):
        self.negotiate()
        error = False
        for n in self.parts:
            if self.collision_box.width > 2 * n.collision_box.width or self.collision_box.width > 100:
                error = True
                break
        if error:
            self.state = "error"
        else:
            self.state = "prune"
        return

    def prune_phase(self):
        pruned, against = PruningUtil.prune(self, self.world.wall_segments)
        if pruned:
            #    for p in self.parts:
            #        p.wall_segment = against
            #        against.add_part(p)
            self.state = "dead"
        else:
            self.state = "normalize"

    def calculate_extended_bounding_box(self):
        h, w = self.world.get_shape()
        points_forward, points_backward = self.collision_box.get_extended_ray_trace_points(w, h)
        steps_backward, bx, by = self.crawl(points_backward)
        steps_forward, fx, fy = self.crawl(points_forward)
        self.collision_box_extended = self.collision_box.copy()

        if steps_forward > 1 or steps_backward > 1:
            extension = steps_backward + steps_forward
            l = self.collision_box_extended.length
            self.collision_box_extended.set_length(l + extension + 2)
            if steps_forward > steps_backward:
                (bx1, by1), (bx2, by2) = self.collision_box_extended.get_center_line()
                self.collision_box_extended.move_forward(abs(steps_backward - steps_forward) / 2)
                (x1, y1), (x2, y2) = self.collision_box_extended.get_center_line()
                id_start = self.world.get_occupied_id(x1, y1)
                id_end = self.world.get_occupied_id(x2, y2)
                if id_start in self.wall_dic and id_end in self.wall_dic:
                    if steps_forward > 1 or steps_backward > 1:
                        logging.info("error")

            else:
                self.collision_box_extended.move_backward(abs(steps_backward - steps_forward) / 2)
                (x1, y1), (x2, y2) = self.collision_box_extended.get_center_line()
                id_start = self.world.get_occupied_id(x1, y1)
                id_end = self.world.get_occupied_id(x2, y2)
                if id_start in self.wall_dic and id_end in self.wall_dic:
                    if steps_forward > 1 or steps_backward > 1:
                        logging.info("error")

        logging.info(f"steps b{steps_backward} steps f{steps_forward}")

    def crawl(self, points):
        steps = 0
        x, y = 0, 0
        measuring_extent = False
        if points is None:
            raise Exception
        for p in points:
            x = int(p[0])
            y = int(p[1])
            if self.world.is_food(x, y):
                id = self.world.get_occupied_wall_id(x, y)
                if id != self.id:
                    measuring_extent = True
                if measuring_extent:
                    steps = steps + 1
            else:
                return steps, x, y

        return steps, x, y

    def recalculate_parent_box_from_parts(self):
        if not self.parts:
            raise ValueError("Cannot recalculate extent without parts.")
        line_strings = self.get_sorted_lines()

        endpoints = []
        for line in line_strings:
            coords = list(line.coords)
            endpoints.append(Point(coords[0]))
            endpoints.append(Point(coords[-1]))

        max_dist = -1
        max_pair = (None, None)

        for p1, p2 in combinations(endpoints, 2):
            dist = p1.distance(p2)
            if dist > max_dist:
                max_dist = dist
                max_pair = (p1, p2)

        width = self.collision_box.width
        center_line = LineString([max_pair[0], max_pair[1]])
        self.collision_box = CollisionBox.create_from_line(center_line, width)

    def process_state(self):

        wrongs = []
        if self.state == "error":
            for n in self.parts:
                for i in self.parts:
                    if not n.collision_box.is_on_same_axis_as(i.collision_box):
                        wrongs.append(i)
                logging.debug("error")
            return
        if self.state == "negotiate":
            self.negotiate_phase()
            return
        elif self.state == "prune":
            self.prune_phase()
            return
        elif self.state == "normalize":
            self.normalize()
            self.state = "fill"
            return
        elif self.state == "fill":
            self.fill_box()
            self.state = "extend"
            return
        elif self.state == "extend":
            self.calculate_extended_bounding_box()
            self.state = "fitting"
            return
        elif self.state == "fitting":
            self.fitting_phase()
        elif self.state == "opening":
            self.calculate_openings()
            self.state = "done"
            return
        elif self.state == "dead":
            for e in self.overlapping:
                ratio = e.collision_box.calculate_overlap(self.collision_box)
                area = self.collision_box.get_area()
                r = ratio / area
                percent = r * 100
                print(f"{percent}%")
            return

    def fill_box(self):
        pixels = self.collision_box.iterate_covered_pixels()
        for p in pixels:
            x = p[0]
            y = p[1]
            self.world.occupy_wall(x, y, self)

    def is_valid(self):
        not_to_short = self.collision_box.length != 0
        not_to_wide = self.collision_box.width < 100
        return not_to_wide and not_to_short

    def normalize(self):
        width = self.collision_box.width
        for p in self.parts:
            width = min(width, p.collision_box.width)
        self.collision_box.width = width

        def dot(px, py, qx, qy):
            """Dot product of 2D vectors (px,py) · (qx,qy)."""
            return px * qx + py * qy

        parent_box = self.get_collision_box()  # The "merged/normalized" parent
        if not parent_box:
            return  # no parent box => nothing to do

        # ------------------------------------------------------------
        # 1) Get parent's orientation & geometry
        # ------------------------------------------------------------
        # - Parent direction & normal (unit vectors in float form)
        p_direction, p_normal = parent_box.derive_direction_and_normal()
        # - Convert to Decimal for consistent arithmetic
        pdx, pdy = Decimal(p_direction.direction[0]), Decimal(p_direction.direction[1])
        pnx, pny = Decimal(p_normal.direction[0]), Decimal(p_normal.direction[1])

        # - Parent center
        pcx_float, pcy_float = parent_box.get_center()
        pcx, pcy = Decimal(float(pcx_float)), Decimal(float(pcy_float))

        # - Parent rotation
        p_rotation = parent_box.rotation

        # - Parent width (we want children to match)
        p_width = parent_box.width

        # ------------------------------------------------------------
        # 2) Compute the parent's normal offset:
        #    the dot product of parent's center on parent's normal
        # ------------------------------------------------------------
        parent_normal_offset = dot(pcx, pcy, pnx, pny)

        # ------------------------------------------------------------
        # 3) For each child, re-align
        # ------------------------------------------------------------
        for part in self.parts:
            cbox = part.collision_box
            if not cbox:
                continue

            # Step (a) Child's center in Decimal
            ccx_f, ccy_f = cbox.get_center()
            ccx, ccy = Decimal(float(ccx_f)), Decimal(float(ccy_f))

            # Step (b) Child's direction offset => dot(child_center, parent_direction)
            child_dir_offset = dot(ccx, ccy, pdx, pdy)

            # Step (c) We want the child's normal offset to match the parent's
            #          So we do child_norm_offset = parent_normal_offset
            #          (We ignore the child's old normal offset.)
            #
            # If, for some reason, you want to shift each child differently,
            # you can, but typically "snap them to the parent's normal line."
            child_norm_offset = parent_normal_offset

            # Step (d) Recompute child's new center in world coords:
            #   new_center = child_dir_offset * direction + child_norm_offset * normal
            new_cx_dec = child_dir_offset * pdx + child_norm_offset * pnx
            new_cy_dec = child_dir_offset * pdy + child_norm_offset * pny

            # Step (e) Update child's box
            #    - same rotation as parent
            #    - same width as parent
            #    - keep original length (or you can clamp it too)
            #    - set its new center
            cbox.rotation = p_rotation
            cbox.set_width(p_width)
            # cbox.set_length(...)  # if you also want to unify lengths, do it here

            cbox.set_position(float(new_cx_dec), float(new_cy_dec))

            # Force recalculation of corners so it’s consistent
            cbox.corners = None
            cbox.calculate_corners()

    def corners(self):
        return self.collision_box.calculate_corners()

    def get_center(self):
        return self.collision_box.get_center()

    def draw_corners(self, screen, vp, colour=(0, 255, 255), size=1):
        self.cb_drawer.draw(self.collision_box, screen, vp, colour)

    def draw(self, screen, vp):

        size = 1
        if self.is_selected():
            size = 3

        colour = (0, 255, 0)
        self.draw_corners(screen, vp, colour, size)
        for o in self.overlapping:
            self.cb_drawer.draw(o.collision_box, screen, vp, colour)

        x, y = self.get_center()
        x, y = vp.convert(x, y)
        pygame.draw.circle(screen, colour, (x, y), 1)
        self.f = font.Font(None, int(vp.zoom_factor * 8))
        for p in self.parts:
            score = p.get_covered_ratio()
            x, y = p.get_center()
            x, y = vp.convert(x, y)
            text_surface = self.f.render(f"s: {score:.{2}f}", True, (15, 255, 0))
            screen.blit(text_surface, (x, y))  # Position (x=10, y=10)

        self.draw_opening(screen, vp)

    def draw_opening(self, screen, vp):
        colour = (255, 0, 0)
        for o in self.openings:
            center = self.get_center()
            v = Vector(center)
            direction = self.collision_box.get_direction()
            direction.scale(o.center_x)
            position = v + direction
            x = position.dx()
            y = position.dy()
            width = self.collision_box.width

            collision_box = CollisionBox(x, y, width, o.width,
                                         self.collision_box.rotation)
            self.cb_drawer.draw(collision_box, screen, vp, colour)

    def get_score(self):
        return len(self.parts)

    def get_collision_box(self):
        return self.collision_box

    def get_occupation_ratio(self):
        if self.collision_box.get_area() == 0:
            return 0
        value = 0
        for p in self.parts:
            value += p.get_occupation_ratio()
        ratio = value / len(self.parts)
        return ratio

    def kill(self):
        self.alive = False
