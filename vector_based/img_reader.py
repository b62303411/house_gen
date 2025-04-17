import cv2
import numpy as np
from shapely import Polygon


class ImgReader:

    def __init__(self):
        pass

    def extract_wall_polygons(self,image_path, darkness_threshold=30, min_area=20):
        """
        Extract wall shapes (drawn in black) from an image, even if blurred or low-res.

        Args:
            image_path (str): Path to the input image.
            darkness_threshold (int): Max brightness to consider a pixel part of a wall (0–255).
            min_area (int): Minimum area (in pixels) for a polygon to be considered valid.

        Returns:
            List[Polygon]: List of Shapely polygons representing wall contours.
        """
        # Step 1: Load and convert to grayscale
        img = cv2.imread(image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Step 2: Threshold to detect "almost black"
        _, mask = cv2.threshold(gray, darkness_threshold, 255, cv2.THRESH_BINARY_INV)

        # Step 3: Morphological closing to absorb bleed
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        closed = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        # Step 4: Find contours
        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Step 5: Convert contours to Shapely polygons
        polygons = []
        for contour in contours:
            if len(contour) >= 3:
                coords = [(int(pt[0][0]), int(pt[0][1])) for pt in contour]
                poly = Polygon(coords)
                if poly.is_valid and poly.area >= min_area:
                    polygons.append(poly)

        return polygons
    def read(self,img):
        polygons = self.extract_wall_polygons('../floor_plans/fp2.png')
        image = cv2.imread('../floor_plans/fp2.png')  # Color image
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Define threshold for "almost black"
        _, wall_mask = cv2.threshold(gray, 30, 255, cv2.THRESH_BINARY_INV)

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        closed_mask = cv2.morphologyEx(wall_mask, cv2.MORPH_CLOSE, kernel)

        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(closed_mask)
        min_area = 20  # discard small dots

        clean_mask = np.zeros_like(closed_mask)
        for i in range(1, num_labels):  # skip background
            if stats[i, cv2.CC_STAT_AREA] >= min_area:
                clean_mask[labels == i] = 255

        return polygons, clean_mask