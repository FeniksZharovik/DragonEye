# models/schemas.py

from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional
from datetime import datetime


# ----------------------------
# CREATE (input dari program)
# ----------------------------
class GradingResultCreate(BaseModel):
    source: Optional[str] = None

    # PCV features
    length_cm: Optional[float] = None
    diameter_cm: Optional[float] = None
    weight_est_g: Optional[float] = None
    ratio: Optional[float] = None

    # Berat aktual
    weight_actual_g: Optional[float] = None

    # Fuzzy result
    fuzzy_score: Optional[float] = None

    # Grading
    final_grade: Optional[str] = None

    class Config:
        from_attributes = True  # Pydantic V2


# ----------------------------
# RESPONSE (kembalian dari DB)
# ----------------------------
class GradingResultResponse(GradingResultCreate):
    id: UUID = Field(...)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True  # Pydantic V2