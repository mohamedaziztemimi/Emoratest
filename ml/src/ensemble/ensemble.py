"""Ensemble model combining conversion, intent, and friction predictions (CONV-22).

Produces a unified session score and action recommendation by weighting
the three individual model outputs. The ensemble is a transparent weighted
combination — no meta-model — so every score can be traced back to its
component signals.

Action ladder:
    session_score < 0.30  → "monitor"   (low risk, no action)
    0.30 ≤ score < 0.50   → "nudge"     (soft engagement)
    0.50 ≤ score < 0.75   → "intervene" (active intervention)
    score ≥ 0.75          → "urgent"    (last-chance retention)
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Default mapping: how much abandonment risk each intent class carries.
_DEFAULT_INTENT_RISK: dict[str, float] = {
    "browsing": 0.3,
    "comparing": 0.4,
    "deciding": 0.6,
    "exiting": 0.9,
}

ACTION_THRESHOLDS: list[tuple[float, str]] = [
    (0.75, "urgent"),
    (0.50, "intervene"),
    (0.30, "nudge"),
    (0.00, "monitor"),
]


@dataclass
class EnsembleConfig:
    """Weights and thresholds for combining model outputs."""

    conversion_weight: float = 0.5
    friction_weight: float = 0.3
    intent_weight: float = 0.2
    intent_risk_map: dict[str, float] = field(default_factory=lambda: dict(_DEFAULT_INTENT_RISK))


@dataclass
class EnsembleResult:
    """Unified prediction output from the ensemble."""

    session_score: float
    conversion_prob: float
    intent_label: str
    intent_probs: dict[str, float]
    friction_prob: float
    recommended_action: str
    confidence: float


class EnsembleModel:
    """Weighted combination of conversion, intent, and friction model outputs."""

    def __init__(self, config: EnsembleConfig | None = None) -> None:
        self.config = config or EnsembleConfig()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def score(
        self,
        conversion_prob: float,
        intent_label: str,
        intent_probs: dict[str, float],
        friction_prob: float,
    ) -> EnsembleResult:
        """Combine three model outputs into a single session score."""
        intent_risk = self.config.intent_risk_map.get(intent_label, 0.5)

        session_score = self._compute_session_score(
            conversion_prob, intent_risk, friction_prob
        )
        confidence = self._compute_confidence(
            conversion_prob, intent_probs, friction_prob
        )
        action = self._recommend_action(session_score)

        return EnsembleResult(
            session_score=round(session_score, 4),
            conversion_prob=round(conversion_prob, 4),
            intent_label=intent_label,
            intent_probs=intent_probs,
            friction_prob=round(friction_prob, 4),
            recommended_action=action,
            confidence=round(confidence, 4),
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _compute_session_score(
        self,
        conversion_prob: float,
        intent_risk: float,
        friction_prob: float,
    ) -> float:
        """Weighted combination.

        Higher conversion probability *decreases* risk, so we invert it.
        """
        abandonment_risk = 1.0 - conversion_prob
        cfg = self.config
        raw = (
            cfg.conversion_weight * abandonment_risk
            + cfg.friction_weight * friction_prob
            + cfg.intent_weight * intent_risk
        )
        return max(0.0, min(1.0, raw))

    def _compute_confidence(
        self,
        conversion_prob: float,
        intent_probs: dict[str, float],
        friction_prob: float,
    ) -> float:
        """Confidence is high when all three models agree on risk direction.

        Each model's "certainty" is measured by how far its primary signal
        is from the decision boundary (0.5). Agreement boosts confidence.
        """
        # Convert each to a risk certainty in [0, 1]
        conv_certainty = abs(conversion_prob - 0.5) * 2  # 0 at 0.5, 1 at 0/1
        friction_certainty = abs(friction_prob - 0.5) * 2

        # Intent certainty: how peaked the probability distribution is
        if intent_probs:
            max_prob = max(intent_probs.values())
            intent_certainty = max_prob  # 0.25 = uniform, 1.0 = certain
        else:
            intent_certainty = 0.5

        # Agreement bonus: are they pointing the same direction?
        # High risk = low conversion + high friction + risky intent
        risk_signals = [
            1.0 - conversion_prob,  # > 0.5 means risky
            friction_prob,          # > 0.5 means risky
        ]
        agreement = 1.0 - abs(risk_signals[0] - risk_signals[1])

        confidence = (
            0.3 * conv_certainty
            + 0.3 * friction_certainty
            + 0.2 * intent_certainty
            + 0.2 * agreement
        )
        return max(0.0, min(1.0, confidence))

    @staticmethod
    def _recommend_action(session_score: float) -> str:
        """Map session score to an action via the threshold ladder."""
        for threshold, action in ACTION_THRESHOLDS:
            if session_score >= threshold:
                return action
        return "monitor"
