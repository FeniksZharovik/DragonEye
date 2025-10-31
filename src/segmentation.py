import cv2
import numpy as np

def segment_image(hsv):
    """
    Segmentasi buah naga berdasarkan warna merah, hijau, dan kuning
    dengan pendekatan adaptif.
    """

    # --- Warna merah / magenta ---
    lower_red1 = np.array([0, 40, 40])
    upper_red1 = np.array([15, 255, 255])
    lower_red2 = np.array([160, 40, 40])
    upper_red2 = np.array([180, 255, 255])

    # --- Warna hijau ---
    lower_green = np.array([35, 30, 40])
    upper_green = np.array([85, 255, 255])

    # --- Warna kuning (transisi antara hijau dan merah) ---
    lower_yellow = np.array([20, 30, 50])
    upper_yellow = np.array([35, 255, 255])

    # --- Gabungkan semua range warna ---
    mask_red = cv2.bitwise_or(cv2.inRange(hsv, lower_red1, upper_red1),
                              cv2.inRange(hsv, lower_red2, upper_red2))
    mask_green = cv2.inRange(hsv, lower_green, upper_green)
    mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)

    # Gabungkan semua warna jadi satu mask besar
    mask = cv2.bitwise_or(mask_red, mask_green)
    mask = cv2.bitwise_or(mask, mask_yellow)

    # --- Filter adaptif berdasarkan Saturation & Value ---
    s = hsv[:, :, 1]
    v = hsv[:, :, 2]
    adaptive_mask = cv2.inRange(s, 30, 255)
    adaptive_mask = cv2.bitwise_and(adaptive_mask, cv2.inRange(v, 40, 255))
    mask = cv2.bitwise_and(mask, adaptive_mask)

    # --- Bersihkan noise kecil dan isi lubang ---
    kernel = np.ones((7, 7), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    # --- Ambil kontur terbesar (area buah utama) ---
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        filled_mask = np.zeros_like(mask)
        cv2.drawContours(filled_mask, [max(contours, key=cv2.contourArea)], -1, 255, -1)
        mask = filled_mask

    segmented = cv2.bitwise_and(hsv, hsv, mask=mask)
    return segmented, mask
