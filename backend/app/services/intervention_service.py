"""Intervention Recommendation Engine (CONV-39).

Maps session risk profiles to evidence-based psychological interventions.
Each intervention is grounded in behavioral economics research:
- Loss aversion (Kahneman & Tversky)
- Social proof (Cialdini)
- Urgency / scarcity (Cialdini)
- Commitment / consistency (Cialdini)
- Anchoring (Tversky & Kahneman)

The engine ranks interventions by match strength against the session's
feature vector and risk scores, returning the top-N most relevant.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InterventionTemplate:
    """Static intervention definition with targeting rules."""

    intervention_id: str
    name: str
    description: str
    trigger: str
    psychological_basis: str
    # Feature thresholds that make this intervention relevant
    min_abandonment_risk: float = 0.0
    max_abandonment_risk: float = 1.0
    relevant_friction_types: tuple[str, ...] = ()
    relevant_intents: tuple[str, ...] = ()
    base_priority: float = 0.5
    estimated_lift: float | None = None


# ── Intervention Catalog ──────────────────────────────────────────

CATALOG: list[InterventionTemplate] = [
    InterventionTemplate(
        intervention_id="INT-001",
        name="Exit Intent Popup — Limited Offer",
        description="Display a time-limited discount when user shows exit intent",
        trigger="Detected when user moves mouse toward browser tab/close button",
        psychological_basis="Loss aversion + scarcity: framing the discount as something "
        "the user will lose creates urgency to act",
        min_abandonment_risk=0.5,
        relevant_friction_types=("exit_intent", "hesitation"),
        relevant_intents=("browsing", "comparing"),
        base_priority=0.85,
        estimated_lift=0.12,
    ),
    InterventionTemplate(
        intervention_id="INT-002",
        name="Social Proof Notification",
        description="Show recent purchases or live visitor count near product/checkout",
        trigger="Detected during price deliberation or product comparison",
        psychological_basis="Social proof: seeing others buy reduces uncertainty and "
        "validates the purchase decision",
        min_abandonment_risk=0.3,
        relevant_friction_types=("hesitation",),
        relevant_intents=("browsing", "comparing"),
        base_priority=0.70,
        estimated_lift=0.08,
    ),
    InterventionTemplate(
        intervention_id="INT-003",
        name="Progress Indicator — Checkout Steps",
        description="Add visual progress bar showing checkout completion steps",
        trigger="Detected during checkout flow when user pauses > 10 seconds",
        psychological_basis="Commitment/consistency + goal gradient: users who see progress "
        "feel invested and accelerate toward completion",
        min_abandonment_risk=0.4,
        relevant_friction_types=("checkout_delay", "hesitation"),
        relevant_intents=("buying",),
        base_priority=0.75,
        estimated_lift=0.10,
    ),
    InterventionTemplate(
        intervention_id="INT-004",
        name="Rage Click Recovery",
        description="Detect rage clicks and offer contextual help or navigation assistance",
        trigger="Detected when user repeatedly clicks same element in frustration",
        psychological_basis="Frustration recovery: acknowledging difficulty and offering help "
        "prevents abandonment from usability friction",
        min_abandonment_risk=0.2,
        relevant_friction_types=("rage_click",),
        relevant_intents=("browsing", "comparing", "buying"),
        base_priority=0.80,
        estimated_lift=0.15,
    ),
    InterventionTemplate(
        intervention_id="INT-005",
        name="Price Anchoring — Compare Value",
        description="Show original price, savings amount, and per-unit cost comparison",
        trigger="Detected when user dwells on pricing for > 5 seconds",
        psychological_basis="Anchoring effect: presenting a higher reference price makes "
        "the actual price feel like a better deal",
        min_abandonment_risk=0.3,
        relevant_friction_types=("hesitation",),
        relevant_intents=("comparing",),
        base_priority=0.65,
        estimated_lift=0.07,
    ),
    InterventionTemplate(
        intervention_id="INT-006",
        name="Scroll Retreat — Content Simplification",
        description="Simplify page layout when user repeatedly scrolls back up",
        trigger="Detected when user scrolls back up 3+ times (overwhelmed signal)",
        psychological_basis="Cognitive load reduction: users retreating up the page are "
        "overwhelmed — simplifying reduces decision fatigue",
        min_abandonment_risk=0.3,
        relevant_friction_types=("scroll_retreat",),
        relevant_intents=("browsing", "comparing"),
        base_priority=0.60,
        estimated_lift=0.06,
    ),
    InterventionTemplate(
        intervention_id="INT-007",
        name="Urgency Timer — Cart Reservation",
        description="Show countdown timer reserving cart items for a limited time",
        trigger="Detected during buying intent with high abandonment risk",
        psychological_basis="Scarcity + loss aversion: time pressure combined with "
        "potential loss of reserved items drives completion",
        min_abandonment_risk=0.4,
        relevant_friction_types=("checkout_delay", "exit_intent"),
        relevant_intents=("buying",),
        base_priority=0.75,
        estimated_lift=0.11,
    ),
    InterventionTemplate(
        intervention_id="INT-008",
        name="Trust Signal — Security Badges",
        description="Prominently display payment security badges and guarantee icons",
        trigger="Detected at checkout when user hesitates > 15 seconds",
        psychological_basis="Trust transfer: established security symbols reduce perceived "
        "risk at the critical checkout moment",
        min_abandonment_risk=0.4,
        relevant_friction_types=("checkout_delay", "hesitation"),
        relevant_intents=("buying",),
        base_priority=0.70,
        estimated_lift=0.09,
    ),
]


def recommend_interventions(
    *,
    abandonment_risk: float | None,
    friction_score: float | None,
    intent_label: str | None,
    features: dict | None = None,
    max_results: int = 3,
) -> list[dict]:
    """Score and rank interventions for a session's risk profile.

    Returns the top-N interventions sorted by match priority (descending).
    """
    risk = abandonment_risk or 0.0
    friction = friction_score or 0.0
    intent = intent_label or "browsing"
    feats = features or {}

    scored: list[tuple[float, InterventionTemplate]] = []

    for tmpl in CATALOG:
        # Gate: risk must be within the template's targeting range
        if risk < tmpl.min_abandonment_risk:
            continue
        if risk > tmpl.max_abandonment_risk:
            continue

        score = tmpl.base_priority

        # Boost: risk alignment — higher risk = more urgent interventions score higher
        score += risk * 0.15

        # Boost: friction alignment
        if friction > 0.5:
            score += 0.05

        # Boost: intent match
        if tmpl.relevant_intents and intent in tmpl.relevant_intents:
            score += 0.10

        # Boost: feature-specific triggers
        if "rage_click" in tmpl.relevant_friction_types:
            rage = feats.get("rage_click_score", 0)
            if rage > 0.3:
                score += 0.10
        if "exit_intent" in tmpl.relevant_friction_types:
            exits = feats.get("exit_intent_count", 0)
            if exits >= 1:
                score += 0.08
        if "checkout_delay" in tmpl.relevant_friction_types:
            checkout_hes = feats.get("checkout_hesitation_s", 0)
            if checkout_hes > 10:
                score += 0.08
        if "scroll_retreat" in tmpl.relevant_friction_types:
            retreats = feats.get("scroll_retreat_count", 0)
            if retreats >= 3:
                score += 0.08

        # Clamp to 0-1
        score = min(1.0, max(0.0, score))
        scored.append((score, tmpl))

    # Sort by score descending, take top N
    scored.sort(key=lambda x: x[0], reverse=True)

    results = []
    for priority, tmpl in scored[:max_results]:
        results.append({
            "intervention_id": tmpl.intervention_id,
            "name": tmpl.name,
            "description": tmpl.description,
            "trigger": tmpl.trigger,
            "priority": round(priority, 4),
            "psychological_basis": tmpl.psychological_basis,
            "estimated_lift": tmpl.estimated_lift,
        })

    return results
