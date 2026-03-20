"""Model comparison and A/B test analysis (CONV-26).

Provides:
    - ModelComparator: statistically compare two model versions on the same test set
    - ABTestAnalyzer: analyze conversion-rate A/B tests for interventions

Statistical tests used:
    - McNemar's test for paired classifier comparison
    - Two-proportion z-test for A/B conversion rate comparison
    - Normal approximation for sample size calculation
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy import stats


@dataclass
class ComparisonResult:
    """Result of comparing two models on the same metric."""

    model_a_name: str
    model_b_name: str
    metric_name: str
    model_a_value: float
    model_b_value: float
    delta: float
    delta_pct: float
    statistically_significant: bool
    p_value: float
    recommendation: str  # "a_wins" | "b_wins" | "no_diff" | "inconclusive"


@dataclass
class ABTestResult:
    """Result of an A/B test analysis."""

    control_rate: float
    treatment_rate: float
    lift: float
    p_value: float
    significant: bool
    result: str  # matches Experiment.result enum
    sample_size_adequate: bool
    min_detectable_effect: float


class ModelComparator:
    """Compare two model versions on the same test set."""

    def compare_binary(
        self,
        y_true: np.ndarray,
        pred_a: np.ndarray,
        pred_b: np.ndarray,
        proba_a: np.ndarray,
        proba_b: np.ndarray,
        model_a_name: str = "model_a",
        model_b_name: str = "model_b",
        significance_level: float = 0.05,
    ) -> list[ComparisonResult]:
        """Compare two binary classifiers using McNemar's test + AUC comparison."""
        from sklearn.metrics import accuracy_score, f1_score, roc_auc_score

        results = []

        # AUC comparison
        auc_a = roc_auc_score(y_true, proba_a)
        auc_b = roc_auc_score(y_true, proba_b)
        results.append(self._make_comparison(
            model_a_name, model_b_name, "auc_roc",
            auc_a, auc_b, significance_level,
            p_value=self._mcnemar_p(y_true, pred_a, pred_b),
        ))

        # Accuracy
        acc_a = accuracy_score(y_true, pred_a)
        acc_b = accuracy_score(y_true, pred_b)
        p_val = self._mcnemar_p(y_true, pred_a, pred_b)
        results.append(self._make_comparison(
            model_a_name, model_b_name, "accuracy",
            acc_a, acc_b, significance_level, p_value=p_val,
        ))

        # F1
        f1_a = f1_score(y_true, pred_a, zero_division=0)
        f1_b = f1_score(y_true, pred_b, zero_division=0)
        results.append(self._make_comparison(
            model_a_name, model_b_name, "f1",
            f1_a, f1_b, significance_level, p_value=p_val,
        ))

        return results

    def compare_multiclass(
        self,
        y_true: np.ndarray,
        pred_a: np.ndarray,
        pred_b: np.ndarray,
        class_names: list[str],
        model_a_name: str = "model_a",
        model_b_name: str = "model_b",
        significance_level: float = 0.05,
    ) -> list[ComparisonResult]:
        """Compare two multi-class classifiers using McNemar's test."""
        from sklearn.metrics import accuracy_score, f1_score

        p_val = self._mcnemar_p(y_true, pred_a, pred_b)

        results = []
        acc_a = accuracy_score(y_true, pred_a)
        acc_b = accuracy_score(y_true, pred_b)
        results.append(self._make_comparison(
            model_a_name, model_b_name, "accuracy",
            acc_a, acc_b, significance_level, p_value=p_val,
        ))

        f1_a = f1_score(y_true, pred_a, average="macro", zero_division=0)
        f1_b = f1_score(y_true, pred_b, average="macro", zero_division=0)
        results.append(self._make_comparison(
            model_a_name, model_b_name, "macro_f1",
            f1_a, f1_b, significance_level, p_value=p_val,
        ))

        return results

    # ------------------------------------------------------------------

    @staticmethod
    def _mcnemar_p(
        y_true: np.ndarray,
        pred_a: np.ndarray,
        pred_b: np.ndarray,
    ) -> float:
        """McNemar's test: are the two classifiers' errors significantly different?"""
        correct_a = (pred_a == y_true)
        correct_b = (pred_b == y_true)

        # b = A correct, B wrong; c = A wrong, B correct
        b = int(np.sum(correct_a & ~correct_b))
        c = int(np.sum(~correct_a & correct_b))

        if b + c == 0:
            return 1.0  # no disagreement

        # McNemar's chi-squared with continuity correction
        chi2 = (abs(b - c) - 1) ** 2 / (b + c)
        return float(stats.chi2.sf(chi2, df=1))

    @staticmethod
    def _make_comparison(
        a_name: str, b_name: str, metric: str,
        val_a: float, val_b: float,
        sig_level: float, p_value: float,
    ) -> ComparisonResult:
        delta = val_b - val_a
        delta_pct = (delta / val_a * 100) if val_a != 0 else 0.0
        significant = p_value < sig_level

        if not significant:
            rec = "no_diff"
        elif delta > 0:
            rec = "b_wins"
        elif delta < 0:
            rec = "a_wins"
        else:
            rec = "inconclusive"

        return ComparisonResult(
            model_a_name=a_name,
            model_b_name=b_name,
            metric_name=metric,
            model_a_value=round(val_a, 4),
            model_b_value=round(val_b, 4),
            delta=round(delta, 4),
            delta_pct=round(delta_pct, 2),
            statistically_significant=significant,
            p_value=round(p_value, 6),
            recommendation=rec,
        )


class ABTestAnalyzer:
    """Analyze A/B test results for intervention experiments."""

    def analyze(
        self,
        control_conversions: int,
        control_total: int,
        treatment_conversions: int,
        treatment_total: int,
        significance_level: float = 0.05,
    ) -> ABTestResult:
        """Two-proportion z-test for conversion rate comparison."""
        cr = control_conversions / max(control_total, 1)
        tr = treatment_conversions / max(treatment_total, 1)
        lift = (tr - cr) / cr if cr > 0 else 0.0

        # Pooled proportion
        p_pool = (control_conversions + treatment_conversions) / max(
            control_total + treatment_total, 1
        )
        inv_n = 1 / max(control_total, 1) + 1 / max(treatment_total, 1)
        se = math.sqrt(max(p_pool * (1 - p_pool) * inv_n, 1e-12))
        z = (tr - cr) / se
        p_value = 2 * (1 - stats.norm.cdf(abs(z)))  # two-tailed

        significant = bool(p_value < significance_level)
        min_n = self.required_sample_size(cr, 0.05) if cr > 0 else 0
        adequate = min(control_total, treatment_total) >= min_n

        if not significant:
            result = "no_diff" if adequate else "inconclusive"
        elif tr > cr:
            result = "b_wins"  # treatment wins
        else:
            result = "a_wins"  # control wins

        return ABTestResult(
            control_rate=round(cr, 4),
            treatment_rate=round(tr, 4),
            lift=round(lift, 4),
            p_value=round(p_value, 6),
            significant=significant,
            result=result,
            sample_size_adequate=adequate,
            min_detectable_effect=0.05,
        )

    @staticmethod
    def required_sample_size(
        baseline_rate: float,
        min_detectable_effect: float,
        power: float = 0.8,
        significance: float = 0.05,
    ) -> int:
        """Minimum sample size per variant for a valid A/B test.

        Uses the normal approximation formula:
            n = (Z_α/2 + Z_β)² × [p₁(1-p₁) + p₂(1-p₂)] / (p₂ - p₁)²
        """
        p1 = baseline_rate
        p2 = baseline_rate + min_detectable_effect

        if p2 <= p1 or p1 <= 0 or p2 >= 1:
            return 0

        z_alpha = stats.norm.ppf(1 - significance / 2)
        z_beta = stats.norm.ppf(power)

        numerator = (z_alpha + z_beta) ** 2 * (p1 * (1 - p1) + p2 * (1 - p2))
        denominator = (p2 - p1) ** 2

        return int(math.ceil(numerator / denominator))
