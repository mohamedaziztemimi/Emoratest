"""Integration model for outbound webhooks and third-party connections.

Supports:
- Alert integrations (Slack, Jira) for experiment results and emotion spikes
- Analytics integrations (Amplitude, PostHog) for experiment tracking
- Data warehouse integrations (Snowflake, BigQuery) for data sync
- Generic webhooks and Zapier for custom integrations
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
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


class IntegrationType(str, Enum):
    """Types of supported integrations."""

    SLACK = "slack"
    JIRA = "jira"
    AMPLITUDE = "amplitude"
    POSTHOG = "posthog"
    SNOWFLAKE = "snowflake"
    BIGQUERY = "bigquery"
    WEBHOOK = "webhook"
    ZAPIER = "zapier"


class EventType(str, Enum):
    """Event types that can trigger integrations."""

    EXPERIMENT_WINNER = "experiment.winner"
    EXPERIMENT_STARTED = "experiment.started"
    EXPERIMENT_STOPPED = "experiment.stopped"
    TEST_STARTED = "test.started"
    TEST_STOPPED = "test.stopped"
    EMOTION_FRUSTRATION_SPIKE = "emotion.frustration_spike"
    ANOMALY_DETECTED = "anomaly.detected"
    SESSION_ENDED = "session.ended"
    USER_CHURN_RISK = "user.churn_risk"


class Integration(Base):
    """Third-party integration configuration."""

    __tablename__ = "integrations"

    # ── Primary Fields ──────────────────────────────────────

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # ── Type & Config ─────────────────────────────────────

    integration_type: Mapped[str] = mapped_column(
        String(32), nullable=False
    )
    config: Mapped[dict] = mapped_column(
        JSON, nullable=False, comment="Encrypted at rest in production"
    )

    # ── Event Subscription ───────────────────────────────────

    events: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, default=list
    )

    # ── Status & Health ────────────────────────────────────

    enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    last_triggered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    failure_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )

    # ── Timestamps ───────────────────────────────────────

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    # ── Helper Methods ─────────────────────────────────────

    def is_alert_integration(self) -> bool:
        """Check if this is an alerting integration."""
        return self.integration_type in {
            IntegrationType.SLACK,
            IntegrationType.JIRA,
        }

    def is_analytics_integration(self) -> bool:
        """Check if this is an analytics integration."""
        return self.integration_type in {
            IntegrationType.AMPLITUDE,
            IntegrationType.POSTHOG,
        }

    def is_warehouse_integration(self) -> bool:
        """Check if this is a data warehouse integration."""
        return self.integration_type in {
            IntegrationType.SNOWFLAKE,
            IntegrationType.BIGQUERY,
        }

    def is_webhook_integration(self) -> bool:
        """Check if this is a generic webhook."""
        return self.integration_type == IntegrationType.WEBHOOK

    def subscribes_to(self, event_type: str) -> bool:
        """Check if integration subscribes to an event type."""
        return event_type in self.events

    def increment_failure(self) -> bool:
        """Increment failure count and check if should auto-disable."""
        self.failure_count += 1
        self.last_triggered_at = datetime.now(UTC)
        return self.failure_count >= 5

    def reset_failure_count(self) -> None:
        """Reset failure count after successful trigger."""
        self.failure_count = 0

    def to_dict(self) -> dict:
        """Serialize to dictionary (without sensitive config)."""
        return {
            "id": str(self.id),
            "workspace_id": str(self.workspace_id),
            "name": self.name,
            "integration_type": self.integration_type,
            "events": self.events,
            "enabled": self.enabled,
            "last_triggered_at": (
                self.last_triggered_at.isoformat() if self.last_triggered_at else None
            ),
            "failure_count": self.failure_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "config": {
                "webhook_url": self.config.get("webhook_url") if self.config else None,
                # Return only safe config fields
            },
        }


class WebhookLog(Base):
    """Log of webhook dispatch attempts and responses."""

    __tablename__ = "webhook_logs"

    # ── Primary Fields ──────────────────────────────────────

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    integration_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("integrations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)

    # ── Request/Response ─────────────────────────────────

    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    response_status: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="HTTP status code"
    )
    response_body: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    duration_ms: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )

    # ── Timestamp ─────────────────────────────────────────

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    # ── Helper Methods ─────────────────────────────────────

    def was_successful(self) -> bool:
        """Check if webhook dispatch was successful."""
        return 200 <= self.response_status < 300

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "id": str(self.id),
            "integration_id": str(self.integration_id),
            "event_type": self.event_type,
            "response_status": self.response_status,
            "duration_ms": self.duration_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "payload": self.payload,
        }
