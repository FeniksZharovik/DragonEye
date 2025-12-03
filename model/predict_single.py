import cv2
import numpy as np
import math
import skfuzzy as fuzz
from skfuzzy import control as ctrl

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

    radius = diameter_cm / 2
    volume_cm3 = math.pi * (radius ** 2) * length_cm

    density = 0.22
    weight_est_g = density * volume_cm3

    weight_est_g *= 1.32
    weight_est_g = max(weight_est_g, 0)

    ratio = length_cm / diameter_cm if diameter_cm > 0 else 0.0

    return (
        round(length_cm, 3),
        round(diameter_cm, 3),
        round(weight_est_g, 3),
        round(ratio, 4)
    )


# ============================
# 4. FUZZY GRADING (single image)
# ============================

def fuzzy_grade_single(length, diameter, weight, ratio):

    # Fungsi keanggotaan untuk normalisasi
    def norm(value, lo, hi):
        return max(0, min(1, (value - lo) / (hi - lo + 1e-9)))

    # Normalisasi
    length_n = norm(length, 5, 18)
    diameter_n = norm(diameter, 3, 12)
    weight_n = norm(weight, 150, 650)
    ratio_n = norm(ratio, 1.0, 1.8)

    # Fuzzy Variables
    length_f = ctrl.Antecedent(np.linspace(0, 1, 101), 'length')
    diameter_f = ctrl.Antecedent(np.linspace(0, 1, 101), 'diameter')
    weight_f = ctrl.Antecedent(np.linspace(0, 1, 101), 'weight')
    ratio_f = ctrl.Antecedent(np.linspace(0, 1, 101), 'ratio')

    grade_f = ctrl.Consequent(np.linspace(0, 100, 101), 'grade')

    # Membership Functions
    length_f['small'] = fuzz.trimf(length_f.universe, [0.0, 0.0, 0.4])
    length_f['medium'] = fuzz.trimf(length_f.universe, [0.3, 0.55, 0.8])
    length_f['large'] = fuzz.trimf(length_f.universe, [0.6, 1.0, 1.0])

    diameter_f['small'] = fuzz.trimf(diameter_f.universe, [0.0, 0.0, 0.4])
    diameter_f['medium'] = fuzz.trimf(diameter_f.universe, [0.3, 0.55, 0.8])
    diameter_f['large'] = fuzz.trimf(diameter_f.universe, [0.6, 1.0, 1.0])

    weight_f['low'] = fuzz.trimf(weight_f.universe, [0.0, 0.0, 0.4])
    weight_f['mid'] = fuzz.trimf(weight_f.universe, [0.3, 0.55, 0.8])
    weight_f['high'] = fuzz.trimf(weight_f.universe, [0.6, 1.0, 1.0])

    ratio_f['poor'] = fuzz.trimf(ratio_f.universe, [0.0, 0.0, 0.4])
    ratio_f['normal'] = fuzz.trimf(ratio_f.universe, [0.3, 0.55, 0.8])
    ratio_f['good'] = fuzz.trimf(ratio_f.universe, [0.6, 1.0, 1.0])

    grade_f['C'] = fuzz.trimf(grade_f.universe, [0, 0, 45])
    grade_f['B'] = fuzz.trimf(grade_f.universe, [35, 60, 85])
    grade_f['A'] = fuzz.trimf(grade_f.universe, [75, 100, 100])

    # Aturan fuzzy
    rules = [
        ctrl.Rule(weight_f['high'] & diameter_f['large'] & length_f['large'], grade_f['A']),
        ctrl.Rule(weight_f['mid'] & diameter_f['medium'], grade_f['B']),
        ctrl.Rule(weight_f['low'] | ratio_f['poor'] | length_f['small'], grade_f['C']),
    ]

    control_sys = ctrl.ControlSystem(rules)
    sim = ctrl.ControlSystemSimulation(control_sys)

    # Input nilai
    sim.input['length'] = length_n
    sim.input['diameter'] = diameter_n
    sim.input['weight'] = weight_n
    sim.input['ratio'] = ratio_n

    # Inferensi
    sim.compute()

    score = sim.output['grade']

    # Tentukan grade berdasarkan standar bobot
    if weight > 350:
        label = "A"
    elif 250 <= weight <= 350:
        label = "B"
    else:
        label = "C"

    return label, score


# ============================
# 5. FINAL PREDICT
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