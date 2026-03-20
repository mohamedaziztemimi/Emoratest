"""Psychology-aware intervention engine (CONV-24).

Maps session features (and optionally SHAP attributions) to psychological
states from the psychology framework, then recommends ranked interventions.

Two-layer logic:
    1. **Rule-based trigger matching** — each psychological state in the
       framework has trigger conditions (feature >= threshold). If the
       trigger_logic is "ALL", every condition must hold; if "ANY", at
       least one must hold.
    2. **SHAP-enhanced confidence** — when SHAP attributions are provided,
       the confidence for a matched state is boosted if the trigger features
       also have high absolute SHAP values (meaning the model *actually*
       relied on those features, not just that they crossed a threshold).

Priority score = severity_weight × confidence × expected_lift, used to rank
which interventions to surface first.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from src.explainability.shap_explainer import FeatureAttribution

_FRAMEWORK_PATH = (
    Path(__file__).resolve().parent.parent.parent / "psychology" / "framework_v1.json"
)


@dataclass
class PsychologicalStateMatch:
    """A psychological state that was detected in a session."""

    state_id: str
    state_label: str
    confidence: float
    trigger_features_matched: list[str]
    shap_evidence: list[FeatureAttribution]
    severity: float


@dataclass
class InterventionRecommendation:
    """A concrete intervention to show the user."""

    intervention_id: str
    intervention_type: str
    message: str
    placement: str
    expected_lift: float
    source_state: str
    priority_score: float


# ---------------------------------------------------------------------------
# Trigger evaluation operators
# ---------------------------------------------------------------------------

_OPERATORS: dict[str, callable] = {
    ">=": lambda v, t: v >= t,
    "<=": lambda v, t: v <= t,
    ">": lambda v, t: v > t,
    "<": lambda v, t: v < t,
    "==": lambda v, t: v == t,
}


class InterventionEngine:
    """Maps features + SHAP to psychology framework interventions."""

    def __init__(self, framework_path: Path | str | None = None) -> None:
        path = Path(framework_path) if framework_path else _FRAMEWORK_PATH
        with open(path) as f:
            data = json.load(f)
        self.states: list[dict] = data["states"]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def match_states(
        self,
        features: dict[str, float],
        shap_attributions: list[FeatureAttribution] | None = None,
    ) -> list[PsychologicalStateMatch]:
        """Evaluate which psychological states are triggered."""
        matches: list[PsychologicalStateMatch] = []

        for state in self.states:
            trigger_features = state["trigger_features"]
            trigger_logic = state.get("trigger_logic", "ALL")

            matched_features: list[str] = []
            total_triggers = len(trigger_features)

            for feat_name, condition in trigger_features.items():
                feat_val = features.get(feat_name, 0.0)
                op = condition["operator"]
                threshold = condition["threshold"]
                if self._evaluate_trigger(feat_val, op, threshold):
                    matched_features.append(feat_name)

            # Check trigger logic
            if trigger_logic == "ALL" and len(matched_features) < total_triggers:
                continue
            if trigger_logic == "ANY" and len(matched_features) == 0:
                continue

            # Compute confidence
            base_confidence = len(matched_features) / total_triggers
            shap_evidence = self._collect_shap_evidence(
                matched_features, shap_attributions
            )
            confidence = self._compute_shap_confidence(
                base_confidence, shap_evidence
            )

            severity = state["severity_weight"] * confidence

            matches.append(
                PsychologicalStateMatch(
                    state_id=state["id"],
                    state_label=state["label"],
                    confidence=round(confidence, 4),
                    trigger_features_matched=matched_features,
                    shap_evidence=shap_evidence,
                    severity=round(severity, 4),
                )
            )

        # Sort by severity descending
        matches.sort(key=lambda m: m.severity, reverse=True)
        return matches

    def recommend(
        self,
        features: dict[str, float],
        shap_attributions: list[FeatureAttribution] | None = None,
        max_interventions: int = 3,
    ) -> list[InterventionRecommendation]:
        """Return top-N interventions ranked by priority_score."""
        matched_states = self.match_states(features, shap_attributions)

        recommendations: list[InterventionRecommendation] = []
        for match in matched_states:
            # Find this state's interventions from framework
            state_def = next(s for s in self.states if s["id"] == match.state_id)
            for intervention in state_def["interventions"]:
                priority = match.severity * intervention["expected_lift"]
                recommendations.append(
                    InterventionRecommendation(
                        intervention_id=intervention["id"],
                        intervention_type=intervention["type"],
                        message=intervention["message"],
                        placement=intervention["placement"],
                        expected_lift=intervention["expected_lift"],
                        source_state=match.state_id,
                        priority_score=round(priority, 6),
                    )
                )

        # Sort by priority_score descending, take top-N
        recommendations.sort(key=lambda r: r.priority_score, reverse=True)
        return recommendations[:max_interventions]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _evaluate_trigger(value: float, operator: str, threshold: float) -> bool:
        """Check if a single trigger condition is met."""
        op_fn = _OPERATORS.get(operator)
        if op_fn is None:
            return False
        return op_fn(value, threshold)

    @staticmethod
    def _collect_shap_evidence(
        matched_features: list[str],
        shap_attributions: list[FeatureAttribution] | None,
    ) -> list[FeatureAttribution]:
        """Filter SHAP attributions to only those matching trigger features."""
        if not shap_attributions:
            return []
        return [a for a in shap_attributions if a.feature_name in matched_features]

    @staticmethod
    def _compute_shap_confidence(
        base_confidence: float,
        shap_evidence: list[FeatureAttribution],
    ) -> float:
        """Boost confidence when SHAP agrees with trigger matches.

        If the trigger features also have high absolute SHAP values,
        the model actually relied on them — this is stronger evidence
        than just crossing a threshold.
        """
        if not shap_evidence:
            return base_confidence

        # Mean absolute SHAP of the matched trigger features
        mean_shap = sum(abs(a.shap_value) for a in shap_evidence) / len(shap_evidence)

        # Boost: up to +0.2 for high SHAP agreement (sigmoid-style capping)
        boost = min(mean_shap / (mean_shap + 0.5), 0.2)

        return min(base_confidence + boost, 1.0)
