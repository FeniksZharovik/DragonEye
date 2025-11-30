"""
Metrics Service for Classification Evaluation
Computes accuracy, precision, recall, F1-score, and confusion matrix
"""

import requests
import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class MetricsService:
    """Service to compute classification metrics from grading results"""
    
    VALID_GRADES = ["A", "B", "C"]
    API_ENDPOINT = "http://127.0.0.1:8000/api/gradingresult/all"
    
    @staticmethod
    def fetch_grading_results() -> List[Dict[str, Any]]:
        """
        Fetch all grading results from the API
        
        Returns:
            List of grading result dictionaries
            
        Raises:
            Exception: If API call fails
        """
        try:
            response = requests.get(MetricsService.API_ENDPOINT, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = data.get("data", [])
            
            logger.info(f"Fetched {len(results)} grading results from API")
            return results
        except Exception as e:
            logger.error(f"Error fetching grading results: {str(e)}")
            raise
    
    @staticmethod
    def validate_grades(y_true: List[str], y_pred: List[str]) -> tuple:
        """
        Validate and filter grades, keeping only valid ones (A, B, C)
        
        Args:
            y_true: List of true labels (grade_by_weight)
            y_pred: List of predicted labels (final_grade)
            
        Returns:
            Tuple of (filtered_y_true, filtered_y_pred)
        """
        valid_indices = []
        
        for i, (true_grade, pred_grade) in enumerate(zip(y_true, y_pred)):
            if true_grade in MetricsService.VALID_GRADES and pred_grade in MetricsService.VALID_GRADES:
                valid_indices.append(i)
        
        y_true_filtered = [y_true[i] for i in valid_indices]
        y_pred_filtered = [y_pred[i] for i in valid_indices]
        
        logger.info(f"Validated grades: {len(y_true_filtered)} out of {len(y_true)} records")
        
        return y_true_filtered, y_pred_filtered
    
    @staticmethod
    def compute_metrics(y_true: List[str], y_pred: List[str]) -> Dict[str, Any]:
        """
        Compute comprehensive classification metrics
        
        Args:
            y_true: List of true labels
            y_pred: List of predicted labels
            
        Returns:
            Dictionary containing all metrics
        """
        if not y_true or not y_pred:
            logger.warning("No valid grades to compute metrics")
            return {
                "accuracy": 0,
                "precision_A": 0, "precision_B": 0, "precision_C": 0,
                "recall_A": 0, "recall_B": 0, "recall_C": 0,
                "f1_A": 0, "f1_B": 0, "f1_C": 0,
                "macro_precision": 0, "macro_recall": 0, "macro_f1": 0,
                "weighted_f1": 0,
                "confusion_matrix": [[0, 0, 0], [0, 0, 0], [0, 0, 0]],
                "total_samples": 0,
                "valid_samples": 0
            }
        
        # Overall metrics
        accuracy = accuracy_score(y_true, y_pred)
        macro_precision = precision_score(y_true, y_pred, average='macro', zero_division=0)
        macro_recall = recall_score(y_true, y_pred, average='macro', zero_division=0)
        macro_f1 = f1_score(y_true, y_pred, average='macro', zero_division=0)
        weighted_f1 = f1_score(y_true, y_pred, average='weighted', zero_division=0)
        
        # Per-class metrics
        metrics = {
            "accuracy": round(float(accuracy), 4),
            "macro_precision": round(float(macro_precision), 4),
            "macro_recall": round(float(macro_recall), 4),
            "macro_f1": round(float(macro_f1), 4),
            "weighted_f1": round(float(weighted_f1), 4),
            "total_samples": len(y_true),
            "valid_samples": len(y_true),
        }
        
        # Per-class metrics (A, B, C)
        for grade in MetricsService.VALID_GRADES:
            try:
                precision = precision_score(y_true, y_pred, labels=[grade], average=None, zero_division=0)[0]
                recall = recall_score(y_true, y_pred, labels=[grade], average=None, zero_division=0)[0]
                f1 = f1_score(y_true, y_pred, labels=[grade], average=None, zero_division=0)[0]
                
                metrics[f"precision_{grade}"] = round(float(precision), 4)
                metrics[f"recall_{grade}"] = round(float(recall), 4)
                metrics[f"f1_{grade}"] = round(float(f1), 4)
            except Exception as e:
                logger.warning(f"Error computing metrics for grade {grade}: {str(e)}")
                metrics[f"precision_{grade}"] = 0
                metrics[f"recall_{grade}"] = 0
                metrics[f"f1_{grade}"] = 0
        
        # Confusion matrix
        cm = confusion_matrix(y_true, y_pred, labels=MetricsService.VALID_GRADES)
        cm_list = cm.tolist()
        
        metrics["confusion_matrix"] = cm_list
        
        logger.info(f"Computed metrics - Accuracy: {accuracy:.4f}, Macro F1: {macro_f1:.4f}")
        
        return metrics
    
    @staticmethod
    def get_all_metrics() -> Dict[str, Any]:
        """
        Main method: Fetch data, validate, and compute metrics
        
        Returns:
            Dictionary with all metrics and metadata
        """
        try:
            # Fetch data
            results = MetricsService.fetch_grading_results()
            
            if not results:
                return {
                    "status": "warning",
                    "message": "No grading results found",
                    "metrics": None
                }
            
            # Extract grades
            y_true = [r.get("grade_by_weight") for r in results]
            y_pred = [r.get("final_grade") for r in results]
            
            # Validate
            y_true_valid, y_pred_valid = MetricsService.validate_grades(y_true, y_pred)
            
            if not y_true_valid:
                return {
                    "status": "warning",
                    "message": "No valid grades after filtering",
                    "metrics": None
                }
            
            # Compute metrics
            metrics = MetricsService.compute_metrics(y_true_valid, y_pred_valid)
            
            return {
                "status": "success",
                "message": f"Metrics computed successfully for {len(y_true_valid)} samples",
                "metrics": metrics,
                "timestamp": pd.Timestamp.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error in get_all_metrics: {str(e)}")
            return {
                "status": "error",
                "message": f"Error computing metrics: {str(e)}",
                "metrics": None
            }
