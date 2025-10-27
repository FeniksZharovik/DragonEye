# src/data_augmentation.py

import cv2
import os
import numpy as np

def augment_image(image_path, output_folder):
    # Membaca citra
    image = cv2.imread(image_path)

    # Augmentasi citra dengan berbagai teknik
    augmented_images = []

    # 1. Rotasi
    rotated_image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
    augmented_images.append(rotated_image)

    # 2. Flipping Horizontal
    flipped_image = cv2.flip(image, 1)
    augmented_images.append(flipped_image)

    # 3. Zooming
    zoomed_image = image[10:250, 10:250]  # Crop citra untuk zoom
    augmented_images.append(zoomed_image)

    # Menyimpan citra augmented
    for i, aug_img in enumerate(augmented_images):
        output_path = os.path.join(output_folder, f"aug_{i}_{os.path.basename(image_path)}")
        cv2.imwrite(output_path, aug_img)

def augment_folder(input_folder, output_folder):
    # Memastikan folder output ada
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Mengambil semua file citra di folder input
    for filename in os.listdir(input_folder):
        if filename.endswith(('.png', '.jpg', '.jpeg')):
            image_path = os.path.join(input_folder, filename)

            # Melakukan augmentasi citra
            augment_image(image_path, output_folder)
            print(f'Augmented: {filename}')

if __name__ == "__main__":
    processed_data_path = r'..\dataset\processed'
    augmented_data_path = r'..\dataset\augmented'

    # Proses semua citra yang sudah diproses
    augment_folder(processed_data_path, augmented_data_path)
