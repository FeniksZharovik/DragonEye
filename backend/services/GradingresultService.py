# services/GradingresultService.py

from sqlalchemy.orm import Session
from models.grading_model import GradingResult
from models.schemas import GradingResultCreate, GradingResultResponse
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class GradingresultService:
    """Service layer for Grading Results CRUD operations"""

    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> List[GradingResult]:
        """Fetch all grading results from the database"""
        try:
            results = self.db.query(GradingResult).all()
            logger.info(f"Fetched {len(results)} grading results")
            return results
        except Exception as e:
            logger.error(f"Error fetching all grading results: {str(e)}")
            raise

    def get_by_id(self, result_id: str) -> Optional[GradingResult]:
        """Fetch a single grading result by ID"""
        try:
            result = self.db.query(GradingResult).filter(
                GradingResult.id == result_id
            ).first()
            if result:
                logger.info(f"Fetched grading result with ID: {result_id}")
            else:
                logger.warning(f"Grading result not found with ID: {result_id}")
            return result
        except Exception as e:
            logger.error(f"Error fetching grading result by ID {result_id}: {str(e)}")
            raise

    def get_by_filename(self, filename: str) -> Optional[GradingResult]:
        """Fetch grading results by filename"""
        try:
            results = self.db.query(GradingResult).filter(
                GradingResult.filename == filename
            ).all()
            logger.info(f"Fetched {len(results)} results for filename: {filename}")
            return results
        except Exception as e:
            logger.error(f"Error fetching grading result by filename {filename}: {str(e)}")
            raise

    def create(self, grading_data: GradingResultCreate) -> GradingResult:
        """Create a new grading result"""
        try:
            db_result = GradingResult(**grading_data.dict())
            self.db.add(db_result)
            self.db.commit()
            self.db.refresh(db_result)
            logger.info(f"Created grading result with ID: {db_result.id}")
            return db_result
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating grading result: {str(e)}")
            raise

    def update(self, result_id: str, grading_data: GradingResultCreate) -> Optional[GradingResult]:
        """Update an existing grading result"""
        try:
            db_result = self.db.query(GradingResult).filter(
                GradingResult.id == result_id
            ).first()
            
            if not db_result:
                logger.warning(f"Grading result not found for update: {result_id}")
                return None
            
            # Update fields
            for key, value in grading_data.dict(exclude_unset=True).items():
                setattr(db_result, key, value)
            
            self.db.commit()
            self.db.refresh(db_result)
            logger.info(f"Updated grading result with ID: {result_id}")
            return db_result
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating grading result {result_id}: {str(e)}")
            raise

    def delete(self, result_id: str) -> bool:
        """Delete a grading result"""
        try:
            db_result = self.db.query(GradingResult).filter(
                GradingResult.id == result_id
            ).first()
            
            if not db_result:
                logger.warning(f"Grading result not found for deletion: {result_id}")
                return False
            
            self.db.delete(db_result)
            self.db.commit()
            logger.info(f"Deleted grading result with ID: {result_id}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting grading result {result_id}: {str(e)}")
            raise

    def get_paginated(self, skip: int = 0, limit: int = 10) -> List[GradingResult]:
        """Fetch paginated grading results"""
        try:
            results = self.db.query(GradingResult).offset(skip).limit(limit).all()
            logger.info(f"Fetched {len(results)} paginated results (skip={skip}, limit={limit})")
            return results
        except Exception as e:
            logger.error(f"Error fetching paginated grading results: {str(e)}")
            raise