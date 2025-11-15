# file: feature_extraction.py
import cv2
import numpy as np
from skimage.feature import graycomatrix, graycoprops

def extract_features(segmented_img, mask):
    """
    Ekstraksi fitur buah naga dari hasil segmentasi.
    Output:
        area_cm2       : luas objek dalam cm² (berdasarkan kalibrasi nyata)
        width_cm       : lebar buah dalam cm
        height_cm      : tinggi buah dalam cm
        weight_est_g   : estimasi berat buah (gram)
        texture_score  : nilai kekasaran permukaan (0–1)
        hue_mean       : rata-rata hue warna kulit (0–1)
    """

    # 1) validasi mask
    if mask is None or np.count_nonzero(mask) == 0:
        return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0

    # 2) kontur terbesar
    c = max(contours, key=cv2.contourArea)
    area_px = float(cv2.contourArea(c))
    x, y, w_box, h_box = cv2.boundingRect(c)

    # 3) kalibrasi px -> cm (berdasarkan data nyata)
    pixel_per_cm = 102.0   # default: 3060 px ≈ 30 cm → 102 px per cm
    cm_per_pixel = 1.0 / pixel_per_cm

    # sedikit koreksi dimensi (kompensasi bounding box vs objek)
    width_cm = (w_box * cm_per_pixel) * 0.9
    height_cm = (h_box * cm_per_pixel) * 0.9
    area_cm2 = area_px * (cm_per_pixel ** 2)

    # 4) estimasi berat (gram) — k dapat dikalibrasi dengan load-cell
    k = 2.0      # nilai konservatif; ubah jika perlu (2.95 sebelumnya tampak overestimate pada beberapa dataset)
    p = 1.15
    weight_est_g = k * (area_cm2 ** p)

    # 5) konversi ke HSV untuk ekstraksi warna & tekstur
    if len(segmented_img.shape) == 3:
        hsv = cv2.cvtColor(segmented_img, cv2.COLOR_BGR2HSV)
        h_ch, s_ch, v_ch = cv2.split(hsv)
    else:
        h_ch = s_ch = v_ch = segmented_img

    # 6) crop berdasarkan bounding box untuk fokus region
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(hsv.shape[1], x + w_box), min(hsv.shape[0], y + h_box)
    s_crop = s_ch[y0:y1, x0:x1]
    v_crop = v_ch[y0:y1, x0:x1]
    h_crop = h_ch[y0:y1, x0:x1]
    mask_crop = mask[y0:y1, x0:x1]

    if np.count_nonzero(mask_crop) == 0:
        hue_mean = float(np.mean(h_ch[mask > 0]) / 180.0) if np.count_nonzero(mask) > 0 else 0.0
        return round(area_cm2,4), round(width_cm,3), round(height_cm,3), round(weight_est_g,3), 0.0, round(hue_mean,6)

    # 7) ekstraksi fitur tekstur menggunakan GLCM
    def compute_glcm_score(img_channel, mask_local):
        levels = 64
        norm = cv2.normalize(img_channel, None, 0, levels - 1, cv2.NORM_MINMAX).astype(np.uint8)
        masked = np.where(mask_local > 0, norm, 0).astype(np.uint8)
        if np.count_nonzero(mask_local) < 10:
            return 0.0
        try:
            glcm = graycomatrix(masked,
                                distances=[1, 2],
                                angles=[0, np.pi/4, np.pi/2],
                                levels=levels,
                                symmetric=True,
                                normed=True)
            contrast = float(np.mean(graycoprops(glcm, 'contrast')))
            homogeneity = float(np.mean(graycoprops(glcm, 'homogeneity')))
            energy = float(np.mean(graycoprops(glcm, 'energy')))
            # score: higher homogeneity+energy => halus; higher contrast => kasar
            raw = (homogeneity + energy) / 2.0
            # penalize by contrast
            score = raw * (1.0 - contrast / (contrast + 0.3))
            return float(score)
        except Exception:
            return 0.0

    s_score = compute_glcm_score(s_crop, mask_crop)
    v_score = compute_glcm_score(v_crop, mask_crop)

    # gabungkan S & V (memberi bobot kecil ke V)
    raw_texture = 0.7 * s_score + 0.3 * v_score

    # perluas rentang kecil → gunakan tanh untuk menaikkan nilai kecil
    texture_score = np.tanh(raw_texture * 3.5)   # skala empiris; hasil di (0,1)
    texture_score = float(np.clip(texture_score, 0.0, 1.0))

    # 8) hue rata-rata (0..1)
    region_h = h_crop[mask_crop > 0]
    hue_mean = float(np.mean(region_h) / 180.0) if region_h.size > 0 else 0.0

    return (
        round(area_cm2, 4),
        round(width_cm, 3),
        round(height_cm, 3),
        round(weight_est_g, 3),
        round(texture_score, 6),
        round(hue_mean, 6)
    )
