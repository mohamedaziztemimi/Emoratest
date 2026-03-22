"""Pydantic schemas for Cohort & Segment Analytics (CONV-40)."""

from datetime import datetime

from pydantic import BaseModel


class CohortBucket(BaseModel):
    """One segment bucket with aggregated metrics."""

    label: str
    session_count: int
    purchase_count: int
    abandon_count: int
    conversion_rate: float
    avg_abandonment_risk: float | None = None
    avg_friction_score: float | None = None


class CohortAnalyticsResponse(BaseModel):
    """Cohort analysis results segmented by the requested dimension."""

    dimension: str
    buckets: list[CohortBucket]
    total_sessions: int
    overall_conversion_rate: float
    date_from: datetime | None = None
    date_to: datetime | None = None


class RiskDistributionBucket(BaseModel):
    """Histogram bucket for risk score distribution."""

    range_label: str
    range_min: float
    range_max: float
    session_count: int
    conversion_rate: float


class RiskDistributionResponse(BaseModel):
    """Distribution of abandonment risk across merchant sessions."""

    buckets: list[RiskDistributionBucket]
    total_sessions: int
    avg_risk: float | None = None
    median_risk: float | None = None
