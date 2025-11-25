import cv2
import numpy as np

# ============================
# 1. PREPROCESSING
# ============================

def preprocess_image(img):
    img = cv2.GaussianBlur(img, (3, 3), 0)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    return hsv


# ============================
# 2. SEGMENTATION
# ============================

def segment_image(hsv):
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

    bg_light = cv2.inRange(hsv, (0, 0, 160), (180, 60, 255))
    bg_dark  = cv2.inRange(hsv, (0, 0, 0),   (180, 100, 50))
    bg_mask = cv2.bitwise_or(bg_light, bg_dark)

    mask = cv2.bitwise_and(mask, cv2.bitwise_not(bg_mask))

    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)

    edge_refine = cv2.inRange(hsv, (0, 0, 130), (180, 70, 255))
    edge_refine = cv2.GaussianBlur(edge_refine, (5, 5), 0)
    edge_refine = cv2.dilate(edge_refine, kernel, iterations=1)
    mask = cv2.bitwise_and(mask, cv2.bitwise_not(edge_refine))

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        filled = np.zeros_like(mask)
        cv2.drawContours(filled, [max(contours, key=cv2.contourArea)], -1, 255, -1)
        mask = filled

    mask_blur = cv2.GaussianBlur(mask, (3, 3), 0)
    _, mask_final = cv2.threshold(mask_blur, 100, 255, cv2.THRESH_BINARY)

    segmented = cv2.bitwise_and(hsv, hsv, mask=mask_final)
    return segmented, mask_final


# ============================
# 3. FEATURE EXTRACTION
# ============================

def extract_features(segmented_img, mask):
    if mask is None or np.count_nonzero(mask) == 0:
        return 0, 0, 0, 0

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return 0, 0, 0, 0

    c = max(contours, key=cv2.contourArea)
    area_px = float(cv2.contourArea(c))
    x, y, w_box, h_box = cv2.boundingRect(c)

    pixel_per_cm = 102.0
    cm_per_pixel = 1.0 / pixel_per_cm

    length_cm = max(w_box, h_box) * cm_per_pixel * 0.9
    diameter_cm = min(w_box, h_box) * cm_per_pixel * 0.9

    area_cm2 = area_px * (cm_per_pixel ** 2)

    k = 2.0
    p = 1.15
    weight_est_g = k * (area_cm2 ** p)

    ratio = length_cm / diameter_cm if diameter_cm > 0 else 0

    return (
        round(length_cm, 3),
        round(diameter_cm, 3),
        round(weight_est_g, 3),
        round(ratio, 4)
    )


# ============================
# 4. FUZZY GRADING (single image version)
# ============================

def fuzzy_grade_single(length, diameter, weight, ratio):
    lname = ["small", "medium", "large"]
    dname = ["small", "medium", "large"]
    wname = ["low", "mid", "high"]
    rname = ["poor", "normal", "good"]

    def norm(value, lo, hi):
        return max(0, min(1, (value - lo) / (hi - lo + 1e-9)))

    length_n   = norm(length, 5, 18)
    diameter_n = norm(diameter, 3, 12)
    weight_n   = norm(weight, 150, 650)
    ratio_n    = norm(ratio, 1.0, 1.8)

    # Score fuzzy tetap dihitung
    score = (
        0.35 * weight_n +
        0.25 * diameter_n +
        0.20 * length_n +
        0.20 * ratio_n
    ) * 100

    # Grade mengikuti standar BERAT
    if weight > 350:
        label = "A"
    elif 250 <= weight <= 350:
        label = "B"
    else:
        label = "C"

    return label, score


# ============================
# 5. FINAL PREDICT FUNCTION
# ============================

def predict_single_image(path):
    img = cv2.imread(path)
    if img is None:
        return None, "Gambar tidak dapat dibaca."

    hsv = preprocess_image(img)
    segmented, mask = segment_image(hsv)

    length, diameter, weight, ratio = extract_features(segmented, mask)

    label, score = fuzzy_grade_single(length, diameter, weight, ratio)

    return {
        "grade": label,
        "score": score,
        "length": length,
        "diameter": diameter,
        "weight": weight,
        "ratio": ratio
    }, None
