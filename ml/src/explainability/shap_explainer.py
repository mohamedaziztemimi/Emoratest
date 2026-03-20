"""Unified SHAP explainability across all models (CONV-23).

Provides both local (per-session) and global (dataset-level) explanations
for the conversion predictor, intent classifier, and friction detector.

Local explanations answer: "Why did the model predict *this* for *this* session?"
Global explanations answer: "Which features matter most *across all sessions*?"
"""

from __future__ import annotations

import pickle
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import shap

from src.data.loader import FEATURE_COLS


@dataclass
class FeatureAttribution:
    """One feature's contribution to a single prediction."""

    feature_name: str
    shap_value: float
    feature_value: float
    direction: str  # "increases_risk" | "decreases_risk"


@dataclass
class LocalExplanation:
    """Per-session SHAP explanation for one model."""

    model_name: str
    base_value: float
    attributions: list[FeatureAttribution]
    top_k: list[FeatureAttribution]


@dataclass
class GlobalExplanation:
    """Dataset-level feature importance for one model."""

    model_name: str
    feature_importance: dict[str, float]
    feature_ranking: list[str]


# Direction logic per model:
#   - conversion: positive SHAP → higher conversion prob → DECREASES risk
#   - friction:   positive SHAP → higher friction prob  → INCREASES risk
#   - intent:     positive SHAP for "exiting" class     → INCREASES risk
_RISK_DIRECTION: dict[str, str] = {
    "conversion": "inverted",  # positive SHAP = good
    "friction": "direct",      # positive SHAP = bad
    "intent": "direct",        # positive SHAP for predicted class (neutral)
}


class UnifiedExplainer:
    """Wraps SHAP TreeExplainers for all three models."""

    def __init__(
        self,
        predictor_explainer: shap.TreeExplainer,
        intent_explainer: shap.TreeExplainer,
        friction_explainer: shap.TreeExplainer,
        feature_cols: list[str] | None = None,
        intent_classes: list[str] | None = None,
    ) -> None:
        self._explainers = {
            "conversion": predictor_explainer,
            "intent": intent_explainer,
            "friction": friction_explainer,
        }
        self._feature_cols = feature_cols or list(FEATURE_COLS)
        self._intent_classes = intent_classes or [
            "browsing", "comparing", "deciding", "exiting",
        ]

    @classmethod
    def from_artifacts(cls, artifacts_dir: Path) -> UnifiedExplainer:
        """Load all three SHAP explainers from ml/artifacts/."""
        artifacts_dir = Path(artifacts_dir)

        def _load(name: str):
            with open(artifacts_dir / name, "rb") as f:
                return pickle.load(f)  # noqa: S301

        predictor_shap = _load("predictor_v1_shap.pkl")
        intent_shap = _load("intent_v1_shap.pkl")
        friction_shap = _load("friction_v1_shap.pkl")

        # Load intent metadata for class names
        intent_meta = _load("intent_v1_meta.pkl")
        intent_classes = intent_meta.get("intent_classes", None)

        # Feature columns from any meta
        predictor_meta = _load("predictor_v1_meta.pkl")
        feature_cols = predictor_meta.get("feature_cols", None)

        return cls(
            predictor_explainer=predictor_shap,
            intent_explainer=intent_shap,
            friction_explainer=friction_shap,
            feature_cols=feature_cols,
            intent_classes=intent_classes,
        )

    # ------------------------------------------------------------------
    # Local explanations (per-session)
    # ------------------------------------------------------------------

    def explain_local(
        self,
        features: np.ndarray,
        model_name: str,
        top_k: int = 3,
        target_class: int | None = None,
    ) -> LocalExplanation:
        """Per-session SHAP explanation for a single model.

        Args:
            features: 1-D or 2-D array with shape (n_features,) or (1, n_features).
            model_name: "conversion", "intent", or "friction".
            top_k: Number of top features to highlight.
            target_class: For intent (multi-class), which class to explain.
                          Defaults to the class with highest mean |SHAP|.
        """
        if model_name not in self._explainers:
            raise ValueError(f"Unknown model: {model_name}. Use: {list(self._explainers)}")

        explainer = self._explainers[model_name]
        x = np.asarray(features)
        if x.ndim == 1:
            x = x.reshape(1, -1)

        shap_values = explainer.shap_values(x)
        expected = explainer.expected_value
        is_multi = not np.isscalar(expected) and np.asarray(expected).ndim > 0

        base_value = (
            float(np.asarray(expected)[target_class or 0]) if is_multi else float(expected)
        )

        # Multi-class SHAP values come in two possible formats:
        #   - list of arrays: [array(n, feats), ...] one per class (older SHAP)
        #   - 3-D array: shape (n_samples, n_features, n_classes)  (newer SHAP)
        sv_arr = np.asarray(shap_values)

        if isinstance(shap_values, list) and sv_arr.ndim == 3 and sv_arr.shape[0] > 1:
            # list format: (n_classes, n_samples, n_features)
            if target_class is not None:
                sv = sv_arr[target_class][0]
            else:
                mean_abs = [np.abs(sv_arr[c][0]).mean() for c in range(sv_arr.shape[0])]
                best_class = int(np.argmax(mean_abs))
                sv = sv_arr[best_class][0]
                base_value = float(np.asarray(expected)[best_class])
        elif sv_arr.ndim == 3 and sv_arr.shape[-1] > 1:
            # 3-D array format: (n_samples, n_features, n_classes)
            row = sv_arr[0]  # (n_features, n_classes)
            if target_class is not None:
                sv = row[:, target_class]
            else:
                mean_abs = np.abs(row).mean(axis=0)
                best_class = int(np.argmax(mean_abs))
                sv = row[:, best_class]
                if is_multi:
                    base_value = float(np.asarray(expected)[best_class])
        else:
            # Binary model: shape (n_samples, n_features)
            sv = sv_arr[0]

        risk_mode = _RISK_DIRECTION.get(model_name, "direct")
        attributions = self._build_attributions(sv, x[0], risk_mode)

        # Sort by |SHAP| descending for top_k
        sorted_attrs = sorted(attributions, key=lambda a: abs(a.shap_value), reverse=True)

        return LocalExplanation(
            model_name=model_name,
            base_value=base_value,
            attributions=attributions,
            top_k=sorted_attrs[:top_k],
        )

    def explain_all_local(
        self,
        features: np.ndarray,
        top_k: int = 3,
    ) -> dict[str, LocalExplanation]:
        """Per-session SHAP for all three models."""
        return {
            name: self.explain_local(features, name, top_k=top_k)
            for name in self._explainers
        }

    # ------------------------------------------------------------------
    # Global explanations (dataset-level)
    # ------------------------------------------------------------------

    def explain_global(
        self,
        X: np.ndarray,
        model_name: str,
    ) -> GlobalExplanation:
        """Global feature importance = mean |SHAP| across a dataset."""
        if model_name not in self._explainers:
            raise ValueError(f"Unknown model: {model_name}. Use: {list(self._explainers)}")

        explainer = self._explainers[model_name]
        shap_values = explainer.shap_values(X)

        # Handle multi-class formats (list or 3-D array)
        sv_arr = np.asarray(shap_values)
        if isinstance(shap_values, list) and sv_arr.ndim == 3 and sv_arr.shape[0] > 1:
            # list format: (n_classes, n_samples, n_features)
            mean_abs = np.mean([np.abs(sv) for sv in shap_values], axis=0).mean(axis=0)
        elif sv_arr.ndim == 3 and sv_arr.shape[-1] > 1:
            # 3-D array: (n_samples, n_features, n_classes) → avg across classes then samples
            mean_abs = np.abs(sv_arr).mean(axis=-1).mean(axis=0)
        else:
            mean_abs = np.abs(sv_arr).mean(axis=0)

        importance = {}
        for i, col in enumerate(self._feature_cols):
            importance[col] = round(float(mean_abs[i]), 6)

        ranking = sorted(importance, key=lambda k: importance[k], reverse=True)

        return GlobalExplanation(
            model_name=model_name,
            feature_importance=importance,
            feature_ranking=ranking,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _build_attributions(
        self,
        shap_values_row: np.ndarray,
        feature_values_row: np.ndarray,
        risk_mode: str,
    ) -> list[FeatureAttribution]:
        """Build FeatureAttribution list from raw SHAP values."""
        attributions = []
        for i, col in enumerate(self._feature_cols):
            sv = float(shap_values_row[i])
            fv = float(feature_values_row[i])

            if risk_mode == "inverted":
                direction = "decreases_risk" if sv > 0 else "increases_risk"
            else:
                direction = "increases_risk" if sv > 0 else "decreases_risk"

            attributions.append(
                FeatureAttribution(
                    feature_name=col,
                    shap_value=round(sv, 6),
                    feature_value=round(fv, 4),
                    direction=direction,
                )
            )
        return attributions
