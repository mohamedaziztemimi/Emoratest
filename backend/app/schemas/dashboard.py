"""Pydantic schemas for dashboard API endpoints (CONV-37 to CONV-42)."""

from datetime import datetime

from pydantic import BaseModel, Field

# ── Session list ──────────────────────────────────────────────────

class SessionListItem(BaseModel):
    id: str
    page_url: str
    started_at: datetime
    ended_at: datetime | None = None
    outcome: str
    abandonment_risk: float | None = None
    friction_score: float | None = None
    intent_label: str | None = None
    country_code: str | None = None
    device_type: str | None = None


class SessionListResponse(BaseModel):
    sessions: list[SessionListItem]
    total: int
    page: int
    page_size: int


# ── Session detail ────────────────────────────────────────────────

class EventOut(BaseModel):
    id: int
    type: str
    ts: datetime
    x: float | None = None
    y: float | None = None
    velocity: float | None = None
    element_id: str | None = None
    metadata: dict | None = None


class SessionFeaturesOut(BaseModel):
    hesitation_score: float | None = None
    price_dwell_time_s: float | None = None
    rage_click_score: float | None = None
    scroll_retreat_count: int | None = None
    exit_intent_count: int | None = None
    checkout_hesitation_s: float | None = None
    velocity_variance: float | None = None
    session_duration_s: float | None = None
    computed_at: datetime | None = None


class SessionDetailResponse(BaseModel):
    id: str
    page_url: str
    started_at: datetime
    ended_at: datetime | None = None
    outcome: str
    abandonment_risk: float | None = None
    friction_score: float | None = None
    intent_label: str | None = None
    country_code: str | None = None
    device_type: str | None = None
    events: list[EventOut]
    features: SessionFeaturesOut | None = None


# ── Analytics: Friction Map ────────────────────────────────────────

class FrictionMapItem(BaseModel):
    element_id: str
    event_count: int
    avg_hesitation: float
    click_count: int
    rage_click_count: int
    rage_click_rate: float


class FrictionMapResponse(BaseModel):
    elements: list[FrictionMapItem]
    total_elements: int
    date_from: datetime | None = None
    date_to: datetime | None = None


# ── Analytics: Funnel ──────────────────────────────────────────────

class FunnelStep(BaseModel):
    step: str
    sessions: int
    drop_off: int
    drop_off_rate: float = Field(..., ge=0.0, le=1.0)
    avg_friction_score: float | None = None


class FunnelResponse(BaseModel):
    steps: list[FunnelStep]
    total_sessions: int
    conversion_rate: float
    date_from: datetime | None = None
    date_to: datetime | None = None
