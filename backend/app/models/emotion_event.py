"""Emotion event and session models.

Stores real-time emotion classifications, aggregated session summaries,
and relationships to experiments and revenue outcomes.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class EmotionSource(str, Enum):
    """Source of emotion classification."""

    BEHAVIORAL = "behavioral"
    WEBCAM = "webcam"
    VOICE = "voice"
    SURVEY = "survey"


class EmotionEvent(Base):
    """Individual emotion classification event.

    Stores each emotion prediction with full context including
    trigger features, confidence, valence-arousal, and source.
    """

    __tablename__ = "emotion_events"
    __table_args__ = (
        Index("ix_emotion_events_session_id", "session_id"),
        Index("ix_emotion_events_user_id", "user_id"),
        Index("ix_emotion_events_experiment_id", "experiment_id"),
        Index("ix_emotion_events_timestamp", "timestamp"),
    )

    # ── Primary Fields ──────────────────────────────────────────────

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    experiment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("experiments.id", ondelete="SET NULL"),
        nullable=True,
    )
    variant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=True)

    # ── Emotion Classification ─────────────────────────────────────────────

    primary_emotion: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    valence: Mapped[float] = mapped_column(Float, nullable=False)
    arousal: Mapped[float] = mapped_column(Float, nullable=False)

    # ── Trigger Context ────────────────────────────────────────────────

    trigger_features: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, default=None
    )

    # ── Session Context ───────────────────────────────────────────────

    page_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    source: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'behavioral'")
    )

    # ── Metadata ─────────────────────────────────────────────────────

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    # ── Helper Methods ───────────────────────────────────────────────

    def is_high_confidence(self, threshold: float = 0.7) -> bool:
        """Check if this is a high-confidence prediction."""
        return self.confidence >= threshold

    def is_negative_emotion(self) -> bool:
        """Check if this is a negative emotion."""
        negative_emotions = {"confusion", "frustration", "anxiety", "boredom"}
        return self.primary_emotion in negative_emotions

    def is_positive_emotion(self) -> bool:
        """Check if this is a positive emotion."""
        positive_emotions = {"delight", "satisfaction", "focus"}
        return self.primary_emotion in positive_emotions

    def get_emotion_sentiment(self) -> str:
        """Get sentiment category (positive, negative, neutral)."""
        if self.valence < -0.2:
            return "negative"
        elif self.valence > 0.2:
            return "positive"
        else:
            return "neutral"

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "id": str(self.id),
            "session_id": str(self.session_id),
            "user_id": str(self.user_id) if self.user_id else None,
            "experiment_id": str(self.experiment_id) if self.experiment_id else None,
            "variant_id": str(self.variant_id) if self.variant_id else None,
            "primary_emotion": self.primary_emotion,
            "confidence": self.confidence,
            "valence": self.valence,
            "arousal": self.arousal,
            "trigger_features": self.trigger_features,
            "page_url": self.page_url,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "source": self.source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class EmotionSession(Base):
    """Aggregated emotion summary per session.

    Stores session-level emotion aggregates including dominant emotion,
    emotion timeline, weighted scores, and outcome links.
    """

    __tablename__ = "emotion_sessions"
    __table_args__ = (
        Index("ix_emotion_sessions_session_id", "session_id", unique=True),
        Index("ix_emotion_sessions_user_id", "user_id"),
        Index("ix_emotion_sessions_experiment_id", "experiment_id"),
    )

    # ── Primary Fields ──────────────────────────────────────────────

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, unique=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    experiment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("experiments.id", ondelete="SET NULL"),
        nullable=True,
    )
    variant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=True)

    # ── Emotion Summary ───────────────────────────────────────────────

    dominant_emotion: Mapped[str] = mapped_column(String(32), nullable=True)

    # Emotion timeline: list of { timestamp, emotion, confidence }
    emotion_timeline: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=None)

    # Weighted emotion scores (0-1 range)
    frustration_score: Mapped[float] = mapped_column(
        Float, nullable=False, server_default="0"
    )
    confusion_score: Mapped[float] = mapped_column(
        Float, nullable=False, server_default="0"
    )
    delight_score: Mapped[float] = mapped_column(
        Float, nullable=False, server_default="0"
    )

    # ── Outcome Links ─────────────────────────────────────────────────

    converted: Mapped[bool] = mapped_column(Boolean, nullable=True, default=None)
    revenue: Mapped[float] = mapped_column(Float, nullable=True, default=None)
    churn_risk: Mapped[float] = mapped_column(
        Float, nullable=True, default=None
    )

    # ── Timestamps ───────────────────────────────────────────────────

    first_event_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    last_event_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    # ── Helper Methods ───────────────────────────────────────────────

    def get_primary_sentiment(self) -> str:
        """Get sentiment of dominant emotion."""
        emotion_to_sentiment = {
            "confusion": "negative",
            "frustration": "negative",
            "anxiety": "negative",
            "boredom": "negative",
            "delight": "positive",
            "satisfaction": "positive",
            "focus": "positive",
            "hesitation": "neutral",
        }
        return emotion_to_sentiment.get(self.dominant_emotion, "neutral")

    def is_at_risk(self) -> bool:
        """Check if session has negative emotion risk."""
        return (
            self.frustration_score > 0.5
            or self.confusion_score > 0.5
            or (self.churn_risk is not None and self.churn_risk > 0.5)
        )

    def update_emotion_scores(
        self,
        emotion_scores: dict[str, float],
    ) -> None:
        """Update weighted emotion scores from recent classifications.

        Args:
            emotion_scores: Dict of emotion to confidence score.
        """
        if "frustration" in emotion_scores:
            self.frustration_score = emotion_scores["frustration"]
        if "confusion" in emotion_scores:
            self.confusion_score = emotion_scores["confusion"]
        if "delight" in emotion_scores:
            self.delight_score = emotion_scores["delight"]

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "id": str(self.id),
            "session_id": str(self.session_id),
            "user_id": str(self.user_id) if self.user_id else None,
            "experiment_id": str(self.experiment_id) if self.experiment_id else None,
            "variant_id": str(self.variant_id) if self.variant_id else None,
            "dominant_emotion": self.dominant_emotion,
            "emotion_timeline": self.emotion_timeline,
            "frustration_score": round(self.frustration_score, 4),
            "confusion_score": round(self.confusion_score, 4),
            "delight_score": round(self.delight_score, 4),
            "converted": self.converted,
            "revenue": self.revenue,
            "churn_risk": self.churn_risk,
            "first_event_at": self.first_event_at.isoformat() if self.first_event_at else None,
            "last_event_at": self.last_event_at.isoformat() if self.last_event_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
