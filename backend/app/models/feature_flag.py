"""Feature flag model for progressive rollouts and kill switches.

Supports targeting rules, multivariate variants, and environment-specific configs.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from enum import Enum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

if TYPE_CHECKING:
    pass


class FeatureFlagStatus(str, Enum):
    """Feature flag lifecycle status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class FeatureFlag(Base):
    """Feature flag with progressive rollout and targeting capabilities."""

    __tablename__ = "feature_flags"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active','inactive','archived')",
            name="ck_feature_flags_status",
        ),
        CheckConstraint(
            "rollout_percentage >= 0 AND rollout_percentage <= 100",
            name="ck_feature_flags_rollout",
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
    )
    key: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # ── Status & Rollout ─────────────────────────────────────────────

    status: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'inactive'")
    )
    rollout_percentage: Mapped[float] = mapped_column(
        Float, nullable=False, server_default="0"
    )

    # ── Targeting & Variants ────────────────────────────────────────

    targeting_rules: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, default=None
    )
    variants: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=None)
    kill_switch: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )

    # ── Environment Configs ──────────────────────────────────────────

    environments: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, default=None
    )

    # ── Metadata ─────────────────────────────────────────────────────

    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    # ── Helper Methods ────────────────────────────────────────────────

    def is_active(self) -> bool:
        """Check if flag is active."""
        return self.status == FeatureFlagStatus.ACTIVE

    def is_killed(self) -> bool:
        """Check if kill switch is enabled."""
        return self.kill_switch is True

    def is_rollout_complete(self) -> bool:
        """Check if rollout is at 100%."""
        return self.rollout_percentage >= 100.0

    def get_environment_config(self, environment: str) -> dict | None:
        """Get configuration for a specific environment."""
        if not self.environments:
            return None
        return self.environments.get(environment)

    def has_variants(self) -> bool:
        """Check if flag has multivariate variants."""
        return self.variants is not None and len(self.variants) > 0

    def get_total_variant_weight(self) -> float:
        """Get sum of all variant weights."""
        if not self.variants:
            return 0.0
        return sum(v.get("weight", 0.0) for v in self.variants)

    def get_normalized_variants(self) -> list[dict]:
        """Get variants with normalized weights (sum to 1.0)."""
        if not self.variants:
            return []

        total_weight = self.get_total_variant_weight()
        if total_weight == 0:
            # Equal weights
            weight = 1.0 / len(self.variants)
            return [{**v, "weight": weight} for v in self.variants]

        return [
            {**v, "weight": v.get("weight", 0.0) / total_weight}
            for v in self.variants
        ]

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "id": str(self.id),
            "merchant_id": str(self.merchant_id),
            "key": self.key,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "rollout_percentage": self.rollout_percentage,
            "targeting_rules": self.targeting_rules,
            "variants": self.variants,
            "kill_switch": self.kill_switch,
            "environments": self.environments,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
