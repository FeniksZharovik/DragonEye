import cv2
import numpy as np

def extract_features(segmented_img, mask):
    """Ekstraksi fitur ukuran dan estimasi berat"""
    if np.count_nonzero(mask) == 0:
        return 0, 0, 0  # Jika tidak ada area, kembalikan nilai nol

    # --- Ukuran (Area, Panjang, Lebar) ---
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return 0, 0, 0

    c = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(c)
    x, y, w, h = cv2.boundingRect(c)

    # --- Estimasi Berat (berdasarkan area) ---
    k = 0.0025  # Konstanta kalibrasi, sesuaikan dengan data nyata
    weight_est = k * area  # Estimasi berat dalam gram

    # --- Normalisasi Ukuran ---
    area_norm = area / (256 * 256)  # Normalisasi area untuk skala [0, 1]

    return area_norm, w, h, weight_est
