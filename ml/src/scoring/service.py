"""Real-time scoring service — the primary ML entry point (CONV-25).

Loads all models once, then scores sessions through the full pipeline:
    raw features → 3 models → ensemble → SHAP → intervention engine → ScoringResult

Usage (backend integration):
    from ml.src.scoring.service import ScoringService

    service = ScoringService.get_instance()
    result = service.score_session({
        "hesitation_score": 0.4,
        "price_dwell_time_s": 12.0,
        ...
    })
"""

from __future__ import annotations

import pickle
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar

import numpy as np

from src.ensemble.ensemble import EnsembleConfig, EnsembleModel, EnsembleResult
from src.explainability.shap_explainer import (
    FeatureAttribution,
    UnifiedExplainer,
)
from src.intervention.engine import (
    InterventionEngine,
    InterventionRecommendation,
    PsychologicalStateMatch,
)

_DEFAULT_ARTIFACTS = Path(__file__).resolve().parent.parent.parent / "artifacts"
_DEFAULT_FRAMEWORK = (
    Path(__file__).resolve().parent.parent.parent / "psychology" / "framework_v1.json"
)


@dataclass
class ScoringResult:
    """Complete scoring output for one session."""

    # Ensemble
    session_score: float
    recommended_action: str
    confidence: float

    # Individual models
    conversion_prob: float
    intent_label: str
    intent_probs: dict[str, float]
    friction_prob: float

    # Explainability (empty when explain=False)
    top_shap_features: dict[str, list[FeatureAttribution]] = field(default_factory=dict)

    # Interventions
    interventions: list[InterventionRecommendation] = field(default_factory=list)
    psychological_states: list[PsychologicalStateMatch] = field(default_factory=list)

    # Timing
    latency_ms: float = 0.0


class ScoringService:
    """Singleton service that loads models once and scores sessions."""

    _instance: ClassVar[ScoringService | None] = None

    def __init__(
        self,
        artifacts_dir: Path | str | None = None,
        framework_path: Path | str | None = None,
        ensemble_config: EnsembleConfig | None = None,
    ) -> None:
        artifacts = Path(artifacts_dir) if artifacts_dir else _DEFAULT_ARTIFACTS
        fw_path = Path(framework_path) if framework_path else _DEFAULT_FRAMEWORK

        # Load models
        self._predictor = self._load(artifacts / "predictor_v1.pkl")
        self._intent_model = self._load(artifacts / "intent_v1.pkl")
        self._friction_model = self._load(artifacts / "friction_v1.pkl")

        # Load metadata
        self._predictor_meta = self._load(artifacts / "predictor_v1_meta.pkl")
        self._intent_meta = self._load(artifacts / "intent_v1_meta.pkl")
        self._friction_meta = self._load(artifacts / "friction_v1_meta.pkl")

        self._feature_cols: list[str] = self._predictor_meta["feature_cols"]
        self._intent_classes: list[str] = self._intent_meta["intent_classes"]
        self._label_encoder = self._intent_meta["label_encoder"]

        # Ensemble
        self._ensemble = EnsembleModel(ensemble_config)

        # SHAP explainer
        self._explainer = UnifiedExplainer.from_artifacts(artifacts)

        # Intervention engine
        self._intervention_engine = InterventionEngine(fw_path)

    @classmethod
    def get_instance(cls, **kwargs) -> ScoringService:
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = cls(**kwargs)
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton (useful for testing)."""
        cls._instance = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def score_session(
        self,
        features: dict[str, float | int],
        explain: bool = True,
        max_interventions: int = 3,
    ) -> ScoringResult:
        """Score a single session from its extracted features."""
        t0 = time.perf_counter()

        # 1. Build feature array in correct column order
        X = self._features_to_array(features)

        # 2. Run individual models
        conversion_prob = float(self._predictor.predict_proba(X)[:, 1][0])

        intent_encoded = int(self._intent_model.predict(X)[0])
        intent_label = self._label_encoder.inverse_transform([intent_encoded])[0]

        intent_proba = self._intent_model.predict_proba(X)[0]
        intent_probs = {
            cls: round(float(p), 4)
            for cls, p in zip(self._intent_classes, intent_proba, strict=True)
        }

        friction_prob = float(self._friction_model.predict_proba(X)[:, 1][0])

        # 3. Ensemble scoring
        ensemble_result: EnsembleResult = self._ensemble.score(
            conversion_prob=conversion_prob,
            intent_label=intent_label,
            intent_probs=intent_probs,
            friction_prob=friction_prob,
        )

        # 4. SHAP explanations (optional)
        top_shap: dict[str, list[FeatureAttribution]] = {}
        shap_attrs_for_intervention: list[FeatureAttribution] = []
        if explain:
            explanations = self._explainer.explain_all_local(X[0], top_k=3)
            for model_name, expl in explanations.items():
                top_shap[model_name] = expl.top_k
            # Use friction SHAP for intervention engine (most relevant for psychology)
            if "friction" in explanations:
                shap_attrs_for_intervention = explanations["friction"].attributions

        # 5. Intervention recommendations
        intervention_engine = self._intervention_engine
        psych_states = intervention_engine.match_states(
            features, shap_attrs_for_intervention or None
        )
        interventions = intervention_engine.recommend(
            features, shap_attrs_for_intervention or None, max_interventions
        )

        latency = (time.perf_counter() - t0) * 1000

        return ScoringResult(
            session_score=ensemble_result.session_score,
            recommended_action=ensemble_result.recommended_action,
            confidence=ensemble_result.confidence,
            conversion_prob=ensemble_result.conversion_prob,
            intent_label=ensemble_result.intent_label,
            intent_probs=ensemble_result.intent_probs,
            friction_prob=ensemble_result.friction_prob,
            top_shap_features=top_shap,
            interventions=interventions,
            psychological_states=psych_states,
            latency_ms=round(latency, 2),
        )

    def score_batch(
        self,
        features_list: list[dict[str, float | int]],
        explain: bool = False,
    ) -> list[ScoringResult]:
        """Score multiple sessions. explain=False by default for speed."""
        return [
            self.score_session(f, explain=explain)
            for f in features_list
        ]

    def health_check(self) -> dict:
        """Verify all models are loaded and functional."""
        sample = {col: 0.0 for col in self._feature_cols}
        try:
            result = self.score_session(sample, explain=False)
            return {
                "status": "healthy",
                "models_loaded": ["predictor_v1", "intent_v1", "friction_v1"],
                "feature_cols": self._feature_cols,
                "sample_score": result.session_score,
                "latency_ms": result.latency_ms,
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _features_to_array(self, features: dict[str, float | int]) -> np.ndarray:
        """Convert feature dict to ordered numpy array."""
        row = [float(features.get(col, 0.0)) for col in self._feature_cols]
        return np.array([row])

    @staticmethod
    def _load(path: Path):
        with open(path, "rb") as f:
            return pickle.load(f)  # noqa: S301
