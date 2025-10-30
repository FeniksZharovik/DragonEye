import cv2
import numpy as np
import os

def segment_image_keep_rgb(image_path, output_path):
    """
    Segmentasi buah naga dari background putih (termasuk bayangan).
    - Mempertahankan warna RGB
    - Adaptif terhadap variasi pencahayaan
    - Gunakan gabungan warna, saturasi, dan edge detection
    """

    # --- Baca citra ---
    image = cv2.imread(image_path)
    if image is None:
        print(f"[WARNING] Gagal membaca {image_path}")
        return

    # --- Konversi ke HSV ---
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)

    # --- Mask warna buah naga (merah–kuning–magenta) ---
    mask1 = cv2.inRange(hsv, (0, 50, 40), (40, 255, 255))     # merah → kuning
    mask2 = cv2.inRange(hsv, (140, 50, 40), (179, 255, 255))  # magenta → merah
    color_mask = cv2.bitwise_or(mask1, mask2)

    # --- Tambahkan deteksi tepi (untuk menangkap batas objek) ---
    edges = cv2.Canny(v, 60, 150)
    edges = cv2.dilate(edges, None, iterations=2)

    # --- Gunakan saturasi untuk menolak area putih/bayangan ---
    sat_mask = cv2.inRange(s, 60, 255)

    # --- Gabungkan semua mask ---
    combined = cv2.bitwise_or(color_mask, edges)
    combined = cv2.bitwise_and(combined, sat_mask)

    # --- Perhalus dan isi lubang ---
    mask = cv2.medianBlur(combined, 5)
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)

    # Isi lubang internal
    mask_flood = mask.copy()
    h, w = mask.shape[:2]
    flood_temp = np.zeros((h+2, w+2), np.uint8)
    cv2.floodFill(mask_flood, flood_temp, (0,0), 255)
    mask_inv = cv2.bitwise_not(mask_flood)
    mask = mask | mask_inv

    # --- Terapkan mask ---
    segmented = cv2.bitwise_and(image, image, mask=mask)

    # --- Simpan hasil ---
    os.makedirs(output_path, exist_ok=True)
    filename = f"segmented_{os.path.basename(image_path)}"
    output_file = os.path.join(output_path, filename)
    cv2.imwrite(output_file, segmented, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    print(f"[INFO] Saved: {output_file}")

def segment_folder_keep_rgb(input_folder, output_folder):
    """Proses semua gambar dalam folder."""
    for root, _, files in os.walk(input_folder):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                in_path = os.path.join(root, file)
                rel_path = os.path.relpath(root, input_folder)
                out_sub = os.path.join(output_folder, rel_path)
                segment_image_keep_rgb(in_path, out_sub)

if __name__ == "__main__":
    input_folder = r"E:\DragonEye\dataset\processed"
    output_folder = r"E:\DragonEye\dataset\segmented_rgb"
    segment_folder_keep_rgb(input_folder, output_folder)
