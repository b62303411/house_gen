import cv2
import numpy as np


class ImageParser:
    def __init__(self):
        self.img_gray = None
        self._img_gray_filtered = None

    def __int__(self):
        pass

    def set_two_color_img(self, img,threshold):
        self._img_gray_filtered = self.filter_img(img,threshold)

    def read_img(self, path):
        return cv2.imread(path, cv2.IMREAD_GRAYSCALE)

    def filter_img(self, img, threshold):
        return (img >= threshold).astype(np.uint8)

    def init(self, img_path, threshold):
        self.img_gray = self.read_img()
        if self.img_gray is None:
            raise FileNotFoundError(f"Cannot load image: {img_path}")
        self.img_gray = cv2.bitwise_not(self.img_gray)
        self._img_gray_filtered = self.filter_img(self.img_gray,threshold)

    def get_black_and_white(self):
        return self._img_gray_filtered

    def get_colored_image(self):
        return self.img_gray
