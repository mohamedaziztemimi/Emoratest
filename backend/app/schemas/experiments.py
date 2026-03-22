"""Pydantic schemas for Experiment CRUD and A/B test results (CONV-38, CONV-41)."""

from datetime import date, datetime

from pydantic import BaseModel, Field

# ── Experiment CRUD ──────────────────────────────────────────────


class ExperimentCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=256)
    hypothesis: str | None = Field(None, max_length=2000)
    page_element: str | None = Field(None, max_length=128)
    friction_type: str | None = Field(
        None, pattern=r"^(hesitation|rage_click|scroll_retreat|exit_intent|checkout_delay)$"
    )
    variant_a: str | None = Field(None, max_length=2000)
    variant_b: str | None = Field(None, max_length=2000)


class ExperimentUpdateRequest(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=256)
    hypothesis: str | None = Field(None, max_length=2000)
    page_element: str | None = Field(None, max_length=128)
    friction_type: str | None = Field(
        None, pattern=r"^(hesitation|rage_click|scroll_retreat|exit_intent|checkout_delay)$"
    )
    variant_a: str | None = Field(None, max_length=2000)
    variant_b: str | None = Field(None, max_length=2000)
    result: str | None = Field(
        None, pattern=r"^(a_wins|b_wins|no_diff|inconclusive)$"
    )
    conversion_delta: float | None = Field(None, ge=-1.0, le=1.0)
    sample_size: int | None = Field(None, ge=0)
    ran_at: date | None = None


class ExperimentOut(BaseModel):
    id: str
    merchant_id: str
    title: str
    hypothesis: str | None = None
    page_element: str | None = None
    friction_type: str | None = None
    variant_a: str | None = None
    variant_b: str | None = None
    result: str | None = None
    conversion_delta: float | None = None
    sample_size: int | None = None
    ran_at: date | None = None
    source: str | None = None
    created_at: datetime


class ExperimentListResponse(BaseModel):
    experiments: list[ExperimentOut]
    total: int
    page: int
    page_size: int


# ── A/B Test Results (CONV-41) ───────────────────────────────────


class ABResultRecordRequest(BaseModel):
    """Record the outcome of an A/B experiment."""

    result: str = Field(..., pattern=r"^(a_wins|b_wins|no_diff|inconclusive)$")
    conversion_delta: float = Field(..., ge=-1.0, le=1.0)
    sample_size: int = Field(..., ge=1)
    ran_at: date


class ABStatisticalSummary(BaseModel):
    """Statistical significance summary for an experiment."""

    experiment_id: str
    title: str
    result: str | None
    conversion_delta: float | None
    sample_size: int | None
    confidence_level: float | None = None
    is_significant: bool = False
    p_value: float | None = None
    power: float | None = None
    recommendation: str = "insufficient_data"
