# controllers/grading_controller.py

from services.pcv.preprocess import preprocess_image
from services.pcv.segmentation import segment_image
from services.pcv.feature_extract import extract_length_diameter_weight
from services.pcv.normalization import normalize_features
from services.fuzzy.mamdani import compute_fuzzy_score
from services.grading_service import combine_final_grade
from models.grading_model import GradingResult
from core.database import SessionLocal


def process_and_grade_image(img, filename):
    db = SessionLocal()

    # =====================================================
    # 1. Preprocessing (HSV)
    # =====================================================
    hsv = preprocess_image(img)

    # =====================================================
    # 2. Segmentasi → menghasilkan mask
    # =====================================================
    segmented, mask = segment_image(hsv)

    # =====================================================
    # 3. Ekstraksi fitur BARU (tanpa area/texture/hue)
    #    return:
    #       length_cm, diameter_cm, weight_est_g, ratio
    # =====================================================
    length_cm, diameter_cm, weight_est_g, ratio = extract_length_diameter_weight(segmented, mask)

    # =====================================================
    # 4. Normalisasi fitur BARU
    #    return:
    #       length_norm, diameter_norm, weight_norm, ratio_norm
    # =====================================================
    (length_norm,
     diameter_norm,
     weight_norm,
     ratio_norm) = normalize_features(
         length_cm,
         diameter_cm,
         weight_est_g,
         ratio
     )

    # =====================================================
    # 5. Hitung fuzzy score (HANYA 4 fitur)
    # =====================================================
    fuzzy_score = compute_fuzzy_score(
        length_norm,
        diameter_norm,
        weight_norm,
        ratio_norm
    )

    # =====================================================
    # 6. Grading berdasarkan berat aktual ESTIMASI
    # =====================================================
    if weight_est_g >= 350:
        grade_weight = "A"
    elif weight_est_g >= 250:
        grade_weight = "B"
    else:
        grade_weight = "C"

    # =====================================================
    # 7. Final grade berdasarkan fuzzy + berat
    # =====================================================
    final_grade = combine_final_grade(grade_weight, fuzzy_score)

    # =====================================================
    # 8. SIMPAN ke database (model BARU)
    # =====================================================
    record = GradingResult(
        length_cm=length_cm,
        diameter_cm=diameter_cm,
        weight_est_g=weight_est_g,
        ratio=ratio,

        # nilai aktual belum ada → default None
        weight_actual_g=None,

        # normalized
        length_norm=length_norm,
        diameter_norm=diameter_norm,
        weight_norm=weight_norm,
        ratio_norm=ratio_norm,

        fuzzy_score=fuzzy_score,
        final_grade=final_grade
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return record