import os
import cv2
import csv
from config import RAW_DATA_DIR, SEGMENTED_DIR, FEATURE_CSV
from utils import load_all_images, save_image
from preprocessing import preprocess_image
from segmentation import segment_image
from feature_extraction import extract_features

# 1. Load semua gambar
image_paths = load_all_images(RAW_DATA_DIR)
print(f"[INFO] Total gambar ditemukan: {len(image_paths)}")

# 2. Buat file CSV untuk fitur
with open(FEATURE_CSV, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["filename", "hue_mean", "texture_contrast", "area"])

    # 3. Loop setiap gambar
    for path in image_paths:
        img_name = os.path.basename(path)
        print(f"[PROCESS] Memproses: {img_name}")

        img = cv2.imread(path)
        if img is None:
            print(f"⚠️ Gagal membaca {img_name}")
            continue

        # Preprocessing
        hsv = preprocess_image(img)

        # Segmentasi
        segmented, mask = segment_image(hsv)

        # Ekstraksi fitur
        hue, texture, area = extract_features(segmented, mask)

        # Simpan hasil segmentasi
        out_path = os.path.join(SEGMENTED_DIR, img_name)
        save_image(out_path, cv2.cvtColor(segmented, cv2.COLOR_HSV2BGR))

        # Simpan fitur ke CSV
        writer.writerow([img_name, hue, texture, area])

print("✅ Selesai! Semua hasil disimpan di folder dataset/")
