import cv2
import numpy as np

def segment_image(hsv):

    # --- Warna utama buah naga (merah, hijau, kuning) ---
    lower_red1 = np.array([0, 40, 40])
    upper_red1 = np.array([15, 255, 255])
    lower_red2 = np.array([160, 40, 40])
    upper_red2 = np.array([180, 255, 255])
    lower_green = np.array([35, 40, 40])
    upper_green = np.array([90, 255, 255])
    lower_yellow = np.array([20, 40, 40])
    upper_yellow = np.array([45, 255, 255])

    mask_red = cv2.bitwise_or(cv2.inRange(hsv, lower_red1, upper_red1),
                              cv2.inRange(hsv, lower_red2, upper_red2))
    mask_green = cv2.inRange(hsv, lower_green, upper_green)
    mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)
    mask = cv2.bitwise_or(mask_red, cv2.bitwise_or(mask_green, mask_yellow))

    # --- Buang background putih / abu & bayangan ---
    bg_light = cv2.inRange(hsv, (0, 0, 160), (180, 60, 255))
    bg_dark = cv2.inRange(hsv, (0, 0, 0), (180, 100, 50))
    bg_mask = cv2.bitwise_or(bg_light, bg_dark)
    mask = cv2.bitwise_and(mask, cv2.bitwise_not(bg_mask))

    # --- Bersihkan noise dan haluskan tepi ---
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)

    # --- Refinement lembut untuk sisa tipis background ---
    # Fokus: area terang tapi tidak terlalu jenuh (warna abu tipis di pinggir)
    edge_refine = cv2.inRange(hsv, (0, 0, 130), (180, 70, 255))
    edge_refine = cv2.GaussianBlur(edge_refine, (5, 5), 0)
    edge_refine = cv2.dilate(edge_refine, kernel, iterations=1)
    mask = cv2.bitwise_and(mask, cv2.bitwise_not(edge_refine))

    # --- Ambil kontur terbesar (buah utama) ---
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        filled_mask = np.zeros_like(mask)
        cv2.drawContours(filled_mask, [max(contours, key=cv2.contourArea)], -1, 255, -1)
        mask = filled_mask

    # --- Feathering ringan untuk tepi (hilangkan garis keras) ---
    mask_blur = cv2.GaussianBlur(mask, (3, 3), 0)
    _, mask_final = cv2.threshold(mask_blur, 100, 255, cv2.THRESH_BINARY)

    # --- Terapkan mask akhir ke citra ---
    segmented = cv2.bitwise_and(hsv, hsv, mask=mask_final)
    return segmented, mask_final
