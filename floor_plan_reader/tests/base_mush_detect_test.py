import unittest
from itertools import count

import numpy as np

from floor_plan_reader.agents.mushroom_agent import Mushroom
from floor_plan_reader.agents.wall_segment import WallSegment
from floor_plan_reader.id_util import IdUtil
from floor_plan_reader.image_parser import ImageParser
from floor_plan_reader.simulation import Simulation
from floor_plan_reader.world_factory import WorldFactory


class TestMushroomGrowth(unittest.TestCase):
    def setUp(self):
        self.mushroom = None
        self.world = None
        self.blob = None
        self.node_seq = count(start=1)

    def get_world(self):
        return self.simulation.world

    def create_wall(self, x, y):
        self.mushroom = Mushroom(self.get_world(), self.blob, x, y, next(self.node_seq))
        return self.mushroom

    def test_specific(self):
        self.simulation = Simulation()
        file = "735_252x252_517_599.png"
        image_path = f"resources\\{file}"
        img_parser = ImageParser()
        img = img_parser.read_img(image_path)
        img_parser.set_two_color_img(img, 200)

        self.simulation.init_world(img_parser)

        self.blob = self.simulation.world.create_blob(91, 126)
        m = self.create_wall(91, 126)
        m.performe_ray_trace()
        self.assertAlmostEqual(36, m.collision_box.get_area())
        m.absorb_bleading_out()
        self.assertAlmostEqual(49, m.collision_box.get_area())
        m.collision_box._cached_pixels = None
        m.fill_box()
        self.assertTrue(self.get_world().is_occupied(90, 123))
        self.assertTrue(self.get_world().is_occupied(95, 123))
        self.assertTrue(self.get_world().is_occupied(96, 127))
        self.assertTrue(self.get_world().is_occupied(96, 128))
        polygon = m.collision_box.get_polygon()

        m = self.create_wall(44, 102)
        m.performe_ray_trace()

        self.assertAlmostEqual(306, m.collision_box.get_area())
        self.assertEqual(270, m.collision_box.rotation)
        m.absorb_bleading_out()
        self.assertEqual(371, m.collision_box.get_area())
        m.fill_box()
        self.assertTrue(self.get_world().is_occupied(46, 77))
        self.assertEqual(270, m.collision_box.rotation)
        polygon = m.collision_box.get_polygon()

        self.assertAlmostEqual(40,polygon.bounds[0])
        self.assertAlmostEqual(76, polygon.bounds[1])
        self.assertAlmostEqual(46, polygon.bounds[2])
        self.assertAlmostEqual(128, polygon.bounds[3])
