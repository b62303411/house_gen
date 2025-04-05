import json
import math
import unittest
from decimal import Decimal

import numpy as np

from floor_plan_reader.agents.mushroom_agent import Mushroom
from floor_plan_reader.agents.wall_segment import WallSegment
from floor_plan_reader.cell import Cell
from floor_plan_reader.id_util import IdUtil
from floor_plan_reader.math.collision_box import CollisionBox

from floor_plan_reader.world_factory import WorldFactory


class TestMushroomGrowth(unittest.TestCase):
    def setUp(self):
        wf = WorldFactory()
        # Initialize grid with empty space (0)
        grid_size = (700, 700)
        grid = np.zeros(grid_size, dtype=int)
        wf.set_grid(grid)
        self.world = wf.create_World()  # Mock world
        self.blob = None
        self.mushroom = Mushroom(self.world, self.blob, 5, 5, 1)

        self.ws = WallSegment(IdUtil.get_id(), self.world)

    def create_wall(self, x, y):
        self.mushroom = Mushroom(self.world, self.blob, x, y, 1)

    def test_test(self):
        self.mushroom.run()

    def test_perimeter_identification(self):
        self.mushroom.perimeter_reaction_phase()
        self.assertGreater(len(self.mushroom.perimeter), 0, "Perimeter should not be empty")

    def test_growth_cell_clustering(self):
        # Manually add some growth cells
        self.mushroom.growth_cells = {Cell(6, 6), Cell(6, 7), Cell(7, 7)}
        clusters = self.mushroom.cluster_growth_cells(self.mushroom.growth_cells)
        self.assertLessEqual(len(clusters), len(self.mushroom.growth_cells),
                             "Clusters should be fewer than individual growth cells")

    def test_single_mushroom_per_cluster(self):
        self.mushroom.growth_phase()
        self.assertLessEqual(len(self.world.agents), len(self.mushroom.growth_cells),
                             "Only one mushroom should spawn per cluster")

    def test_wall_detection_horizontal_wall(self):
        self.mushroom = Mushroom(2, 4, self.world, 1)
        self.world.grid[4:7, 2:12] = 1  # Horizontal wall (3 pixels thick, 4 pixels long)
        self.assertFalse(self.world.is_food(int(1), int(3)))
        self.assertTrue(self.world.is_food(int(2), int(4)))
        self.assertFalse(self.world.is_food(int(12), int(4)))
        is_food = self.world.is_food_at(self.mushroom.get_center())
        self.assertTrue(is_food, "Mushroom need to be on the food")
        self.mushroom.run()
        self.assertLessEqual(self.mushroom.collision_box.width, 3)
        self.assertLessEqual(self.mushroom.collision_box.length, 10)
        self.assertEqual(self.mushroom.state, "stem_growth")
        self.mushroom.run()
        self.assertEqual(self.mushroom.state, "width_assessment")
        self.mushroom.run()
        # self.assertEqual(self.mushroom.state,"width_expansion")
        self.mushroom.run()
        corners = self.mushroom.collision_box.calculate_corners()
        bottom_right = corners[0]
        other = corners[1]
        top_let = corners[2]
        dir = self.mushroom.collision_box.get_direction()
        self.assertEqual(dir[0], 1)
        self.assertEqual(top_let[0], 11)
        self.assertEqual(top_let[1], 4)
        self.assertEqual(bottom_right[0], 2)
        self.assertEqual(bottom_right[1], 6)
        self.assertEqual(other[0], 11)
        self.assertEqual(other[1], 6)
        for c in corners:
            self.assertTrue(self.mushroom.collidepoint(c[0], c[1]))
        self.assertTrue(self.mushroom.center_on_food())
        x, y = self.mushroom.get_center()
        self.assertEqual(x, 6.5)
        self.assertEqual(y, 5)

    def test_wall_detection_vertical_wall(self):
        self.create_wall(4, 2)

        self.world.grid[2:12, 4:7] = 1  # Horizontal wall (3 pixels thick, 4 pixels long)
        self.assertFalse(self.world.is_food(int(2), int(4)))
        self.assertTrue(self.world.is_food(int(4), int(4)))
        self.assertFalse(self.world.is_food(int(2), int(4)))
        is_food = self.world.is_food_at(self.mushroom.get_center())
        self.assertTrue(is_food, "Mushroom need to be on the food")
        self.mushroom.run()
        self.assertLessEqual(self.mushroom.collision_box.width, 3)
        self.assertLessEqual(self.mushroom.collision_box.length, 10)
        self.assertEqual(self.mushroom.get_state(), "stem_growth")
        self.mushroom.run()
        self.assertEqual(self.mushroom.get_state(), "width_assessment")
        self.mushroom.run()
        # self.assertEqual(self.mushroom.state,"width_expansion")
        self.mushroom.run()
        corners = self.mushroom.collision_box.calculate_corners()
        bottom_right = corners[0]
        other = corners[1]
        top_let = corners[2]
        dir = self.mushroom.collision_box.get_direction()
        self.assertEqual(dir[0], 0)
        self.assertEqual(dir[1], 1)
        self.assertEqual(top_let[0], 4)
        self.assertEqual(top_let[1], 11)
        self.assertEqual(bottom_right[0], 6)
        self.assertEqual(bottom_right[1], 2)
        self.assertEqual(other[0], 6)
        self.assertEqual(other[1], 11)
        for c in corners:
            self.assertTrue(self.mushroom.collidepoint(c[0], c[1]))
        self.assertTrue(self.mushroom.center_on_food())
        x, y = self.mushroom.get_center()
        self.assertEqual(x, 5)
        self.assertEqual(y, 6.5)

    def test_wall_detection(self):
        pass

    def test_collisions(self):
        c = CollisionBox(10, 10, 4, 25, 45)
        c.length = 100
        c.width = 4
        c.center_y = 0
        c.center_x = 0
        c.rotation = 45
        corners = c.calculate_corners()
        d = 50 / math.sqrt(2)
        di = int(d)
        for c in corners:
            self.assertAlmostEqual(di, abs(c[0]), delta=1)

    def test_merge_horizontal_aligned(self):
        # Two boxes, same y, horizontal orientation
        boxA = CollisionBox(center_x=10, center_y=10, width=4, length=6, rotation=0)
        boxB = CollisionBox(center_x=20, center_y=10, width=4, length=6, rotation=0)
        # box a is supposed to be  from 7  to 13
        lineA = boxA.get_center_line()
        lineAString = boxA.get_center_line_string()
        self.assertAlmostEqual(7, lineA[0][0])
        self.assertAlmostEqual(13, lineA[1][0])
        lineB = boxB.get_center_line()
        self.assertAlmostEqual(17, lineB[0][0])
        self.assertAlmostEqual(23, lineB[1][0])

        # box b is supposed to be from 18  to 23
        merged = boxA.merge_aligned(boxB)

        # Both boxes have the same orientation and the same width => merged should have the same width
        self.assertAlmostEqual(merged.width, 4, msg="Width should remain the same for horizontally merged boxes.")
        # The length should be the sum of both plus the gap between them
        # Original box centers are at x=10 and x=20 with length=6 each => half-length=3
        # So the left edge is at x=10-3=7, right edge is at x=20+3=23 => total length=16
        self.assertAlmostEqual(merged.length, 16, msg="Merged length should encompass both boxes fully.")
        # Rotation remains 0
        self.assertEqual(merged.rotation, 0)
        # Check center is midpoint between x=7 (left) and x=23 (right) => (7+23)/2 = 15
        self.assertAlmostEqual(merged.center_x, 15)
        self.assertAlmostEqual(merged.center_y, 10)

    def test_merge_vertical_aligned(self):
        # Two boxes, same x, vertical orientation
        boxA = CollisionBox(center_x=10, center_y=10, width=4, length=6, rotation=90)
        boxB = CollisionBox(center_x=10, center_y=20, width=4, length=6, rotation=90)

        merged = boxA.merge_aligned(boxB)

        # Both boxes share rotation=90 => the length axis is vertical, so 'width' remains the same
        self.assertAlmostEqual(merged.width, 4, msg="Width should remain the same for vertically merged boxes.")
        # The length should again be the sum plus gap
        # For each box: half-length=3 => top is at y=10-3=7 for boxA, bottom is at y=20+3=23 for boxB => total length=16
        self.assertAlmostEqual(merged.length, 16, msg="Merged length should encompass both boxes fully.")
        # Rotation remains 90
        self.assertEqual(merged.rotation, 90)
        # The center is between y=7 and y=23 => midpoint = 15
        self.assertAlmostEqual(merged.center_x, 10)
        self.assertAlmostEqual(merged.center_y, 15)

    def create_mush(self,cb):
        m = Mushroom(self.world, self.blob, cb.center_x, cb.center_y, IdUtil.get_id())
        m.collision_box = cb.copy()
        return m

    def test_merge_vertical_aligned_json(self):
        filename = "resources/test.json"
        world = self.world
        ws = self.ws

        with open(filename, "r") as f:
            data = json.load(f)  # This will be a list of dicts

            # Re-create each CollisionBox
        boxes = [CollisionBox.from_dict(item) for item in data]
        mushrooms = []

        for b in boxes:
            self.assertTrue(b.is_on_same_axis_as(boxes[0]))
            m = self.create_mush(b)
            mushrooms.append(m)

        for m in mushrooms:
            self.ws.add_part(m)

        ws.process_state()
        x, y = ws.get_center()
        a = Decimal(602.75)
        b = Decimal(602.5)
        c = Decimal(602.5)
        d = Decimal(602.5)
        e = Decimal(603.0)
        value = (a + b + c + d + e) / 5
        self.assertAlmostEqual(Decimal(602.65), value)

        l = Decimal(ws.collision_box.length + 2)
        self.assertAlmostEqual(57, l, delta=2)
        self.assertAlmostEqual(696.25, x, delta=2)
        self.assertAlmostEqual(466.25, y, delta=2)

    def test_corners(self):
        cb = CollisionBox(17, 354, 7, 7, 315)

        corners = cb.calculate_corners()

        self.assertNotAlmostEquals(corners[1][0], corners[3][0])

    def test_merge_vertical_aligned_json2(self):
        filename = "resources/test.json"
        world = self.world
        with open(filename, "r") as f:
            data = json.load(f)  # This will be a list of dicts

            # Re-create each CollisionBox
        boxes = [CollisionBox.from_dict(item) for item in data]
        mushrooms = []
        ws = WallSegment(IdUtil.get_id(), world)
        for b in boxes:
            self.assertTrue(b.is_on_same_axis_as(boxes[0]))
            m = Mushroom(b.center_x, b.center_y, world, IdUtil.get_id())
            m.collision_box = b.copy()
            mushrooms.append(m)
            self.world.agents.append(m)
            self.world.walls.add(m)
            pixels = b.iterate_covered_pixels()
            for p in pixels:
                self.world.draw_at(p, 1)
                self.world.occupy(p[0], p[1], m)
        segment = None

        for m in mushrooms:
            m.crawl_phase()
            ws = m.wall_segment
            if ws is not None:
                segment = ws
            self.assertTrue(m.wall_segment is not None)

        self.assertEqual(5, len(segment.parts))


if __name__ == "__main__":
    unittest.main()
