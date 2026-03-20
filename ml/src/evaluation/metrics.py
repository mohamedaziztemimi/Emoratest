"""Model evaluation metrics (CONV-26).

Standardized evaluation for binary and multi-class classifiers,
producing structured metric objects that can be logged, compared,
and stored alongside model artifacts.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


@dataclass
class BinaryMetrics:
    """Evaluation metrics for a binary classifier."""

    auc_roc: float
    auc_pr: float
    accuracy: float
    precision: float
    recall: float
    f1: float
    classification_report: str
    confusion_matrix: list[list[int]]


@dataclass
class MulticlassMetrics:
    """Evaluation metrics for a multi-class classifier."""

    accuracy: float
    macro_f1: float
    weighted_f1: float
    per_class_f1: dict[str, float]
    classification_report: str
    confusion_matrix: list[list[int]]


def evaluate_binary(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_pred_proba: np.ndarray,
    target_names: list[str] | None = None,
) -> BinaryMetrics:
    """Evaluate a binary classifier.

    Args:
        y_true: Ground-truth labels (0/1).
        y_pred: Predicted labels (0/1).
        y_pred_proba: Predicted probabilities for the positive class.
        target_names: Optional class names for the report.
    """
    return BinaryMetrics(
        auc_roc=float(roc_auc_score(y_true, y_pred_proba)),
        auc_pr=float(average_precision_score(y_true, y_pred_proba)),
        accuracy=float(accuracy_score(y_true, y_pred)),
        precision=float(precision_score(y_true, y_pred, zero_division=0)),
        recall=float(recall_score(y_true, y_pred, zero_division=0)),
        f1=float(f1_score(y_true, y_pred, zero_division=0)),
        classification_report=classification_report(
            y_true, y_pred, target_names=target_names, zero_division=0,
        ),
        confusion_matrix=confusion_matrix(y_true, y_pred).tolist(),
    )


def evaluate_multiclass(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    class_names: list[str],
) -> MulticlassMetrics:
    """Evaluate a multi-class classifier.

    Args:
        y_true: Ground-truth labels (encoded ints).
        y_pred: Predicted labels (encoded ints).
        class_names: Ordered list of class names.
    """
    per_class = f1_score(y_true, y_pred, average=None, zero_division=0)
    per_class_dict = {
        name: round(float(score), 4)
        for name, score in zip(class_names, per_class, strict=True)
    }

    return MulticlassMetrics(
        accuracy=float(accuracy_score(y_true, y_pred)),
        macro_f1=float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        weighted_f1=float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
        per_class_f1=per_class_dict,
        classification_report=classification_report(
            y_true, y_pred, target_names=class_names, zero_division=0,
        ),
        confusion_matrix=confusion_matrix(y_true, y_pred).tolist(),
    )
