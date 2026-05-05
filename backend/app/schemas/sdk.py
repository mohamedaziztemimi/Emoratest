"""Pydantic schemas for SDK API endpoints (CONV-34)."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


# ── Survey config ──────────────────────────────────────────────────

class SurveyConfigResponse(BaseModel):
    """Survey configuration returned to SDK on session init."""
    enabled: bool
    trigger: Literal["exit_intent", "scroll_75", "time_30s"] | None = None
    sample_rate: float | None = None
    pages: list[str] | None = None

# ── Session ────────────────────────────────────────────────────

class SessionCreateRequest(BaseModel):
    page_url: str
    started_at: datetime
    country_code: str | None = None
    device_type: str | None = Field(None, pattern=r"^(desktop|mobile|tablet)$")
    environment: str | None = Field("production", pattern=r"^(test|production)$")


class SessionCreateResponse(BaseModel):
    session_id: str
    survey: SurveyConfigResponse | None = None


class SessionOutcomeRequest(BaseModel):
    outcome: str = Field(
        ...,
        pattern=r"^(purchase|abandon|signup|checkout_completed|demo_booked|lead_generated|trial_started)$",
        description="Conversion outcome type"
    )


# ── Session Feedback ─────────────────────────────────────────────

class SessionFeedbackRequest(BaseModel):
    rating: str = Field(
        ...,
        pattern=r"^(negative|neutral|positive)$",
        description="User feedback rating"
    )
    page_url: str


# ── Events ─────────────────────────────────────────────────────

class EventItem(BaseModel):
    type: str = Field(
        ..., pattern=r"^(mouse_move|click|scroll|exit_intent|visibility|mouse_summary)$"
    )
    ts: datetime
    x: float | None = None
    y: float | None = None
    velocity: float | None = None
    element_id: str | None = Field(None, max_length=128)
    metadata: dict | None = None
    # Semantic enrichment fields (business-readable)
    label: str | None = Field(None, max_length=256)
    element_type: str | None = Field(None, max_length=32)
    section: str | None = Field(None, max_length=64)
    selector: str | None = Field(None, max_length=512)


class EventBatchRequest(BaseModel):
    session_id: str
    events: list[EventItem] = Field(..., min_length=1, max_length=200)
    page_url: str | None = None  # For auto-creating sessions if needed
    device_type: str | None = Field(None, pattern=r"^(desktop|mobile|tablet)$")  # Device type for session auto-creation
    country_code: str | None = Field(None, min_length=2, max_length=2)  # ISO country code for session auto-creation
