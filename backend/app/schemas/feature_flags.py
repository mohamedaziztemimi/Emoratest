"""Pydantic schemas for Feature Flags API.

Request and response models for CRUD, evaluation, and management.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


# ── Common Types ────────────────────────────────────────────────────────


FlagStatus = Literal["active", "inactive", "archived"]
RuleOperator = Literal["in", "not_in", "gt", "lt", "gte", "lte", "eq", "neq", "contains", "not_contains", "regex", "not_regex"]


class TargetingRule(BaseModel):
    """A single targeting rule for user attribute matching."""

    attribute: str = Field(..., description="User attribute to match (e.g., email, role, plan)")
    operator: RuleOperator = Field(..., description="Comparison operator")
    values: list[Any] = Field(..., min_length=1, description="Expected values")


class FlagVariant(BaseModel):
    """A multivariate variant with weight."""

    key: str = Field(..., description="Variant identifier")
    weight: float = Field(..., ge=0.0, description="Relative weight for selection")


class EnvironmentConfig(BaseModel):
    """Environment-specific flag configuration."""

    enabled: bool = Field(default=True)
    variant: str | None = Field(None, description="Override variant for this environment")


# ── Request Schemas ────────────────────────────────────────────────


class FeatureFlagCreateRequest(BaseModel):
    """Request to create a new feature flag."""

    key: str = Field(..., min_length=1, max_length=100, description="Unique flag slug")
    name: str = Field(..., min_length=1, max_length=255, description="Human-readable name")
    description: str | None = Field(None, max_length=1000)
    status: FlagStatus | None = Field(default="inactive", description="Initial status")
    rollout_percentage: float = Field(default=0.0, ge=0.0, le=100.0)
    targeting_rules: list[TargetingRule] | None = Field(None, max_length=50)
    variants: list[FlagVariant] | None = Field(None, max_length=20)
    kill_switch: bool = Field(default=False)
    environments: dict[str, EnvironmentConfig] | None = Field(None)
    created_by: str | None = Field(None, max_length=255, description="Creator identifier")

    @field_validator("key")
    @classmethod
    def validate_key(cls, v: str) -> str:
        """Validate flag key format (alphanumeric, underscores, hyphens)."""
        if not v:
            raise ValueError("Flag key cannot be empty")
        import re
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Flag key must contain only alphanumeric characters, underscores, and hyphens")
        return v.lower()

    @field_validator("variants")
    @classmethod
    def validate_variant_weights(cls, v: list[FlagVariant] | None) -> list[FlagVariant] | None:
        """Validate variant weights are positive."""
        if v:
            for variant in v:
                if variant.weight < 0:
                    raise ValueError(f"Variant {variant.key} must have non-negative weight")
        return v


class FeatureFlagUpdateRequest(BaseModel):
    """Request to update a feature flag (partial)."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)
    status: FlagStatus | None = None
    rollout_percentage: float | None = Field(None, ge=0.0, le=100.0)
    targeting_rules: list[TargetingRule] | None = Field(None, max_length=50)
    variants: list[FlagVariant] | None = Field(None, max_length=20)
    kill_switch: bool | None = None
    environments: dict[str, EnvironmentConfig] | None = Field(None)


class FlagEvaluationRequest(BaseModel):
    """Request to evaluate a flag for a user context."""

    user_context: dict[str, Any] = Field(
        ..., description="User attributes for targeting (e.g., user_id, email, role)"
    )
    environment: str = Field(default="production", description="Environment name")


class BulkEvaluationRequest(BaseModel):
    """Request to evaluate all flags for a user."""

    user_context: dict[str, Any] = Field(..., description="User attributes")
    environment: str = Field(default="production", description="Environment name")


class KillSwitchRequest(BaseModel):
    """Request to toggle kill switch."""

    enabled: bool = Field(..., description="Kill switch state")


class RolloutUpdateRequest(BaseModel):
    """Request to update rollout percentage."""

    percentage: float = Field(..., ge=0.0, le=100.0, description="New rollout percentage")


# ── Response Schemas ───────────────────────────────────────────────────


class FeatureFlagOut(BaseModel):
    """Response model for feature flag details."""

    id: str
    merchant_id: str
    key: str
    name: str
    description: str | None = None
    status: FlagStatus
    rollout_percentage: float
    targeting_rules: list[TargetingRule] | None = None
    variants: list[FlagVariant] | None = None
    kill_switch: bool
    environments: dict[str, EnvironmentConfig] | None = None
    created_by: str | None = None
    created_at: datetime
    updated_at: datetime


class FeatureFlagListResponse(BaseModel):
    """Response model for paginated flag list."""

    flags: list[FeatureFlagOut]
    total: int
    page: int
    page_size: int


class FlagEvaluationResponse(BaseModel):
    """Response for single flag evaluation."""

    flag_key: str
    enabled: bool
    variant: str | None = None
    reason: str = ""


class BulkEvaluationResponse(BaseModel):
    """Response for bulk flag evaluation."""

    flags: dict[str, dict[str, Any]]
    evaluated_at: str


class ExposureStatsResponse(BaseModel):
    """Response for exposure statistics."""

    flag_key: str
    days: int
    total_users: int
    exposed_users: int
    exposure_percentage: float
    variant_breakdown: dict[str, float]
