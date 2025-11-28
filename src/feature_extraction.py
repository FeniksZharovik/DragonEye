# file: feature_extraction.py
import cv2
import numpy as np
import math

def extract_features(segmented_img, mask):

    if mask is None or np.count_nonzero(mask) == 0:
        return 0.0, 0.0, 0.0, 0.0

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return 0.0, 0.0, 0.0, 0.0

    c = max(contours, key=cv2.contourArea)
    x, y, w_box, h_box = cv2.boundingRect(c)

    pixel_per_cm = 102.0
    cm_per_pixel = 1.0 / pixel_per_cm

    length_cm = max(w_box, h_box) * cm_per_pixel * 0.9
    diameter_cm = min(w_box, h_box) * cm_per_pixel * 0.9
    ratio = length_cm / diameter_cm if diameter_cm > 0 else 0.0

    # ----------------------------------------
    # Estimasi berat berbasis volume (Modified)
    # ----------------------------------------
    radius = diameter_cm / 2
    volume_cm3 = math.pi * (radius ** 2) * length_cm

    density = 0.22  # density rata-rata buah naga
    weight_est_g = density * volume_cm3

    # Scaling (Adjusted)
    weight_est_g *= 1.32     # scaling ditingkatkan

    weight_est_g = max(weight_est_g, 0)

    return (
        round(length_cm, 3),
        round(diameter_cm, 3),
        round(weight_est_g, 3),
        round(ratio, 4)
    )
