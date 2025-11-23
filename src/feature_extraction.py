# file: feature_extraction.py
import cv2
import numpy as np

def extract_features(segmented_img, mask):
    """
    Ekstraksi fitur buah naga hanya berdasarkan dimensi dan estimasi berat.
    Output:
        length          : panjang bounding box (cm)
        diameter        : diameter/lebar bounding box (cm)
        weight_est_g    : estimasi berat (gram)
        ratio           : length / diameter
    """

    # 1) Validasi mask
    if mask is None or np.count_nonzero(mask) == 0:
        return 0.0, 0.0, 0.0, 0.0

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return 0.0, 0.0, 0.0, 0.0

    # 2) Ambil kontur terbesar
    c = max(contours, key=cv2.contourArea)
    area_px = float(cv2.contourArea(c))
    x, y, w_box, h_box = cv2.boundingRect(c)

    # 3) Kalibrasi piksel → cm (berdasarkan 30cm background)
    pixel_per_cm = 102.0        # 3060px ≈ 30cm → 102 px/cm
    cm_per_pixel = 1.0 / pixel_per_cm

    # Bounding box → ukuran fisik
    length_cm = max(w_box, h_box) * cm_per_pixel * 0.9     # sisi terpanjang
    diameter_cm = min(w_box, h_box) * cm_per_pixel * 0.9   # sisi terpendek

    # 4) Hitung luas dalam cm²
    area_cm2 = area_px * (cm_per_pixel ** 2)

    # 5) Estimasi berat berdasarkan luas
    k = 2.0      # konstanta kalibrasi loadcell
    p = 1.15
    weight_est_g = k * (area_cm2 ** p)

    # 6) Rasio bentuk → panjang terhadap diameter
    if diameter_cm > 0:
        ratio = length_cm / diameter_cm
    else:
        ratio = 0.0

    return (
        round(length_cm, 3),
        round(diameter_cm, 3),
        round(weight_est_g, 3),
        round(ratio, 4)
    )
