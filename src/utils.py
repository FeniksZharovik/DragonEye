import cv2
import numpy as np
import os

def load_all_images(base_path):
    """Load semua file gambar dari subfolder raw_data"""
    image_paths = []
    for root, _, files in os.walk(base_path):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                image_paths.append(os.path.join(root, file))
    return image_paths

def save_image(output_path, image):
    cv2.imwrite(output_path, image)
