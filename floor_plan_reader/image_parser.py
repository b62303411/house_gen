import cv2
import numpy as np


class ImageParser:
    def __init__(self):
        self.img_colour = None
        self.img_gray = None
        self._img_gray_filtered = None

    def __int__(self):
        pass

    def set_two_color_img(self, img,threshold):
        self._img_gray_filtered = self.filter_img(img,threshold)

    def read_img(self, path):
        return cv2.imread(path, cv2.IMREAD_GRAYSCALE)

    def filter_img(self, img, threshold):
        adaptive =  cv2.adaptiveThreshold(
            img, 180, cv2.ADAPTIVE_THRESH_MEAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        return (adaptive >= threshold).astype(np.uint8)

    def init(self, img_path, threshold):
        self.img_colour = cv2.imread(img_path)
        self.img_gray = self.read_img(img_path)
        if self.img_gray is None:
            raise FileNotFoundError(f"Cannot load image: {img_path}")
        self._img_gray_filtered = self.filter_img(self.img_gray, threshold)
        self.img_gray = cv2.bitwise_not(self._img_gray_filtered)


    def get_black_and_white(self):
        return self._img_gray_filtered

    def get_colored_image(self):
        return self.img_gray
