# src/segmentation.py

import cv2
import os
import numpy as np

def segment_image(image_path, output_path):
    # Membaca citra
    image = cv2.imread(image_path)

    # Mengkonversi citra menjadi grayscale
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Melakukan thresholding untuk segmentasi (misalnya, threshold global)
    _, binary_image = cv2.threshold(gray_image, 127, 255, cv2.THRESH_BINARY)

    # Menyimpan hasil segmentasi
    cv2.imwrite(output_path, binary_image)

def segment_folder(input_folder, output_folder):
    # Memastikan folder output ada
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Mengambil semua file citra di folder input
    for filename in os.listdir(input_folder):
        if filename.endswith(('.png', '.jpg', '.jpeg')):
            image_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, filename)

            # Melakukan segmentasi
            segment_image(image_path, output_path)
            print(f'Segmented: {filename}')

if __name__ == "__main__":
    processed_data_path = r'..\dataset\processed'
    segmented_data_path = r'..\dataset\segmented'

    # Proses semua citra yang sudah diproses
    segment_folder(processed_data_path, segmented_data_path)
