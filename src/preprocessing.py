import cv2
import numpy as np

def preprocess_image(img):
    """Denoise dan konversi warna, tanpa resize (untuk pengukuran akurat)."""
    img = cv2.GaussianBlur(img, (3, 3), 0)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    return hsv
