import logging
from decimal import Decimal

import pygame
from pygame import font

from floor_plan_reader.agents.agent import Agent
from floor_plan_reader.display.bounding_box_drawer import BoundingBoxDrawer
from floor_plan_reader.math.collision_box import CollisionBox
from floor_plan_reader.pruning_util import PruningUtil


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

    def set_position(self, x, y):
        self.collision_box.set_position(x, y)

    def calculate_if_external(self):
        pass

    def calculate_openings(self):
        pass

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
        steps_backward,bx,by = self.crawl(points_backward)
        steps_forward,fx,fy = self.crawl(points_forward)
        self.collision_box_extended = self.collision_box.copy()

        if steps_forward > 1 or steps_backward > 1:
            extension = steps_backward+steps_forward
            l = self.collision_box_extended.length
            self.collision_box_extended.set_lenght(l + extension+2)
            if steps_forward > steps_backward:
                (bx1, by1), (bx2, by2) = self.collision_box_extended.get_center_line()
                self.collision_box_extended.move_forward(abs(steps_backward-steps_forward)/2)
                (x1, y1), (x2, y2) = self.collision_box_extended.get_center_line()
                id_start = self.world.get_occupied_id(x1,y1)
                id_end = self.world.get_occupied_id(x2, y2)
                if id_start in self.wall_dic and id_end in self.wall_dic:
                    if steps_forward > 1 or steps_backward > 1:
                        logging.info("error")

            else:
                self.collision_box_extended.move_backward(abs(steps_backward-steps_forward)/2)
                (x1, y1), (x2, y2) = self.collision_box_extended.get_center_line()
                id_start = self.world.get_occupied_id(x1, y1)
                id_end = self.world.get_occupied_id(x2, y2)
                if id_start in self.wall_dic and id_end in self.wall_dic:
                    if steps_forward > 1 or steps_backward > 1:
                        logging.info("error")

        logging.info(f"steps b{steps_backward} steps f{steps_forward}")

    def crawl(self, points):
        steps = 0
        x,y = 0,0
        measuring_extent = False
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
                return steps ,x,y

        return steps,x,y

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
