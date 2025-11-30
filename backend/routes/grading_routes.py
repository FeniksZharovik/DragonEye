
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
import numpy as np
import cv2
from sqlalchemy.orm import Session
import logging

from core.database import get_db
from services.grading_service import process_image
from models.schemas import GradingResultResponse

logger = logging.getLogger(__name__)
router = APIRouter()

# =====================================================================
# ENDPOINT: /grade-image
# =====================================================================
@router.post("/grade-image", response_model=GradingResultResponse)
async def grade_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Menerima upload gambar → menjalankan PCV → fuzzy → simpan DB → MQTT publish.
    Semua dilakukan di process_image(). Endpoint hanya menerima & mengembalikan hasil.
    """

    # 1) Validasi input file
    filename = file.filename
    img_bytes = await file.read()

    if not img_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File upload kosong."
        )

    img_arr = np.frombuffer(img_bytes, np.uint8)
    img_np = cv2.imdecode(img_arr, cv2.IMREAD_COLOR)

    if img_np is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File bukan gambar valid atau format tidak didukung."
        )

    # 2) Proses grading (sudah termasuk simpan DB + publish MQTT)
    try:
        result, err_msg = process_image(
            image_bgr=img_np,
            reference_df=None,
            filename=filename,
            db=db,
            publish_mqtt=True,
            fuzzy_fallback_on_invalid_weight=True
        )
    except Exception as e:
        logger.exception(f"Error saat proses grading: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Processing error."
        )

    if err_msg:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=err_msg
        )

    return result