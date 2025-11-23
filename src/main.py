import os
import cv2
import csv
from config import RAW_DATA_DIR, SEGMENTED_DIR, FEATURE_CSV
from utils import load_all_images, save_image
from preprocessing import preprocess_image
from segmentation import segment_image
from feature_extraction import extract_features

# 1️⃣ Load semua gambar
image_paths = load_all_images(RAW_DATA_DIR)
print(f"[INFO] Total gambar ditemukan: {len(image_paths)}")

# 2️⃣ Cek apakah CSV sudah ada
file_exists = os.path.exists(FEATURE_CSV)

# 3️⃣ Tulis ke CSV (append agar data baru tidak menimpa yang lama)
with open(FEATURE_CSV, mode='a', newline='') as file:
    writer = csv.writer(file)

    # 4️⃣ Jika CSV belum ada, buat header baru
    if not file_exists:
        writer.writerow([
            "filename",
            "length_cm",
            "diameter_cm",
            "weight_est_g",
            "ratio_ld"
        ])

    # 5️⃣ Proses setiap gambar
    for path in image_paths:
        img_name = os.path.basename(path)
        print(f"[PROCESS] Memproses: {img_name}")

        img = cv2.imread(path)
        if img is None:
            print(f" Gagal membaca {img_name}")
            continue

        # Preprocessing (HSV, noise removal, dsb.)
        hsv = preprocess_image(img)

        # Segmentasi
        segmented, mask = segment_image(hsv)

        # Ekstraksi fitur (versi baru)
        length_cm, diameter_cm, weight_est_g, ratio_ld = extract_features(segmented, mask)

        # Simpan gambar hasil segmentasi
        out_path = os.path.join(SEGMENTED_DIR, img_name)
        save_image(out_path, cv2.cvtColor(segmented, cv2.COLOR_HSV2BGR))

        # Simpan data fitur ke CSV
        writer.writerow([
            img_name,
            length_cm,
            diameter_cm,
            weight_est_g,
            ratio_ld
        ])

print("\n[OK] Ekstraksi fitur selesai!")
print(f"     File CSV tersimpan di: {FEATURE_CSV}")
