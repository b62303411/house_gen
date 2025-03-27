import logging
import threading
import time

import numpy as np
import unittest

import pygame
from PIL.Image import Image

from floor_plan_reader.display.view_point import ViewPoint
from floor_plan_reader.simulation import Simulation

import numpy as np
import unittest

from PIL.Image import Image

from floor_plan_reader.wall_scanner import WallScanner
from floor_plan_reader.world_factory import WorldFactory

class TestWallScanner(unittest.TestCase):
    def setUp(self):
        self.wf = WorldFactory()
        self.width = 0
        self.height = 0
        self.vp = ViewPoint()
        self.simulation = None
        pygame.init()



    def draw(self):
        self.screen.fill((50, 50, 50))

        # Scale the floorplan based on zoom_factor
        new_w = int(self.width * self.vp.zoom_factor)
        new_h = int(self.height * self.vp.zoom_factor)
        floorplan_scaled = pygame.transform.smoothscale(self.simulation.floorplan_surf, (new_w, new_h))
        img = pygame.transform.smoothscale(self.simulation.img_gray_surface, (new_w, new_h))

    def worker(self):
        logging.debug("Thread started")
        #time.sleep(2)  # Simulate some work
        while True:
            self.simulation.view.draw()
            time.sleep(0.5)
        logging.debug("Thread finished")
    def test_case_two(self):


        self.simulation = Simulation()
        file = "debug_169x15_552_337.png"
        image_path = f"test_img\\{file}"
        self.simulation.init_world(image_path)
        self.simulation.view.vp.zoom_factor=5
        self.screen = pygame.display.set_mode((self.simulation.width*5, self.simulation.height*5), pygame.RESIZABLE)
        pygame.display.set_caption("Ant Demo (Native Resolution + Zoom)")
        shape = self.simulation.world.get_shape()
        self.simulation.view.init()
        thread = threading.Thread(target=self.worker)
        thread.start()
        """
            Perform tests on the 10x10 image array.
            """
        # Test 1: Check if the center pixel is green (0, 255, 0)
        center_x, center_y = shape[1] // 2, shape[0] // 2  # Center of a 10x10 grid
        self.simulation.world.draw_at((center_x,center_y),1)
        scanner = WallScanner(self.simulation.world)
        result = scanner.scan_for_walls(center_x, center_y)
        self.assertTrue(result.is_valid())
        blob = self.simulation.world.create_blob(center_x, center_y)

        #self.simulation.world = self.world
        blob.active_mush
        n = 0
        while n < 84:
            self.simulation.run()
            self.simulation.view.draw()
            n = n + 1
        n=0
        self.simulation.view.draw()
        while n < 5:
            n = n + 1
            self.simulation.run()
            self.simulation.view.draw()
        self.simulation.run()
        self.simulation.view.draw()
        self.simulation.run()
        self.simulation.view.draw()
        self.assertEqual(blob.status, "done")

    def test_case_one(self):
        file = "region_20x20_426_463.png"
        image_path = f"test_img\\{file}"
        # image = Image.open(image_path)
        # image_array = np.array(image)
        self.wf.set_img(image_path)
        self.world = self.wf.create_World()
        """
            Perform tests on the 10x10 image array.
            """
        # Test 1: Check if the center pixel is green (0, 255, 0)
        center_x, center_y = 10, 10  # Center of a 10x10 grid
        # center_pixel = image_array[center_y, center_x]
        # is_center_green = np.array_equal(center_pixel, [0, 255, 0])

        # Test 2: Count the number of white (empty) and black (wall) pixels
        # white_pixels = np.sum(np.all(image_array == [255, 255, 255], axis=-1))
        # black_pixels = np.sum(np.all(image_array == [0, 0, 0], axis=-1))
        scanner = WallScanner(self.world)
        result = scanner.scan_for_walls(center_x, center_y)
        self.assertTrue(result.is_valid())


class TestWallScanner(unittest.TestCase):
    def setUp(self):
        self.wf = WorldFactory()
    def test_case_one(self):
            file= "region_20x20_426_463.png"
            image_path = f"test_img\\{file}"
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
