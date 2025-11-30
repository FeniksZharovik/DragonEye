# routes/metrics_routes.py

from fastapi import APIRouter, HTTPException
from services.metrics_service import MetricsService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Metrics"])


@router.get("/metrics/classification")
def get_classification_metrics():
    """
    Get comprehensive classification metrics
    
    Returns:
    {
        "status": "success" | "warning" | "error",
        "message": "string",
        "metrics": {
            "accuracy": float,
            "precision_A": float,
            "precision_B": float,
            "precision_C": float,
            "recall_A": float,
            "recall_B": float,
            "recall_C": float,
            "f1_A": float,
            "f1_B": float,
            "f1_C": float,
            "macro_precision": float,
            "macro_recall": float,
            "macro_f1": float,
            "weighted_f1": float,
            "confusion_matrix": [[int, int, int], [int, int, int], [int, int, int]],
            "total_samples": int,
            "valid_samples": int
        },
        "timestamp": "ISO datetime"
    }
    """
    try:
        result = MetricsService.get_all_metrics()
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_classification_metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching metrics: {str(e)}")


@router.get("/metrics/summary")
def get_metrics_summary():
    """
    Get a simplified summary of metrics for dashboard cards
    """
    try:
        result = MetricsService.get_all_metrics()
        
        if result["status"] == "error" or not result.get("metrics"):
            raise HTTPException(status_code=500, detail=result["message"])
        
        metrics = result["metrics"]
        
        return {
            "status": "success",
            "summary": {
                "accuracy": metrics.get("accuracy", 0),
                "macro_f1": metrics.get("macro_f1", 0),
                "weighted_f1": metrics.get("weighted_f1", 0),
                "total_samples": metrics.get("total_samples", 0),
                "grade_distribution": {
                    "A": {
                        "precision": metrics.get("precision_A", 0),
                        "recall": metrics.get("recall_A", 0),
                        "f1": metrics.get("f1_A", 0)
                    },
                    "B": {
                        "precision": metrics.get("precision_B", 0),
                        "recall": metrics.get("recall_B", 0),
                        "f1": metrics.get("f1_B", 0)
                    },
                    "C": {
                        "precision": metrics.get("precision_C", 0),
                        "recall": metrics.get("recall_C", 0),
                        "f1": metrics.get("f1_C", 0)
                    }
                }
            },
            "timestamp": result.get("timestamp")
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_metrics_summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching metrics: {str(e)}")


@router.get("/metrics/confusion-matrix")
def get_confusion_matrix():
    """
    Get just the confusion matrix for visualization
    """
    try:
        result = MetricsService.get_all_metrics()
        
        if result["status"] == "error" or not result.get("metrics"):
            raise HTTPException(status_code=500, detail=result["message"])
        
        metrics = result["metrics"]
        
        return {
            "status": "success",
            "confusion_matrix": metrics.get("confusion_matrix", [[0, 0, 0], [0, 0, 0], [0, 0, 0]]),
            "labels": ["A", "B", "C"],
            "total_samples": metrics.get("total_samples", 0)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_confusion_matrix: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching confusion matrix: {str(e)}")
