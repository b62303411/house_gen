import unittest
from itertools import count, permutations

import numpy as np
from shapely.geometry import LineString, Point

from floor_plan_reader.agents.mushroom_agent import Mushroom
from floor_plan_reader.agents.wall_segment import WallSegment
from floor_plan_reader.math.collision_box import CollisionBox
from floor_plan_reader.world_factory import WorldFactory


class TestWallScanner(unittest.TestCase):
    def setUp(self):
        wf = WorldFactory()
        # Initialize grid with empty space (0)
        grid_size = (700, 700)
        grid = np.zeros(grid_size, dtype=int)
        wf.set_grid(grid)
        self.world = wf.create_World()  # Mock world
        self.blob = None
        self.node_seq = count(start=1)

    def create_mush(self,line_coord):
        line = LineString(line_coord)
        cb = CollisionBox.create_from_line(line,4)
        center  = cb.get_center()
        mushroom: Mushroom = Mushroom(self.world, self.blob, center[0],center[1] ,f"N{next(self.node_seq)}")
        mushroom.collision_box=cb
        return mushroom

    def test_sorting_all_permutations_of_three_segments(self):
        parent_line = [(602.5, 50.0), (602.5, 190.0)]
        line = LineString(parent_line)
        parent_line_e = [(602.5, 49.0), (602.5, 200.0)]
        line_e = LineString(parent_line_e)
        cb = CollisionBox.create_from_line(line, 4)
        cbe = CollisionBox.create_from_line(line_e, 4)
        wall = WallSegment(0, self.world)
        wall.collision_box = cb
        wall.collision_box_extended = cbe
        # Define 3 ordered segments
        line_coords = [
            [(602.5, 50), (602.5, 90)],  # A
            [(602.5, 100), (602.5, 140)],  # B
            [(602.5, 150), (602.5, 190)]  # C
        ]

        # Generate all permutations of the 3 segments
        for i, perm in enumerate(permutations(line_coords), 1):
            with self.subTest(permutation=i):
                wall.parts.clear()

                for coords in perm:
                    line = LineString(coords)
                    part = self.create_mush(line)
                    wall.add_part(part)

                center_lines = wall.get_sorted_lines()
                for j in range(len(center_lines) - 1):
                    end_j = Point(center_lines[j].coords[-1])
                    start_j1 = Point(center_lines[j + 1].coords[0])
                    gap = end_j.distance(start_j1)

                    print(f"Permutation {i}, Segment {j} → {j + 1}: gap={gap:.2f}")
                    self.assertTrue(gap < 100, f"Gap too big in permutation {i}: {gap:.2f}")
                    self.assertLessEqual(end_j.y, start_j1.y,
                                         f"Permutation {i}: Line {j} ends at {end_j.y} > start of line {j + 1} at {start_j1.y}")
    def test_unsorted_vertical_parts_fail(self):
        # Parent wall is vertical
        parent_line = [(602.5, 50.0), (602.5, 350.0)]
        line = LineString(parent_line)
        parent_line_e = [(602.5, 49.0), (602.5, 351.0)]
        line_e = LineString(parent_line)
        cb = CollisionBox.create_from_line(line, 4)
        cbe = CollisionBox.create_from_line(line_e, 4)
        # Define 3 ordered segments
        line_coords = [
            [(602.5, 50), (602.5, 90)],  # A
            [(602.5, 100), (602.5, 140)],  # B
            [(602.5, 150), (602.5, 190)]  # C
        ]

        # Parts out of order
        parts = [self.create_mush([(602.5, 304.5), (602.5, 332.5)]),
                 self.create_mush([(602.5, 238.5), (602.5, 268.5)]),
                 self.create_mush([(602.5, 57.5), (602.5, 145.5)])
        ]

        wall = WallSegment(0, self.world)
        wall.collision_box = cb
        wall.collision_box_extended = cbe
        for p in parts:
            wall.add_part(p)
        center_lines = wall.get_sorted_lines()
        center = Point(wall.get_center())

        for i in range(len(center_lines) - 1):
            end_i = Point(center_lines[i].coords[-1])
            start_i1 = Point(center_lines[i + 1].coords[0])
            gap = end_i.distance(start_i1)
            self.assertTrue(gap < 100)
            assert end_i.y <= start_i1.y, (
                f"Line {i} ends at {end_i.y} but next line starts at {start_i1.y}, "
                f"indicating incorrect order"
            )

