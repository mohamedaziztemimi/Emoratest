"""Pydantic schemas for SDK API endpoints (CONV-34)."""

from datetime import datetime

from pydantic import BaseModel, Field

# ── Session ────────────────────────────────────────────────────

class SessionCreateRequest(BaseModel):
    page_url: str
    started_at: datetime
    country_code: str | None = None
    device_type: str | None = Field(None, pattern=r"^(desktop|mobile|tablet)$")


class SessionCreateResponse(BaseModel):
    session_id: str


class SessionOutcomeRequest(BaseModel):
    outcome: str = Field(
        ...,
        pattern=r"^(purchase|abandon|signup|checkout_completed|demo_booked|lead_generated|trial_started)$",
        description="Conversion outcome type"
    )


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
