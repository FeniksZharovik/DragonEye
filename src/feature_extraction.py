import cv2
import numpy as np
from skimage.feature import graycomatrix, graycoprops

def extract_features(segmented_img, mask):
    """
    Ekstraksi fitur buah naga:
    Return:
        area (pixel), width, height, weight_est, texture_score, hue_mean
    """

    # Jika mask kosong → kembalikan nol semua
    if mask is None or np.count_nonzero(mask) == 0:
        return 0.0, 0, 0, 0.0, 0.0, 0.0

    # --- Kontur & bounding box untuk area dan crop
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return 0.0, 0, 0, 0.0, 0.0, 0.0

    c = max(contours, key=cv2.contourArea)
    area = float(cv2.contourArea(c))
    x, y, w_box, h_box = cv2.boundingRect(c)   # gunakan nama berbeda untuk lebar/tinggi
    w_box, h_box = int(w_box), int(h_box)

    # Estimasi berat (koefisien empiris; bisa disesuaikan)
    k = 0.004
    weight_est = k * area

    # Pastikan segmented_img dalam 3-channel HSV; jika tidak, buat backup
    hsv = segmented_img.copy()
    if len(hsv.shape) == 3:
        h_ch, s_ch, v_ch = cv2.split(hsv)   # ganti nama channel jadi h_ch, s_ch, v_ch
    else:
        h_ch = s_ch = v_ch = hsv

    # Crop area bounding box untuk mengurangi noise di belakang
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(hsv.shape[1], x + w_box), min(hsv.shape[0], y + h_box)
    s_crop = s_ch[y0:y1, x0:x1]
    h_crop = h_ch[y0:y1, x0:x1]
    mask_crop = mask[y0:y1, x0:x1]

    # Jika crop kosong -> fallback
    if mask_crop is None or mask_crop.size == 0 or np.count_nonzero(mask_crop) == 0:
        hue_mean = float(np.mean(h_ch[mask > 0]) / 180.0) if np.count_nonzero(mask) > 0 else 0.0
        return area, w_box, h_box, weight_est, 0.0, hue_mean

    # Ambil pixel region (hanya nilai di dalam mask)
    region_s = s_crop[mask_crop > 0]
    region_h = h_crop[mask_crop > 0]

    if region_s.size == 0:
        hue_mean = float(np.mean(region_h) / 180.0) if region_h.size > 0 else 0.0
        return area, w_box, h_box, weight_est, 0.0, hue_mean

    # --- Hitung Tekstur (GLCM) pada crop
    levels = 64
    s_norm = cv2.normalize(s_crop, None, 0, levels - 1, cv2.NORM_MINMAX).astype(np.uint8)
    s_masked = np.where(mask_crop > 0, s_norm, 0).astype(np.uint8)

    if np.count_nonzero(mask_crop) < 10:
        contrast = homogeneity = energy = 0.0
    else:
        try:
            glcm = graycomatrix(
                s_masked,
                distances=[1, 2],
                angles=[0, np.pi/4, np.pi/2],
                levels=levels,
                symmetric=True,
                normed=True
            )
            contrast = float(np.mean(graycoprops(glcm, 'contrast')))
            homogeneity = float(np.mean(graycoprops(glcm, 'homogeneity')))
            energy = float(np.mean(graycoprops(glcm, 'energy')))
        except Exception:
            contrast = homogeneity = energy = 0.0

    texture_score = (homogeneity + energy) / 2.0 * (1.0 - contrast / (contrast + 1.0))
    hue_mean = float(np.mean(region_h) / 180.0) if region_h.size > 0 else 0.0

    return area, w_box, h_box, weight_est, float(texture_score), hue_mean
