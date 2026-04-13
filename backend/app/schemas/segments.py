"""Pydantic schemas for Segment CRUD and targeting evaluation."""

from datetime import datetime
from typing import Any, Literal, Union

from pydantic import BaseModel, Field, field_validator

# ── Types ────────────────────────────────────────────────────────

SegmentType = Literal["static", "dynamic", "emotional"]
ConditionOperatorType = Literal["eq", "neq", "gt", "lt", "gte", "lte", "contains", "in", "not_in", "regex", "exists", "not_exists"]
SegmentOperatorType = Literal["AND", "OR"]


# ── Condition Tree Schemas ─────────────────────────────────────────

class LeafCondition(BaseModel):
    """A leaf condition in the condition tree."""

    attribute: str = Field(..., description="Attribute path (e.g., user.country, session.frustration_score)")
    operator: ConditionOperatorType = Field(..., description="Comparison operator")
    value: Any = Field(..., description="Value to compare against")


class ConditionGroup(BaseModel):
    """A group of conditions with AND/OR logic."""

    operator: SegmentOperatorType = Field(default="AND", description="AND or OR logic")
    conditions: list[Union[LeafCondition, "ConditionGroup"]] = Field(
        default_factory=list,
        description="Nested conditions"
    )


# Resolve forward reference
ConditionGroup.model_rebuild()


class SegmentConditions(BaseModel):
    """Root condition tree for a segment."""

    operator: SegmentOperatorType = Field(default="AND", description="AND or OR logic")
    conditions: list[LeafCondition | ConditionGroup] = Field(
        default_factory=list,
        description="List of conditions"
    )


# ── Segment CRUD Schemas ─────────────────────────────────────────

class SegmentCreateRequest(BaseModel):
    """Request to create a new segment."""

    name: str = Field(..., min_length=1, max_length=255, description="Segment name")
    description: str | None = Field(None, max_length=2000, description="Segment description")
    conditions: SegmentConditions = Field(
        default_factory=lambda: SegmentConditions(operator="AND", conditions=[]),
        description="Condition tree for matching users"
    )
    segment_type: SegmentType = Field(default="static", description="Segment type")

    @field_validator("conditions")
    @classmethod
    def validate_conditions(cls, v: SegmentConditions) -> SegmentConditions:
        """Validate condition tree depth."""
        def check_depth(conditions: dict, depth: int = 0) -> int:
            max_depth = depth
            if "conditions" in conditions:
                for cond in conditions["conditions"]:
                    if isinstance(cond, dict):
                        if "operator" in cond:
                            current_depth = check_depth(cond, depth + 1)
                            max_depth = max(max_depth, current_depth)
            return max_depth

        conditions_dict = v.model_dump()
        max_depth = check_depth(conditions_dict)

        if max_depth > 5:
            raise ValueError("Condition depth exceeds maximum of 5 levels")

        return v


class SegmentUpdateRequest(BaseModel):
    """Request to update a segment."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=2000)
    conditions: SegmentConditions | None = None
    is_active: bool | None = None


class SegmentOut(BaseModel):
    """Segment response."""

    id: str
    merchant_id: str
    name: str
    description: str | None
    conditions: dict
    segment_type: SegmentType
    estimated_size: int | None
    is_active: bool
    created_at: datetime | None
    updated_at: datetime | None


class SegmentListResponse(BaseModel):
    """Paginated list of segments."""

    segments: list[SegmentOut]
    total: int
    page: int
    page_size: int


# ── Evaluation Schemas ────────────────────────────────────────────

class SegmentEvaluateRequest(BaseModel):
    """Request to test a segment against sample user context."""

    user_context: dict = Field(
        ...,
        description="User context with nested user/session/event data",
        example={
            "user_id": "user_123",
            "user": {
                "country": "US",
                "city": "New York",
                "device_type": "desktop",
                "browser": "Chrome",
                "plan": "premium",
                "ltv": 1500,
            },
            "session": {
                "emotion": "frustration",
                "frustration_score": 0.8,
                "churn_risk": 0.7,
            },
            "event": {
                "page_url": "/checkout",
                "referrer": "google.com",
                "utm_source": "newsletter",
                "utm_campaign": "spring_sale",
            },
        }
    )


class SegmentEvaluateResponse(BaseModel):
    """Response from segment evaluation."""

    segment_id: str
    matches: bool
    matched_conditions: list[str] | None
    failed_conditions: list[str] | None


# ── Sync Schemas ───────────────────────────────────────────────

class CRMAttributeSync(BaseModel):
    """CRM attribute for a single user."""

    user_id: str = Field(..., description="User ID")
    attributes: dict = Field(
        ...,
        description="Attributes to sync (stored under custom.* namespace)",
        example={"plan": "premium", "ltv": 1500, "tier": "gold"}
    )


class CRMSyncRequest(BaseModel):
    """Bulk CRM attribute sync request."""

    syncs: list[CRMAttributeSync] = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="List of user attributes to sync"
    )


class CRMSyncResponse(BaseModel):
    """Response from CRM sync."""

    synced: int
    failed: int
    errors: list[str] = Field(default_factory=list)


# ── Preview Schemas ─────────────────────────────────────────────

class SampleUser(BaseModel):
    """Anonymized sample user that matches the segment."""

    user_id_hash: str
    matched_attributes: dict[str, Any]


class SegmentPreviewResponse(BaseModel):
    """Preview of segment size and sample users."""

    segment_id: str
    estimated_size: int
    sample_size: int
    confidence: float
    sample_users: list[SampleUser]


# ── Emotion Profile Schema ───────────────────────────────────────

class EmotionProfileOut(BaseModel):
    """Emotional profile of a segment."""

    segment_id: str
    dominant_emotion: str
    frustration_avg: float
    confusion_avg: float
    delight_avg: float
    anxiety_avg: float
    focus_avg: float
    satisfaction_avg: float
    hesitation_avg: float
    conversion_rate: float
    total_users: int


# ── Emotional Cohort Schema ─────────────────────────────────────

class EmotionalCohortRequest(BaseModel):
    """Request to create an emotional cohort."""

    emotion: str = Field(..., description="Emotion to target (e.g., frustration)")
    min_score: float = Field(..., ge=0.0, le=1.0, description="Minimum score threshold")
    experiment_id: str = Field(..., description="Associated experiment ID")


class EmotionalCohortResponse(BaseModel):
    """Response from creating an emotional cohort."""

    segment_id: str
    name: str
    description: str
    conditions: dict
    segment_type: SegmentType
