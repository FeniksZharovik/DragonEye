import cv2
import numpy as np

def segment_image(hsv):
    """Segmentasi buah naga berdasarkan warna merah adaptif"""
    # Rentang warna merah pertama
    lower_red1 = np.array([0, 40, 40])
    upper_red1 = np.array([15, 255, 255])
    
    # Rentang warna merah kedua (magenta tua)
    lower_red2 = np.array([160, 40, 40])
    upper_red2 = np.array([180, 255, 255])
    
    # Kombinasikan kedua mask
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask = cv2.bitwise_or(mask1, mask2)
    
    # Tambahan: hilangkan noise kecil dan isi lubang
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    
    # Opsional: fill hole dengan kontur terbesar
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        largest_contour = max(contours, key=cv2.contourArea)
        filled_mask = np.zeros_like(mask)
        cv2.drawContours(filled_mask, [largest_contour], -1, 255, thickness=cv2.FILLED)
        mask = filled_mask

    segmented = cv2.bitwise_and(hsv, hsv, mask=mask)
    return segmented, mask
