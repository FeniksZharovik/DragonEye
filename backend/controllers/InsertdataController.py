"""
InsertdataController.py

Controller untuk menerima dan menyimpan hasil grading dari IoT/Camera
ke database table grading_results
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

from core.database import get_db
from models.grading_model import GradingResult
from models.schemas import GradingResultCreate, GradingResultResponse

# Logger
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/insertdata", tags=["Insert Data"])


# ============================================================
# DATA CLASS untuk handle grading result dari camera/iot
# ============================================================
class GradingDataBuffer:
    """
    Buffer untuk menyimpan hasil grading sebelum insert ke DB
    
    Digunakan untuk:
    - Menerima data dari IoT/Camera
    - Validasi data
    - Store temporary
    - Insert ke database
    """
    
    def __init__(self):
        self.data: Dict[str, Any] = {}
        self.last_inserted: Optional[GradingResult] = None
        self.is_valid = False
    
    def set_grading_result(
        self,
        grade: str,
        score: float,
        length: float,
        diameter: float,
        weight: float,
        ratio: float
    ) -> bool:
        """
        Set hasil grading ke buffer
        
        Args:
            grade: Grade dari fuzzy logic ('A', 'B', 'C')
            score: Fuzzy score (0-100)
            length: Panjang buah (cm)
            diameter: Diameter buah (cm)
            weight: Berat estimasi (g)
            ratio: Ratio L/D
        
        Returns:
            True jika valid, False jika ada error
        """
        try:
            # Validate data
            if not isinstance(grade, str) or grade not in ['A', 'B', 'C']:
                raise ValueError(f"Grade harus 'A', 'B', atau 'C', dapat: {grade}")
            
            if not (0 <= score <= 100):
                raise ValueError(f"Score harus 0-100, dapat: {score}")
            
            if length <= 0:
                raise ValueError(f"Length harus > 0, dapat: {length}")
            
            if diameter <= 0:
                raise ValueError(f"Diameter harus > 0, dapat: {diameter}")
            
            if weight <= 0:
                raise ValueError(f"Weight harus > 0, dapat: {weight}")
            
            if ratio <= 0:
                raise ValueError(f"Ratio harus > 0, dapat: {ratio}")
            
            # Store data
            self.data = {
                'grade': grade,
                'score': float(score),
                'length_cm': float(length),
                'diameter_cm': float(diameter),
                'weight_est_g': float(weight),
                'ratio': float(ratio),
                'source': 'camera_iot'
            }
            
            self.is_valid = True
            logger.info(f"✓ Grading data valid dan tersimpan di buffer")
            return True
        
        except Exception as e:
            logger.error(f"✗ Error setting grading result: {e}")
            self.is_valid = False
            return False
    
    def get_data(self) -> Optional[Dict[str, Any]]:
        """Get data dari buffer"""
        if not self.is_valid:
            logger.warning("⚠️ Buffer data tidak valid")
            return None
        return self.data.copy()
    
    def clear(self):
        """Clear buffer"""
        self.data = {}
        self.is_valid = False
        logger.info("✓ Buffer cleared")


# Global buffer instance
grading_buffer = GradingDataBuffer()


# ============================================================
# CONTROLLER FUNCTIONS
# ============================================================

def save_grading_result(
    grading_data: GradingResultCreate,
    db: Session
) -> Optional[GradingResult]:
    """
    Simpan hasil grading ke database
    
    Args:
        grading_data: Data grading (GradingResultCreate schema)
        db: Database session
    
    Returns:
        GradingResult object jika berhasil, None jika error
    """
    try:
        # Create database record
        db_record = GradingResult(
            id=uuid.uuid4(),
            length_cm=grading_data.length_cm,
            diameter_cm=grading_data.diameter_cm,
            weight_est_g=grading_data.weight_est_g,
            ratio=grading_data.ratio,
            weight_actual_g=grading_data.weight_actual_g,
            fuzzy_score=grading_data.fuzzy_score,
            final_grade=grading_data.final_grade
        )
        
        # Add to session & commit
        db.add(db_record)
        db.commit()
        db.refresh(db_record)
        
        # Store reference
        grading_buffer.last_inserted = db_record
        
        logger.info(f"✓ Data berhasil disimpan ke DB → Grade {db_record.final_grade}")
        return db_record
    
    except Exception as e:
        db.rollback()
        logger.error(f"✗ Error menyimpan ke database: {e}")
        return None


# ============================================================
# API ENDPOINTS
# ============================================================

@router.post("/grading-from-camera", response_model=GradingResultResponse)
async def insert_grading_from_camera(
    grading_data: GradingResultCreate,
    db: Session = Depends(get_db)
) -> GradingResultResponse:
    """
    Endpoint untuk menerima & insert hasil grading dari camera/IoT
    
    Request body:
    {
        "length_cm": 12.5,
        "diameter_cm": 8.3,
        "weight_est_g": 450.0,
        "ratio": 1.51,
        "fuzzy_score": 75.5,
        "final_grade": "A"
    }
    
    Response:
    {
        "id": "uuid-string",
        "length_cm": ...,
        ...
        "created_at": "2025-01-01T12:00:00+00:00"
    }
    """
    try:
        # Validate final_grade
        if not grading_data.final_grade:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="final_grade tidak boleh kosong"
            )
        
        # Save to database
        result = save_grading_result(grading_data, db)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Gagal menyimpan ke database"
            )
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/grading-buffer", response_model=Dict[str, Any])
async def set_grading_buffer(
    grade: str,
    score: float,
    length: float,
    diameter: float,
    weight: float,
    ratio: float
) -> Dict[str, Any]:
    """
    Set hasil grading ke buffer (step 1 sebelum insert)
    
    Query Parameters:
    - grade: 'A', 'B', atau 'C'
    - score: 0-100
    - length: cm
    - diameter: cm
    - weight: gram
    - ratio: L/D
    
    Response:
    {
        "status": "success",
        "message": "Data tersimpan di buffer",
        "data": {...}
    }
    """
    try:
        # Validate & store to buffer
        success = grading_buffer.set_grading_result(
            grade=grade,
            score=score,
            length=length,
            diameter=diameter,
            weight=weight,
            ratio=ratio
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Data tidak valid"
            )
        
        return {
            "status": "success",
            "message": "✓ Data tersimpan di buffer, siap di-insert ke DB",
            "data": grading_buffer.get_data()
        }
    
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/insert-from-buffer", response_model=GradingResultResponse)
async def insert_from_buffer(db: Session = Depends(get_db)) -> GradingResultResponse:
    """
    Insert data dari buffer ke database (step 2)
    
    Response:
    {
        "id": "uuid",
        "final_grade": "A",
        ...
    }
    """
    try:
        # Get data dari buffer
        data_dict = grading_buffer.get_data()
        
        if not data_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Buffer kosong atau tidak valid"
            )
        
        # Convert ke schema
        grading_data = GradingResultCreate(
            source=data_dict.get('source', 'camera_iot'),
            length_cm=data_dict.get('length_cm'),
            diameter_cm=data_dict.get('diameter_cm'),
            weight_est_g=data_dict.get('weight_est_g'),
            ratio=data_dict.get('ratio'),
            fuzzy_score=data_dict.get('score'),
            final_grade=data_dict.get('grade')
        )
        
        # Save to database
        result = save_grading_result(grading_data, db)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Gagal insert ke database"
            )
        
        # Clear buffer after successful insert
        grading_buffer.clear()
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/buffer-status", response_model=Dict[str, Any])
async def get_buffer_status() -> Dict[str, Any]:
    """
    Check status buffer
    
    Response:
    {
        "is_valid": true/false,
        "has_data": true/false,
        "data": {...} atau null,
        "last_inserted": {...} atau null
    }
    """
    return {
        "is_valid": grading_buffer.is_valid,
        "has_data": len(grading_buffer.data) > 0,
        "data": grading_buffer.get_data(),
        "last_inserted_id": str(grading_buffer.last_inserted.id) if grading_buffer.last_inserted else None,
        "last_inserted_grade": grading_buffer.last_inserted.final_grade if grading_buffer.last_inserted else None
    }


@router.delete("/clear-buffer", response_model=Dict[str, str])
async def clear_buffer() -> Dict[str, str]:
    """Clear buffer"""
    grading_buffer.clear()
    return {"status": "success", "message": "✓ Buffer cleared"}


# ============================================================
# BATCH OPERATIONS
# ============================================================

@router.post("/batch-insert", response_model=Dict[str, Any])
async def batch_insert(
    data_list: list[GradingResultCreate],
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Insert multiple grading results sekaligus
    
    Request body:
    [
        {
            "length_cm": 12.5,
            "diameter_cm": 8.3,
            ...
        },
        {
            "length_cm": 13.2,
            "diameter_cm": 9.1,
            ...
        }
    ]
    
    Response:
    {
        "total": 2,
        "inserted": 2,
        "failed": 0,
        "results": [...]
    }
    """
    try:
        inserted_count = 0
        failed_count = 0
        results = []
        
        for grading_data in data_list:
            result = save_grading_result(grading_data, db)
            
            if result:
                inserted_count += 1
                results.append({
                    "id": str(result.id),
                    "status": "success"
                })
            else:
                failed_count += 1
                results.append({
                    "status": "failed"
                })
        
        return {
            "total": len(data_list),
            "inserted": inserted_count,
            "failed": failed_count,
            "results": results
        }
    
    except Exception as e:
        logger.exception(f"Batch insert error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
