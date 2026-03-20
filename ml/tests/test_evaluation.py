"""Unit tests for model evaluation and comparison framework (CONV-26)."""

from __future__ import annotations

import numpy as np

from src.evaluation.comparison import ABTestAnalyzer, ComparisonResult, ModelComparator
from src.evaluation.metrics import (
    BinaryMetrics,
    MulticlassMetrics,
    evaluate_binary,
    evaluate_multiclass,
)

# ---------------------------------------------------------------------------
# Metrics tests
# ---------------------------------------------------------------------------

class TestEvaluateBinary:
    def test_perfect_predictions(self):
        y_true = np.array([0, 0, 0, 1, 1, 1])
        y_pred = np.array([0, 0, 0, 1, 1, 1])
        y_proba = np.array([0.1, 0.1, 0.2, 0.9, 0.8, 0.95])

        result = evaluate_binary(y_true, y_pred, y_proba)
        assert isinstance(result, BinaryMetrics)
        assert result.auc_roc == 1.0
        assert result.accuracy == 1.0
        assert result.f1 == 1.0

    def test_random_predictions(self):
        rng = np.random.default_rng(42)
        y_true = rng.integers(0, 2, size=200)
        y_proba = rng.random(200)
        y_pred = (y_proba > 0.5).astype(int)

        result = evaluate_binary(y_true, y_pred, y_proba)
        assert 0.3 <= result.auc_roc <= 0.7  # ~random
        assert isinstance(result.confusion_matrix, list)
        assert len(result.confusion_matrix) == 2

    def test_auc_pr_included(self):
        y_true = np.array([0, 0, 0, 0, 1])
        y_pred = np.array([0, 0, 0, 0, 1])
        y_proba = np.array([0.1, 0.1, 0.2, 0.1, 0.9])

        result = evaluate_binary(y_true, y_pred, y_proba)
        assert result.auc_pr > 0


class TestEvaluateMulticlass:
    def test_perfect_predictions(self):
        y_true = np.array([0, 1, 2, 3, 0, 1, 2, 3])
        y_pred = np.array([0, 1, 2, 3, 0, 1, 2, 3])
        names = ["browsing", "comparing", "deciding", "exiting"]

        result = evaluate_multiclass(y_true, y_pred, names)
        assert isinstance(result, MulticlassMetrics)
        assert result.accuracy == 1.0
        assert result.macro_f1 == 1.0

    def test_per_class_f1(self):
        y_true = np.array([0, 0, 1, 1, 2, 2, 3, 3])
        y_pred = np.array([0, 0, 1, 1, 2, 2, 3, 3])
        names = ["a", "b", "c", "d"]

        result = evaluate_multiclass(y_true, y_pred, names)
        assert set(result.per_class_f1.keys()) == set(names)
        for v in result.per_class_f1.values():
            assert v == 1.0

    def test_confusion_matrix_shape(self):
        y_true = np.array([0, 1, 2, 0, 1, 2])
        y_pred = np.array([0, 1, 2, 0, 1, 2])
        names = ["a", "b", "c"]

        result = evaluate_multiclass(y_true, y_pred, names)
        assert len(result.confusion_matrix) == 3
        assert len(result.confusion_matrix[0]) == 3


# ---------------------------------------------------------------------------
# Model comparison tests
# ---------------------------------------------------------------------------

class TestModelComparator:
    def test_compare_binary_returns_results(self):
        rng = np.random.default_rng(42)
        y_true = rng.integers(0, 2, size=200)

        # Model A: random, Model B: perfect
        pred_a = rng.integers(0, 2, size=200)
        proba_a = rng.random(200)
        pred_b = y_true.copy()
        proba_b = y_true.astype(float)

        comp = ModelComparator()
        results = comp.compare_binary(
            y_true, pred_a, pred_b, proba_a, proba_b,
            model_a_name="random", model_b_name="perfect",
        )
        assert len(results) == 3  # auc, accuracy, f1
        assert all(isinstance(r, ComparisonResult) for r in results)

    def test_perfect_vs_random_b_wins(self):
        rng = np.random.default_rng(42)
        n = 300
        y_true = rng.integers(0, 2, size=n)

        pred_a = rng.integers(0, 2, size=n)
        proba_a = rng.random(n)
        pred_b = y_true.copy()
        proba_b = y_true.astype(float)

        comp = ModelComparator()
        results = comp.compare_binary(
            y_true, pred_a, pred_b, proba_a, proba_b,
            model_a_name="random", model_b_name="perfect",
        )
        auc_result = next(r for r in results if r.metric_name == "auc_roc")
        assert auc_result.model_b_value > auc_result.model_a_value
        assert auc_result.delta > 0

    def test_compare_multiclass(self):
        rng = np.random.default_rng(42)
        y_true = rng.integers(0, 4, size=200)
        pred_a = rng.integers(0, 4, size=200)
        pred_b = y_true.copy()

        comp = ModelComparator()
        results = comp.compare_multiclass(
            y_true, pred_a, pred_b,
            class_names=["a", "b", "c", "d"],
        )
        assert len(results) == 2  # accuracy, macro_f1


# ---------------------------------------------------------------------------
# A/B test analyzer tests
# ---------------------------------------------------------------------------

class TestABTestAnalyzer:
    def test_significant_difference(self):
        """Large N, clear difference → significant."""
        ab = ABTestAnalyzer()
        result = ab.analyze(
            control_conversions=100, control_total=1000,
            treatment_conversions=150, treatment_total=1000,
        )
        assert result.significant is True
        assert result.result == "b_wins"
        assert result.lift > 0

    def test_insignificant_small_sample(self):
        """Small N, similar rates → not significant."""
        ab = ABTestAnalyzer()
        result = ab.analyze(
            control_conversions=5, control_total=50,
            treatment_conversions=6, treatment_total=50,
        )
        assert result.significant is False

    def test_control_wins(self):
        """Treatment worse than control → a_wins."""
        ab = ABTestAnalyzer()
        result = ab.analyze(
            control_conversions=200, control_total=1000,
            treatment_conversions=100, treatment_total=1000,
        )
        assert result.significant is True
        assert result.result == "a_wins"

    def test_required_sample_size(self):
        """Sample size for typical e-commerce rate should be reasonable."""
        ab = ABTestAnalyzer()
        n = ab.required_sample_size(baseline_rate=0.04, min_detectable_effect=0.02)
        assert 500 < n < 50000  # reasonable range for 4% → 6%

    def test_required_sample_size_edge_cases(self):
        ab = ABTestAnalyzer()
        assert ab.required_sample_size(0.0, 0.05) == 0
        assert ab.required_sample_size(0.5, 0.0) == 0
