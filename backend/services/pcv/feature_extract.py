import cv2
import numpy as np
import math

def extract_features(segmented_img, mask, pixel_per_cm=102.0, density_g_per_cm3=0.22, scale_factor=1.32):
    """
    Ekstraksi fitur minimal untuk grading:
      - weight_est_g
      - ratio (length/diameter)
    Params:
      - segmented_img: HSV atau BGR hasil segmentasi (tidak digunakan utk tekstur)
      - mask: binary mask (0/255) buah
      - pixel_per_cm: kalibrasi px->cm
      - density_g_per_cm3: density buah (g/cm3)
      - scale_factor: faktor koreksi empiris (pakai 1.0 jika tidak perlu)
    Returns:
      tuple(weight_est_g, ratio)
    """
    # Validasi jika mask kosong
    if mask is None or np.count_nonzero(mask) == 0:
        return 0.0, 0.0

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return 0.0, 0.0

    c = max(contours, key=cv2.contourArea)
    area_px = float(cv2.contourArea(c))
    x, y, w_box, h_box = cv2.boundingRect(c)

    cm_per_pixel = 1.0 / float(pixel_per_cm)

    # Ukuran (kompensasi bounding box vs objek)
    width_cm = (w_box * cm_per_pixel) * 0.9
    height_cm = (h_box * cm_per_pixel) * 0.9

    # Estimasi berat: silinder (sesuai implementasi sebelumnya)
    radius_cm = min(width_cm, height_cm) / 2.0
    length_cm = max(width_cm, height_cm)
    volume_cm3 = math.pi * (radius_cm ** 2) * length_cm

    weight_g = density_g_per_cm3 * volume_cm3
    weight_g *= scale_factor
    weight_g = max(weight_g, 0.0)

    # Ratio (length / diameter)
    ratio = length_cm / (2 * radius_cm) if radius_cm > 0 else 0.0

    return round(weight_g, 3), round(ratio, 4)
