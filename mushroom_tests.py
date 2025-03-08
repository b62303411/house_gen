import unittest

import numpy as np

from cell import Cell
from mushroom_agent import Mushroom
from world_factory import WorldFactory


class TestMushroomGrowth(unittest.TestCase):
    def setUp(self):
        wf = WorldFactory()
        # Initialize grid with empty space (0)
        grid_size = (20, 20)
        grid = np.zeros(grid_size, dtype=int)
        wf.set_grid(grid)
        self.world = wf.create_World()  # Mock world
        self.mushroom = Mushroom(5, 5, self.world, 1)

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
        self.assertLessEqual(self.mushroom.collision_box.width,3)
        self.assertLessEqual(self.mushroom.collision_box.length,10)
        self.assertEqual(self.mushroom.state,"stem_growth")
        self.mushroom.run()
        self.assertEqual(self.mushroom.state, "width_assessment")
        self.mushroom.run()
        #self.assertEqual(self.mushroom.state,"width_expansion")
        self.mushroom.run()
        corners = self.mushroom.collision_box.calculate_corners()
        bottom_right = corners [0]
        other = corners [1]
        top_let = corners[2]
        dir = self.mushroom.collision_box.get_direction()
        self.assertEqual(dir[0],1)
        self.assertEqual(top_let[0], 11)
        self.assertEqual(top_let[1], 4)
        self.assertEqual(bottom_right[0],2)
        self.assertEqual(bottom_right[1], 6)
        self.assertEqual(other[0], 11)
        self.assertEqual(other[1], 6)
        for c in corners:
            self.assertTrue(self.mushroom.collidepoint(c[0],c[1]))
        self.assertTrue(self.mushroom.center_on_food())
        x, y = self.mushroom.get_center()
        self.assertEqual(x, 6.5)
        self.assertEqual(y, 5)

    def test_wall_detection_vertical_wall(self):
        self.mushroom = Mushroom(4,2, self.world, 1)
        self.world.grid[2:12,4:7] = 1  # Horizontal wall (3 pixels thick, 4 pixels long)
        self.assertFalse(self.world.is_food(int(2), int(4)))
        self.assertTrue(self.world.is_food(int(4), int(4)))
        self.assertFalse(self.world.is_food(int(2), int(4)))
        is_food = self.world.is_food_at(self.mushroom.get_center())
        self.assertTrue(is_food, "Mushroom need to be on the food")
        self.mushroom.run()
        self.assertLessEqual(self.mushroom.collision_box.width,3)
        self.assertLessEqual(self.mushroom.collision_box.length,10)
        self.assertEqual(self.mushroom.state,"stem_growth")
        self.mushroom.run()
        self.assertEqual(self.mushroom.state, "width_assessment")
        self.mushroom.run()
        #self.assertEqual(self.mushroom.state,"width_expansion")
        self.mushroom.run()
        corners = self.mushroom.collision_box.calculate_corners()
        bottom_right = corners [0]
        other = corners [1]
        top_let = corners[2]
        dir = self.mushroom.collision_box.get_direction()
        self.assertEqual(dir[0],0)
        self.assertEqual(dir[1], 1)
        self.assertEqual(top_let[0], 4)
        self.assertEqual(top_let[1], 11)
        self.assertEqual(bottom_right[0],6)
        self.assertEqual(bottom_right[1], 2)
        self.assertEqual(other[0], 6)
        self.assertEqual(other[1], 11)
        for c in corners:
            self.assertTrue(self.mushroom.collidepoint(c[0],c[1]))
        self.assertTrue(self.mushroom.center_on_food())
        x,y = self.mushroom.get_center()
        self.assertEqual(x, 5)
        self.assertEqual(y,6.5)
    def test_wall_detection(self):
        pass



if __name__ == "__main__":
    unittest.main()