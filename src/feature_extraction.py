import cv2
import numpy as np
from skimage.feature import graycomatrix, graycoprops

def extract_features(segmented_img, mask):
    """Ekstraksi fitur warna, tekstur, dan ukuran"""
    # --- Warna (Hue) ---
    hue_channel = segmented_img[:, :, 0]
    hue_mean = np.mean(hue_channel[mask > 0])

    # --- Tekstur (GLCM) ---
    gray = cv2.cvtColor(segmented_img, cv2.COLOR_HSV2BGR)
    gray = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY)
    glcm = graycomatrix(gray, [1], [0], symmetric=True, normed=True)
    contrast = graycoprops(glcm, 'contrast')[0, 0]
    homogeneity = graycoprops(glcm, 'homogeneity')[0, 0]

    # --- Ukuran (Area) ---
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    area = cv2.contourArea(contours[0]) if contours else 0

    # --- Normalisasi fitur ---
    hue_norm = hue_mean / 180.0
    contrast_norm = contrast / 10.0
    area_norm = area / (256 * 256)

    return hue_norm, contrast_norm, area_norm
