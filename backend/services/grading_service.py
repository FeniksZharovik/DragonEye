# grading_service.py

import logging
from typing import Any, Dict, Optional, Tuple

import numpy as np
from sqlalchemy.orm import Session

from models.grading_model import GradingResult

# PCV utilities
from services.pcv.preprocess import preprocess_image
from services.pcv.segmentation import segment_image
from services.pcv.feature_extract import extract_features
from services.pcv.normalization import normalize_pct, normalize_fixed

# Fuzzy logic
from services.fuzzy.mamdani import compute_fuzzy_score, grade_from_weight

# MQTT publisher
from services.mqtt_service import publish

logger = logging.getLogger(__name__)

# ============================================================
# SAFE NORMALIZATION
# ============================================================
def _safe_normalize(value: float, series, lo: Optional[float] = None, hi: Optional[float] = None) -> float:
    """
    Percentile → fallback to fixed normalization.
    """
    try:
        if series is not None:
            return normalize_pct(value, series)
    except Exception:
        logger.debug("Percentile normalization failed → fallback.")

    if lo is not None and hi is not None and hi > lo:
        return normalize_fixed(value, lo, hi)

    return 0.0


# ============================================================
# BUILD JSON RESULT PAYLOAD
# ============================================================
def _build_result_payload(db_record: GradingResult) -> Dict[str, Any]:
    return {
        "id": str(db_record.id),
        "length_cm": db_record.length_cm,
        "diameter_cm": db_record.diameter_cm,
        "weight_est_g": db_record.weight_est_g,
        "weight_actual_g": db_record.weight_actual_g,
        "ratio": db_record.ratio,
        "fuzzy_score": float(db_record.fuzzy_score) if db_record.fuzzy_score else None,
        "final_grade": db_record.final_grade,
    }


# ============================================================
# KOMPATIBILITAS LAMA
# ============================================================
def process_grading(
    image_bgr,
    reference_df,
    filename,
    db,
    publish_mqtt=True,
    fuzzy_fallback_on_invalid_weight=True,
    weight_actual_g=None
):
    """Wrapper kompatibel versi lama."""
    return process_image(
        image_bgr=image_bgr,
        reference_df=reference_df,
        filename=filename,
        db=db,
        publish_mqtt=publish_mqtt,
        fuzzy_fallback_on_invalid_weight=fuzzy_fallback_on_invalid_weight,
        weight_actual_g=weight_actual_g
    )


# ============================================================
# FUNGSI YANG DICARI OLEH camera_controller.py
# ============================================================
def run_fuzzy_and_save(
    image_bgr: np.ndarray,
    filename: str,
    db: Session,
    reference_df=None,
    weight_actual_g=None,
    publish_mqtt=True
):
    """
    Dipanggil oleh camera_controller.py untuk menjalankan PCV + fuzzy dan menyimpan hasil.
    """
    result, err = process_image(
        image_bgr=image_bgr,
        reference_df=reference_df,
        db=db,
        publish_mqtt=publish_mqtt,
        weight_actual_g=weight_actual_g
    )
    return result, err


# ============================================================
# MAIN PROCESS: PCV → FUZZY → DB → MQTT
# ============================================================
def process_image(
    image_bgr: np.ndarray,
    reference_df,
    db: Session,
    publish_mqtt: bool = True,
    fuzzy_fallback_on_invalid_weight: bool = True,
    weight_actual_g: Optional[float] = None
) -> Tuple[Dict[str, Any], Optional[str]]:

    # --- 1. Preprocess image ---
    hsv = preprocess_image(image_bgr)

    # --- 2. Segment image ---
    segmented, mask = segment_image(hsv)

    # --- 3. Extract features ---
    length_cm, diameter_cm, weight_est_g, ratio = extract_features(segmented, mask)

    # --- 4. Normalization ---
    # Pilih kolom dari dataframe referensi dengan aman
    def col(series_name):
        if reference_df is None:
            return None
        if hasattr(reference_df, "get"):
            return reference_df.get(series_name)
        if hasattr(reference_df, "columns") and series_name in reference_df.columns:
            return reference_df[series_name]
        return None

    length_norm = _safe_normalize(length_cm, col("length_cm"), lo=5.0, hi=18.0)
    diameter_norm = _safe_normalize(diameter_cm, col("diameter_cm"), lo=3.0, hi=12.0)
    weight_norm = _safe_normalize(weight_est_g, col("weight_est_g"), lo=150.0, hi=650.0)

    # ratio series
    try:
        if reference_df is not None and hasattr(reference_df, "columns"):
            if "ratio" in reference_df.columns:
                ratio_series = reference_df["ratio"]
            else:
                ratio_series = reference_df["length_cm"] / (reference_df["diameter_cm"] + 1e-9)
        else:
            ratio_series = None
    except Exception:
        ratio_series = None

    ratio_norm = _safe_normalize(ratio, ratio_series, lo=1.0, hi=1.8)

    # --- 5. Fuzzy computation ---
    try:
        fuzzy_score = compute_fuzzy_score(length_norm, diameter_norm, weight_norm, ratio_norm)
    except Exception:
        logger.exception("Fuzzy computation failed.")
        fuzzy_score = 0.0

    # --- 6. Grade by real weight or fuzzy ---
    primary_weight = None
    try:
        primary_weight = float(weight_actual_g) if weight_actual_g else weight_est_g
    except Exception:
        primary_weight = weight_est_g

    # Determine final grade based on weight
    final_grade = grade_from_weight(primary_weight)

    # fallback to fuzzy score if weight is invalid
    if (weight_actual_g is None or weight_actual_g <= 0) and fuzzy_fallback_on_invalid_weight:
        if fuzzy_score >= 70:
            final_grade = "A"
        elif fuzzy_score >= 45:
            final_grade = "B"
            # else → "C"
        else:
            final_grade = "C"

    # --- 7. Save to database ---
    try:
        db_record = GradingResult(
            length_cm=length_cm,
            diameter_cm=diameter_cm,
            weight_est_g=weight_est_g,
            weight_actual_g=weight_actual_g,
            ratio=ratio,
            fuzzy_score=float(fuzzy_score),
            final_grade=final_grade
        )

        db.add(db_record)
        db.commit()
        db.refresh(db_record)

    except Exception as e:
        logger.exception("DB write failed.")
        try:
            db.rollback()
        except Exception:
            logger.exception("DB rollback failed.")
        return {}, f"DB error: {e}"

    result_payload = _build_result_payload(db_record)

    # --- 8. Publish MQTT ---
    if publish_mqtt:
        try:
            publish("grading/result", result_payload)
        except Exception:
            logger.exception("MQTT publish failed (non-fatal).")

    return result_payload, None