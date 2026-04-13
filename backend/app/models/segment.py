"""Segment model for flexible audience segmentation.

Supports behavioral, emotional, CRM, geo, and device targeting for
experiment assignment and personalization.

Condition tree structure:
{
  "operator": "AND" | "OR",
  "conditions": [
    {
      "attribute": str,
      "operator": "eq" | "neq" | "gt" | "lt" | "gte" | "lte" | "contains" | "in" | "not_in" | "regex",
      "value": any
    }
    | {
      "operator": "AND" | "OR",
      "conditions": [...]
    }
  ]
}

Supported attributes:
- user.country, user.city, user.device_type, user.browser, user.plan, user.ltv
- session.emotion, session.frustration_score, session.churn_risk
- event.page_url, event.referrer, event.utm_source, event.utm_campaign
- custom.* (any custom attribute from CRM sync)
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

if TYPE_CHECKING:
    pass


class SegmentType(str, Enum):
    """Type of segment."""

    STATIC = "static"
    DYNAMIC = "dynamic"
    EMOTIONAL = "emotional"


class SegmentOperator(str, Enum):
    """Operators for condition evaluation."""

    AND = "AND"
    OR = "OR"


class ConditionOperator(str, Enum):
    """Operators for individual conditions."""

    EQ = "eq"
    NEQ = "neq"
    GT = "gt"
    LT = "lt"
    GTE = "gte"
    LTE = "lte"
    CONTAINS = "contains"
    IN = "in"
    NOT_IN = "not_in"
    REGEX = "regex"
    EXISTS = "exists"
    NOT_EXISTS = "not_exists"


class Segment(Base):
    """Flexible audience segment with condition-based targeting.

    Supports nested AND/OR conditions up to 5 levels deep.
    Attributes can be from user, session, event, or custom namespaces.
    """

    __tablename__ = "segments"
    __table_args__ = (
        CheckConstraint(
            "segment_type IN ('static','dynamic','emotional')",
            name="ck_segments_type",
        ),
    )

    # ── Primary Fields ──────────────────────────────────────────────

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    merchant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # ── Conditions ─────────────────────────────────────────────────

    conditions: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=lambda: {"operator": "AND", "conditions": []}
    )

    # ── Type & Metadata ───────────────────────────────────────────

    segment_type: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'static'")
    )
    estimated_size: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Estimated number of users, updated async"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )

    # ── Timestamps ───────────────────────────────────────────────

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    # ── Helper Methods ─────────────────────────────────────────────

    def is_dynamic(self) -> bool:
        """Check if segment is dynamically evaluated."""
        return self.segment_type == SegmentType.DYNAMIC

    def is_emotional(self) -> bool:
        """Check if segment is emotion-based."""
        return self.segment_type == SegmentType.EMOTIONAL

    def get_condition_depth(self) -> int:
        """Get the maximum depth of nested conditions."""
        def depth(conditions: dict) -> int:
            if "conditions" not in conditions:
                return 0
            if not conditions["conditions"]:
                return 1
            return 1 + max(
                depth(c) if isinstance(c, dict) else 0 for c in conditions["conditions"]
            )

        return depth(self.conditions)

    def get_referenced_attributes(self) -> list[str]:
        """Extract all attribute references from conditions."""
        attributes: set[str] = set()

        def extract(attrs: dict) -> None:
            if "attribute" in attrs:
                attributes.add(attrs["attribute"])
            if "conditions" in attrs:
                for c in attrs["conditions"]:
                    if isinstance(c, dict):
                        extract(c)

        extract(self.conditions)
        return sorted(list(attributes))

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "id": str(self.id),
            "merchant_id": str(self.merchant_id),
            "name": self.name,
            "description": self.description,
            "conditions": self.conditions,
            "segment_type": self.segment_type,
            "estimated_size": self.estimated_size,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
