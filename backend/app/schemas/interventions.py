"""Pydantic schemas for Intervention Recommendation Engine (CONV-39)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class InterventionRecommendation(BaseModel):
    """A single recommended intervention for a session."""

    intervention_id: str
    name: str
    description: str
    trigger: str
    priority: float = Field(..., ge=0.0, le=1.0)
    psychological_basis: str
    estimated_lift: float | None = None


class SessionInterventionsResponse(BaseModel):
    """Recommendations for a specific session based on its risk profile."""

    session_id: str
    abandonment_risk: float | None = None
    friction_score: float | None = None
    intent_label: str | None = None
    recommendations: list[InterventionRecommendation]
    generated_at: datetime


class InterventionResultRecordRequest(BaseModel):
    """Record the outcome of a triggered intervention."""

    intervention_id: str = Field(..., min_length=1, max_length=16)
    session_id: str
    experiment_id: str | None = None
    outcome: str = Field(..., pattern=r"^(converted|dismissed|ignored|bounced)$")
    conversion_delta: float | None = Field(None, ge=-1.0, le=1.0)


class InterventionResultOut(BaseModel):
    id: str
    merchant_id: str
    intervention_id: str
    session_id: str | None
    experiment_id: str | None
    triggered_at: datetime
    outcome: str | None
    conversion_delta: float | None


class InterventionStatsResponse(BaseModel):
    """Aggregated performance stats for an intervention type."""

    intervention_id: str
    total_triggers: int
    converted: int
    dismissed: int
    ignored: int
    bounced: int
    conversion_rate: float
    avg_conversion_delta: float | None
