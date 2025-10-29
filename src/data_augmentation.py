# src/data_augmentation.py

import cv2
import os
import numpy as np

def augment_image(image_path, output_folder):
    """Melakukan augmentasi pada satu gambar dan menyimpannya ke folder output."""
    image = cv2.imread(image_path)
    if image is None:
        print(f"[WARNING] Gagal membaca gambar: {image_path}")
        return

    augmented_images = []

    # 1. Rotasi (90, 180, 270 derajat)
    augmented_images.append(cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE))
    augmented_images.append(cv2.rotate(image, cv2.ROTATE_180))
    augmented_images.append(cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE))

    # 2. Flipping (horizontal dan vertikal)
    augmented_images.append(cv2.flip(image, 1))  # Horizontal
    augmented_images.append(cv2.flip(image, 0))  # Vertikal

    # 3. Zoom (crop dan resize)
    h, w = image.shape[:2]
    zoomed = image[int(0.1*h):int(0.9*h), int(0.1*w):int(0.9*w)]  # crop 80%
    zoomed = cv2.resize(zoomed, (w, h))
    augmented_images.append(zoomed)

    # 4. Gaussian Blur
    blurred = cv2.GaussianBlur(image, (5, 5), 0)
    augmented_images.append(blurred)

    # 5. Adjust Brightness (lebih terang)
    bright = cv2.convertScaleAbs(image, alpha=1.2, beta=30)
    augmented_images.append(bright)

    # Menyimpan hasil augmentasi
    for i, aug_img in enumerate(augmented_images):
        output_path = os.path.join(output_folder, f"aug_{i}_{os.path.basename(image_path)}")
        cv2.imwrite(output_path, aug_img)

def augment_folder(input_folder, output_folder):
    """Melakukan augmentasi pada semua gambar di folder (termasuk subfolder)."""
    if not os.path.exists(input_folder):
        print(f"[ERROR] Folder input tidak ditemukan: {input_folder}")
        return

    print(f"[INFO] Memulai augmentasi dari folder: {input_folder}")
    total_images = 0

    for root, dirs, files in os.walk(input_folder):
        for filename in files:
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                image_path = os.path.join(root, filename)
                relative_path = os.path.relpath(root, input_folder)
                output_subfolder = os.path.join(output_folder, relative_path)

                # Pastikan folder tujuan ada
                os.makedirs(output_subfolder, exist_ok=True)

                augment_image(image_path, output_subfolder)
                total_images += 1
                print(f"Augmented: {filename}")

    print(f"[INFO] Total gambar yang diaugmentasi: {total_images}")

if __name__ == "__main__":
    # Gunakan path absolut agar tidak error FileNotFoundError
    processed_data_path = r'E:\DragonEye\dataset\processed'
    augmented_data_path = r'E:\DragonEye\dataset\augmented'

    augment_folder(processed_data_path, augmented_data_path)
    print("[INFO] Augmentasi selesai.")
