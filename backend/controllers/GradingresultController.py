# backend/controllers/GradingresultController.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from core.database import get_db
from services.GradingresultService import GradingresultService
from models.schemas import GradingResultResponse, GradingResultCreate

router = APIRouter(tags=["Grading Results"])


def serialize_result(result) -> dict:
    """Convert SQLAlchemy model instance to dictionary, handling UUID serialization"""
    data = {
        "id": str(result.id) if hasattr(result.id, '__str__') else result.id,
        "length_cm": result.length_cm,
        "diameter_cm": result.diameter_cm,
        "weight_est_g": result.weight_est_g,
        "weight_actual_g": result.weight_actual_g,
        "ratio": result.ratio,
        "fuzzy_score": result.fuzzy_score,
        "final_grade": result.final_grade,
        "tanggal": result.tanggal.isoformat() if result.tanggal else None,
    }
    return data


# ✅ IMPORTANT: More specific routes MUST come before generic /{id} route!

@router.get("/all", response_model=dict)
def get_all_grading_results(
    db: Session = Depends(get_db)
):
    """
    Fetch ALL grading results from the database (no pagination).
    """
    try:
        service = GradingresultService(db)
        results = service.get_all()
        
        return {
            "data": [serialize_result(r) for r in results],
            "total": len(results),
            "message": "All grading results fetched successfully" if results else "No grading results found"
        }
    except Exception as e:
        import traceback
        print(f"ERROR: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching grading results: {str(e)}"
        )


@router.get("/list/all", response_model=dict)
def list_all_grading_results(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Fetch all grading results with pagination support.
    
    Query Parameters:
    - skip: Number of records to skip (default: 0)
    - limit: Maximum number of records to return (default: 10, max: 100)
    """
    try:
        service = GradingresultService(db)
        results = service.get_paginated(skip=skip, limit=limit)
        
        return {
            "data": [serialize_result(r) for r in results],
            "total": len(results),
            "skip": skip,
            "limit": limit,
            "message": "Grading results fetched successfully" if results else "No grading results found"
        }
    except Exception as e:
        import traceback
        print(f"ERROR: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching grading results: {str(e)}"
        )


@router.get("/{result_id}", response_model=dict)
def get_grading_result_by_id(
    result_id: str,
    db: Session = Depends(get_db)
):
    """
    Fetch a specific grading result by ID.
    
    Parameters:
    - result_id: UUID of the grading result
    """
    try:
        service = GradingresultService(db)
        result = service.get_by_id(result_id)
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Grading result with ID {result_id} not found"
            )
        
        return serialize_result(result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching grading result: {str(e)}"
        )


@router.post("/", response_model=dict)
def create_grading_result(
    grading_data: GradingResultCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new grading result record.
    """
    try:
        service = GradingresultService(db)
        result = service.create(grading_data)
        return serialize_result(result)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating grading result: {str(e)}"
        )


@router.put("/{result_id}", response_model=dict)
def update_grading_result(
    result_id: str,
    grading_data: GradingResultCreate,
    db: Session = Depends(get_db)
):
    """
    Update an existing grading result.
    
    Parameters:
    - result_id: UUID of the grading result to update
    """
    try:
        service = GradingresultService(db)
        result = service.update(result_id, grading_data)
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Grading result with ID {result_id} not found"
            )
        
        return serialize_result(result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating grading result: {str(e)}"
        )


@router.delete("/{result_id}")
def delete_grading_result(
    result_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a grading result by ID.
    
    Parameters:
    - result_id: UUID of the grading result to delete
    """
    try:
        service = GradingresultService(db)
        deleted = service.delete(result_id)
        
        if not deleted:
            raise HTTPException(
                status_code=404,
                detail=f"Grading result with ID {result_id} not found"
            )
        
        return {"message": f"Grading result {result_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting grading result: {str(e)}"
        )