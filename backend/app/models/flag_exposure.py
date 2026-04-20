"""Flag exposure model for tracking variant assignments.

Records which visitors saw which flag variants for conversion tracking.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

if TYPE_CHECKING:
    pass


class FlagExposure(Base):
    """Records a user's exposure to a feature flag variant.

    Used to calculate conversion rates per variant by tracking
    which users saw which variants and their subsequent outcomes.
    """

    __tablename__ = "flag_exposures"
    __table_args__ = (
        Index("ix_flag_exposures_flag_visitor", "flag_id", "visitor_id"),
        Index("ix_flag_exposures_flag_variant", "flag_id", "variant"),
        Index("ix_flag_exposures_timestamp", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    flag_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("feature_flags.id", ondelete="CASCADE"),
        nullable=False,
    )
    visitor_id: Mapped[str] = mapped_column(String(255), nullable=False)
    variant: Mapped[str | None] = mapped_column(String(100), nullable=True)
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="SET NULL"),
        nullable=True,
    )
    enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
