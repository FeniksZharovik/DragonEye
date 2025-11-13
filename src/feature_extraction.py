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

    # =====================================================
    # 1️⃣ Validasi input mask
    # =====================================================
    if mask is None or np.count_nonzero(mask) == 0:
        return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0

    # =====================================================
    # 2️⃣ Ambil kontur terbesar (buah utama)
    # =====================================================
    c = max(contours, key=cv2.contourArea)
    area_px = float(cv2.contourArea(c))
    x, y, w_box, h_box = cv2.boundingRect(c)

    # =====================================================
    # 3️⃣ Kalibrasi piksel → cm (berdasarkan data nyata)
    # =====================================================
    # Real: 3060 px ≈ 30 cm → 1 cm = 102 px
    pixel_per_cm = 102.0
    cm_per_pixel = 1.0 / pixel_per_cm

    # Koreksi dimensi sedikit agar proporsional terhadap bentuk buah
    width_cm = (w_box * cm_per_pixel) * 0.9
    height_cm = (h_box * cm_per_pixel) * 0.9
    area_cm2 = area_px * (cm_per_pixel ** 2)

    # =====================================================
    # 4️⃣ Estimasi berat (gram)
    # =====================================================
    # Berdasarkan data nyata:
    # area ≈ 134.9 cm² → berat ≈ 525 gram
    # k = 525 / (134.9 ^ 1.15) ≈ 2.95
    k = 2.95
    weight_est_g = k * (area_cm2 ** 1.15)

    # =====================================================
    # 5️⃣ Konversi ke HSV untuk ekstraksi warna & tekstur
    # =====================================================
    if len(segmented_img.shape) == 3:
        hsv = cv2.cvtColor(segmented_img, cv2.COLOR_BGR2HSV)
        h_ch, s_ch, v_ch = cv2.split(hsv)
    else:
        h_ch = s_ch = v_ch = segmented_img

    # =====================================================
    # 6️⃣ Crop area buah berdasarkan bounding box
    # =====================================================
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(hsv.shape[1], x + w_box), min(hsv.shape[0], y + h_box)
    s_crop = s_ch[y0:y1, x0:x1]
    h_crop = h_ch[y0:y1, x0:x1]
    mask_crop = mask[y0:y1, x0:x1]

    if np.count_nonzero(mask_crop) == 0:
        hue_mean = float(np.mean(h_ch[mask > 0]) / 180.0) if np.count_nonzero(mask) > 0 else 0.0
        return area_cm2, width_cm, height_cm, weight_est_g, 0.0, hue_mean

    # =====================================================
    # 7️⃣ Ekstraksi fitur tekstur menggunakan GLCM
    # =====================================================
    levels = 64
    s_norm = cv2.normalize(s_crop, None, 0, levels - 1, cv2.NORM_MINMAX).astype(np.uint8)
    s_masked = np.where(mask_crop > 0, s_norm, 0).astype(np.uint8)

    if np.count_nonzero(mask_crop) < 10:
        texture_score = 0.0
    else:
        glcm = graycomatrix(
            s_masked,
            distances=[1, 2, 3],
            angles=[0, np.pi / 4, np.pi / 2],
            levels=levels,
            symmetric=True,
            normed=True
        )
        contrast = float(np.mean(graycoprops(glcm, 'contrast')))
        homogeneity = float(np.mean(graycoprops(glcm, 'homogeneity')))
        energy = float(np.mean(graycoprops(glcm, 'energy')))

        # Rumus yang menyeimbangkan halus vs kasar (0–1)
        texture_score = ((homogeneity + energy) / 2.0) * (1.0 - contrast / (contrast + 0.3))
        # Perluas rentang supaya nilai tidak terlalu kecil
        texture_score = min(max(texture_score * 2.5, 0), 1.0)

    # =====================================================
    # 8️⃣ Ekstraksi warna (Hue rata-rata, 0–1)
    # =====================================================
    region_h = h_crop[mask_crop > 0]
    hue_mean = float(np.mean(region_h) / 180.0) if region_h.size > 0 else 0.0

    # =====================================================
    # 9️⃣ Kembalikan fitur utama
    # =====================================================
    return (
        round(area_cm2, 4),
        round(width_cm, 3),
        round(height_cm, 3),
        round(weight_est_g, 3),
        round(texture_score, 6),
        round(hue_mean, 6)
    )
