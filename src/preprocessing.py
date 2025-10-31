import cv2
import numpy as np

def preprocess_image(img):
    """Resize, denoise, dan konversi warna"""
    img = cv2.resize(img, (256, 256))
    img = cv2.GaussianBlur(img, (3, 3), 0)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    return hsv
