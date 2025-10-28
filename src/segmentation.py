import cv2
import os
import numpy as np

def segment_image(image_path, output_path):
    """
    Melakukan segmentasi citra dengan thresholding dan menyimpan hasilnya.
    """
    # Membaca citra
    image = cv2.imread(image_path)

    # Mengkonversi citra menjadi grayscale
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Melakukan thresholding untuk segmentasi (misalnya, threshold global)
    _, binary_image = cv2.threshold(gray_image, 127, 255, cv2.THRESH_BINARY)

    # Menyimpan hasil segmentasi
    cv2.imwrite(output_path, binary_image)

def segment_folder(input_folder, output_folder):
    """
    Memproses semua citra dalam folder dan subfolder untuk segmentasi.
    """
    # Memastikan folder output ada
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Memastikan folder input ada
    if not os.path.exists(input_folder):
        print(f"Folder input {input_folder} tidak ditemukan!")
        return  # Menghentikan proses jika folder input tidak ada

    # Menyusuri folder dan subfolder dalam input folder
    for root, dirs, files in os.walk(input_folder):
        for filename in files:
            if filename.endswith(('.png', '.jpg', '.jpeg')):  # Memproses hanya file citra
                image_path = os.path.join(root, filename)

                # Membuat folder output yang sesuai dengan struktur folder input
                relative_path = os.path.relpath(root, input_folder)
                output_subfolder = os.path.join(output_folder, relative_path)
                if not os.path.exists(output_subfolder):
                    os.makedirs(output_subfolder)

                output_path = os.path.join(output_subfolder, filename)

                # Melakukan segmentasi
                segment_image(image_path, output_path)
                print(f'Segmented: {filename} at {output_path}')

if __name__ == "__main__":
    processed_data_path = r'E:\DragonEye\dataset\processed'  # Gantilah dengan jalur yang sesuai
    segmented_data_path = r'E:\DragonEye\dataset\segmented'  # Gantilah dengan jalur yang sesuai

    # Proses semua citra yang sudah diproses
    segment_folder(processed_data_path, segmented_data_path)
