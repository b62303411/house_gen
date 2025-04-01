import logging
import unittest
import math

from floor_plan_reader.display.point import Point
from floor_plan_reader.math.collision_box import CollisionBox
from floor_plan_reader.math.vector import Vector


class TestLineDistanceCalculations(unittest.TestCase):
    def setUp(self):
        # Tolerance for floating point comparisons
        self.tol = 1e-6

    def test_vertical_line_distance(self):
        """Test distance to vertical line (special case)"""
        # Vertical line from (5,2) to (5,20)
        segment_start = (5, 2)
        segment_end = (5, 20)
        direction = Vector((segment_end[0] - segment_start[0],
                            segment_end[1] - segment_start[1]))

        # Point at (1,10) - should be distance 4
        point = (1, 10)
        dist = direction.distance_to_line(point, segment_start)
        self.assertAlmostEqual(dist, 4.0, delta=self.tol)

        # Point at (5,15) - should be distance 0 (on the line)
        point = (5, 15)
        dist = direction.distance_to_line(point, segment_start)
        self.assertAlmostEqual(dist, 0.0, delta=self.tol)

    def test_horizontal_line_distance(self):
        """Test distance to horizontal line (special case)"""
        # Horizontal line from (2,5) to (20,5)
        segment_start = (2, 5)
        segment_end = (20, 5)
        direction = Vector((segment_end[0] - segment_start[0],
                            segment_end[1] - segment_start[1]))

        # Point at (10,1) - should be distance 4
        point = (10, 1)
        dist = direction.distance_to_line(point, segment_start)
        self.assertAlmostEqual(dist, 4.0, delta=self.tol)

    def test_diagonal_line_distance(self):
        """Test distance to diagonal line (general case)"""
        # Diagonal line from (1,1) to (5,5)
        segment_start = (1, 1)
        segment_end = (5, 5)
        direction = Vector((segment_end[0] - segment_start[0],
                            segment_end[1] - segment_start[1]))

        # Point at (1,5) - should be distance 2*sqrt(2) ≈ 2.828427
        point = (1, 5)
        dist = direction.distance_to_line(point, segment_start)
        expected = 2 * math.sqrt(2)
        self.assertAlmostEqual(dist, expected, delta=self.tol)



    def test_collision_box_center_line(self):
        """Test distance to collision box's center line"""
        # Vertical box centered at (5,11) with height 18
        box = CollisionBox(center_x=5, center_y=11, width=1, length=18, rotation=90)

        cases = [
            ((1, 10), 4.0),  # Left of box
            ((7, 11), 2.0),  # Right of box
            ((5, 15), 0.0),  # On center line
            ((5, 5), 0.0)  # On center line but outside box bounds
        ]

        for point, expected in cases:
            with self.subTest(point=point):
                p = Point(point[0],point[1])
                dist = box.distance_from_center_line(p)
                self.assertAlmostEqual(dist, expected, delta=self.tol)



    def test_move_forward(self):
        cb = CollisionBox(center_x=0, center_y=0, width=2, length=4, rotation=0)
        cb.move_forward(5)
        self.assertAlmostEqual(cb.center_x, 5)
        self.assertAlmostEqual(cb.center_y, 0)

    def test_move_backward(self):
        cb = CollisionBox(center_x=0, center_y=0, width=2, length=4, rotation=90)
        cb.move_backward(3)
        self.assertAlmostEqual(cb.center_x, 0)
        self.assertAlmostEqual(cb.center_y, -3)

    def test_move_diagonal_forward(self):
        cb = CollisionBox(center_x=1, center_y=1, width=2, length=4, rotation=45)
        cb.move_forward(math.sqrt(2))
        self.assertAlmostEqual(cb.center_x, 2)
        self.assertAlmostEqual(cb.center_y, 2)

    def test_move_diagonal_backward(self):
        cb = CollisionBox(center_x=1, center_y=1, width=2, length=4, rotation=225)
        cb.move_backward(math.sqrt(2))
        self.assertAlmostEqual(cb.center_x, 2)
        self.assertAlmostEqual(cb.center_y, 2)
if __name__ == "__main__":
    unittest.main()