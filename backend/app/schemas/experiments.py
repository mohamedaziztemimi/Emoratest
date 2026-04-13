"""Pydantic schemas for Experiment CRUD and A/B test results (CONV-38, CONV-41).

Extended to support A/B/n, MVT, split URL, multi-page, and server-side experiments.
"""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

# ── Experiment CRUD ──────────────────────────────────────────────

ExperimentType = Literal["ab", "mvt", "split_url", "multipage", "server_side"]
FrictionType = Literal["hesitation", "rage_click", "scroll_retreat", "exit_intent", "checkout_delay"]
ExperimentResult = Literal["a_wins", "b_wins", "no_diff", "inconclusive"]


class SplitUrlConfig(BaseModel):
    """Configuration for split URL experiments."""

    control_url: str = Field(..., min_length=1, max_length=2048)
    variant_urls: list[str] = Field(..., min_length=1, max_length=9)


class ExperimentCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=256)
    hypothesis: str | None = Field(None, max_length=2000)
    page_element: str | None = Field(None, max_length=128)
    friction_type: FrictionType | None = None
    variant_a: str | None = Field(None, max_length=2000)
    variant_b: str | None = Field(None, max_length=2000)

    # ── New fields for full experiment type coverage ──

    experiment_type: ExperimentType = Field(default="ab")
    n_variants: int = Field(default=2, ge=2, le=10, description="Number of variants (2-10)")
    flicker_free: bool = Field(
        default=True, description="Use async snippet or edge delivery to prevent flicker"
    )
    page_urls: list[str] | None = Field(
        None, max_length=10, description="List of URLs for multi-page experiments"
    )
    split_url_config: SplitUrlConfig | None = None
    server_side_key: str | None = Field(None, max_length=64, description="SDK key for server-side delivery")

    @model_validator(mode="after")
    def validate_experiment_config(self) -> "ExperimentCreateRequest":
        """Validate experiment configuration based on experiment_type."""
        errors: list[str] = []

        if self.experiment_type == "split_url" and not self.split_url_config:
            errors.append("split_url type requires split_url_config")

        if self.experiment_type == "multipage" and (not self.page_urls or len(self.page_urls) == 0):
            errors.append("multipage type requires non-empty page_urls")

        if self.experiment_type == "server_side" and not self.server_side_key:
            errors.append("server_side type requires server_side_key")

        if self.experiment_type == "mvt" and self.n_variants < 2:
            errors.append("MVT experiments require at least 2 variants")

        if errors:
            raise ValueError("; ".join(errors))

        return self


class ExperimentUpdateRequest(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=256)
    hypothesis: str | None = Field(None, max_length=2000)
    page_element: str | None = Field(None, max_length=128)
    friction_type: FrictionType | None = None
    variant_a: str | None = Field(None, max_length=2000)
    variant_b: str | None = Field(None, max_length=2000)
    result: ExperimentResult | None = None
    conversion_delta: float | None = Field(None, ge=-1.0, le=1.0)
    sample_size: int | None = Field(None, ge=0)
    ran_at: date | None = None

    # ── New fields for full experiment type coverage ──

    experiment_type: ExperimentType | None = None
    n_variants: int | None = Field(None, ge=2, le=10)
    flicker_free: bool | None = None
    page_urls: list[str] | None = Field(None, max_length=10)
    split_url_config: SplitUrlConfig | None = None
    server_side_key: str | None = Field(None, max_length=64)

    @model_validator(mode="after")
    def validate_update_config(self) -> "ExperimentUpdateRequest":
        """Validate experiment configuration on update."""
        errors: list[str] = []

        if self.experiment_type == "split_url" and not self.split_url_config:
            errors.append("split_url type requires split_url_config")

        if self.experiment_type == "multipage" and (not self.page_urls or len(self.page_urls) == 0):
            errors.append("multipage type requires non-empty page_urls")

        if self.experiment_type == "server_side" and not self.server_side_key:
            errors.append("server_side type requires server_side_key")

        if errors:
            raise ValueError("; ".join(errors))

        return self


class ExperimentOut(BaseModel):
    id: str
    merchant_id: str
    title: str
    hypothesis: str | None = None
    page_element: str | None = None
    friction_type: FrictionType | None = None
    variant_a: str | None = None
    variant_b: str | None = None
    result: ExperimentResult | None = None
    conversion_delta: float | None = None
    sample_size: int | None = None
    ran_at: date | None = None
    source: str | None = None
    created_at: datetime
    updated_at: datetime

    # ── New fields for full experiment type coverage ──

    experiment_type: ExperimentType
    n_variants: int
    flicker_free: bool
    page_urls: list[str] | None = None
    split_url_config: SplitUrlConfig | None = None
    server_side_key: str | None = None


class ExperimentListResponse(BaseModel):
    experiments: list[ExperimentOut]
    total: int
    page: int
    page_size: int


# ── A/B Test Results (CONV-41) ───────────────────────────────────


class ABResultRecordRequest(BaseModel):
    """Record the outcome of an A/B experiment."""

    result: ExperimentResult = Field(...)
    conversion_delta: float = Field(..., ge=-1.0, le=1.0)
    sample_size: int = Field(..., ge=1)
    ran_at: date


class ABStatisticalSummary(BaseModel):
    """Statistical significance summary for an experiment."""

    experiment_id: str
    title: str
    result: ExperimentResult | None = None
    conversion_delta: float | None = None
    sample_size: int | None = None
    confidence_level: float | None = None
    is_significant: bool = False
    p_value: float | None = None
    power: float | None = None
    recommendation: str = "insufficient_data"
