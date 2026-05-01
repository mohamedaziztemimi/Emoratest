import uuid
from datetime import datetime

from sqlalchemy import CHAR, CheckConstraint, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Session(Base):
    __tablename__ = "sessions"
    __table_args__ = (
        CheckConstraint(
            "outcome IN ('purchase','abandon','unknown','signup','checkout_completed','demo_booked','lead_generated','trial_started')",
            name="ck_sessions_outcome",
        ),
        CheckConstraint(
            "abandonment_risk BETWEEN 0 AND 1",
            name="ck_sessions_abandonment_risk",
        ),
        CheckConstraint(
            "friction_score BETWEEN 0 AND 1",
            name="ck_sessions_friction_score",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    merchant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
    )
    page_url: Mapped[str] = mapped_column(Text, nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    outcome: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default="unknown"
    )
    abandonment_risk: Mapped[float | None] = mapped_column(Float)
    friction_score: Mapped[float | None] = mapped_column(Float)
    intent_label: Mapped[str | None] = mapped_column(String(32))
    country_code: Mapped[str | None] = mapped_column(CHAR(2))
    device_type: Mapped[str | None] = mapped_column(String(16))
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Emotion model fields
    primary_emotion: Mapped[str | None] = mapped_column(
        String(32), nullable=True
    )
    emotion_confidence: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    emotion_scores: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True
    )
    valence: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    arousal: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )

    # Tracking fields
    ip_address: Mapped[str | None] = mapped_column(
        String(45), nullable=True  # IPv6 can be up to 45 chars
    )
    user_agent: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
