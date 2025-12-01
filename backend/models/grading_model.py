# models/grading_model.py

from sqlalchemy import Column, String, Float, DateTime, func, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
import uuid
from core.database import Base


class GradingResult(Base):
    __tablename__ = "grading_results"

    # Primary key
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # PCV features (sesuai extract_features di main.py)
    length_cm = Column(Float, nullable=True)       # max(w_box, h_box) * cm_per_pixel * 0.9
    diameter_cm = Column(Float, nullable=True)     # min(w_box, h_box) * cm_per_pixel * 0.9
    weight_est_g = Column(Float, nullable=True)    # estimasi berat dari citra (gram)
    ratio = Column(Float, nullable=True)           # length_cm / diameter_cm

    # Berat aktual dari sensor (opsional)
    weight_actual_g = Column(Float, nullable=True)

    # Fuzzy result (score-only)
    fuzzy_score = Column(Float, nullable=True)

    # Final decision grade
    final_grade = Column(String, nullable=True)

    # Timestamp (matches existing database column)
    tanggal = Column(DateTime(timezone=True), server_default=func.now(), nullable=True, index=True)

    def __repr__(self):
        return f"<GradingResult id={self.id} final_grade={self.final_grade} weight_est={self.weight_est_g}>"

# (Optional) combined index defined in Python (already indexed individually above)
# Index('ix_grading_results_source_created', GradingResult.source, GradingResult.created_at)