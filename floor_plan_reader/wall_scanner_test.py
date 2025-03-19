import numpy as np
import unittest

from PIL.Image import Image

from floor_plan_reader.wall_scanner import WallScanner
from floor_plan_reader.world_factory import WorldFactory




class TestWallScanner(unittest.TestCase):
    def setUp(self):
        self.wf = WorldFactory()

    def test_case_one(self):
            file= "region_20x20_424_467.png"
            image_path = f"test_img\{file}"
            #image = Image.open(image_path)
            #image_array = np.array(image)
            self.wf.set_img(image_path)
            self.world = self.wf.create_World()
            """
            Perform tests on the 10x10 image array.
            """
            # Test 1: Check if the center pixel is green (0, 255, 0)
            center_x, center_y = 10, 10  # Center of a 10x10 grid
            #center_pixel = image_array[center_y, center_x]
            #is_center_green = np.array_equal(center_pixel, [0, 255, 0])

            # Test 2: Count the number of white (empty) and black (wall) pixels
            #white_pixels = np.sum(np.all(image_array == [255, 255, 255], axis=-1))
            #black_pixels = np.sum(np.all(image_array == [0, 0, 0], axis=-1))
            scanner = WallScanner(self.world)
            result = scanner.scan_for_walls(center_x, center_y)
            self.assertTrue(result.is_valid())


