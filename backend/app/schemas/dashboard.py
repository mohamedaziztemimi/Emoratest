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
    primary_emotion: str | None = None
    emotion_confidence: float | None = None
    valence: float | None = None
    arousal: float | None = None
    ip_address: str | None = None
    user_agent: str | None = None


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
    # Semantic enrichment fields (business-readable)
    label: str | None = None
    element_type: str | None = None
    section: str | None = None
    selector: str | None = None
    # Human-readable description from enrichment service
    readable_description: str | None = None


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
    primary_emotion: str | None = None
    emotion_confidence: float | None = None
    emotion_scores: dict | None = None
    valence: float | None = None
    arousal: float | None = None
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


# ── Dashboard Stats Summary ──────────────────────────────────────────


class DashboardStatsResponse(BaseModel):
    """Summary stats for the dashboard overview page."""
    avg_emotion_confidence: float | None = None  # Average emotion confidence across all sessions
    frustration_count: int = 0  # Count of sessions with primary_emotion = 'frustrated'


# ── Analytics: Heatmap (Raw x,y coordinates) ────────────────────────


class HeatmapPoint(BaseModel):
    x: float
    y: float
    value: float = 1.0
    type: str = "click"


class HeatmapSession(BaseModel):
    id: str
    started_at: datetime
    dominant_emotion: str | None = None
    emotion_confidence: float | None = None


class HeatmapResponse(BaseModel):
    points: list[HeatmapPoint]
    sessions: list[HeatmapSession]
    total_points: int
    page_url: str | None = None


# ── Analytics: Element Emotions (per-element emotion data) ────────────────


class ElementEmotionItem(BaseModel):
    element_id: str
    label: str | None = None  # Human-readable element label
    element_type: str | None = None  # button, link, input, etc.
    section: str | None = None  # header, footer, main, etc.
    event_count: int
    click_count: int
    rage_click_count: int
    rage_click_rate: float
    avg_hesitation: float
    dominant_emotion: str | None = None
    emotion_confidence: float | None = None
    emotion_breakdown: dict | None = None
    session_count: int = 0


class ElementEmotionResponse(BaseModel):
    elements: list[ElementEmotionItem]
    total_elements: int
    page_url: str | None = None


# ── Analytics: Why-Analysis ────────────────────────────────────────


class EmotionConversionItem(BaseModel):
    emotion: str
    total_sessions: int
    converted: int
    abandoned: int
    conversion_rate: float
    avg_friction: float | None = None
    avg_abandonment_risk: float | None = None


class EmotionConversionResponse(BaseModel):
    items: list[EmotionConversionItem]
    total_sessions: int
    overall_conversion_rate: float


class DropOffReasonItem(BaseModel):
    page_url: str
    emotion: str
    sessions: int
    drop_off_rate: float
    avg_friction: float | None = None
    avg_abandonment_risk: float | None = None


class DropOffReasonsResponse(BaseModel):
    reasons: list[DropOffReasonItem]
    total_patterns: int


class WhyAnalysisSummary(BaseModel):
    total_sessions: int
    sessions_with_emotion: int
    overall_conversion_rate: float
    top_drop_off_emotion: str | None = None
    top_drop_off_emotion_rate: float | None = None
    top_converting_emotion: str | None = None
    top_converting_emotion_rate: float | None = None
    avg_friction_abandoned: float | None = None
    avg_friction_converted: float | None = None


# ── Analytics: Why-Analysis Emotion Trend ────────────────────────


class EmotionTrendDay(BaseModel):
    date: str
    emotions: dict  # e.g. {"confusion": 3, "delight": 5, "anxiety": 1}
    total: int
    conversion_rate: float | None = None


class EmotionTrendResponse(BaseModel):
    days: list[EmotionTrendDay]
    emotions_seen: list[str]


# ── Bulk Delete Request ────────────────────────────────────────────


class BulkDeleteRequest(BaseModel):
    session_ids: list[str] = Field(..., min_length=1, max_length=100)


# ── Alerts ────────────────────────────────────────────────────────


class AlertResponse(BaseModel):
    alerts: list
    total: int = 0


class AlertCountResponse(BaseModel):
    count: int = 0
