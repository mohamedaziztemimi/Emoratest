import uuid
from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        CheckConstraint(
            "type IN ('mouse_move','click','scroll','exit_intent','visibility','mouse_summary')",
            name="ck_events_type",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    x: Mapped[float | None] = mapped_column(Float)
    y: Mapped[float | None] = mapped_column(Float)
    velocity: Mapped[float | None] = mapped_column(Float)
    element_id: Mapped[str | None] = mapped_column(String(128))
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB)

    # Semantic event enrichment (business-readable fields)
    label: Mapped[str | None] = mapped_column(String(256), nullable=True)
    element_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    section: Mapped[str | None] = mapped_column(String(64), nullable=True)
    selector: Mapped[str | None] = mapped_column(String(512), nullable=True)


class EventEnriched(Base):
    """UI-friendly event display with human-readable descriptions.

    This table is separate from raw events to ensure ML pipeline is not affected.
    Enriched data is generated after events are stored.
    """
    __tablename__ = "event_enriched"
    __table_args__ = (
        CheckConstraint(
            "type IN ('mouse_move','click','scroll','exit_intent','visibility','mouse_summary')",
            name="ck_event_enriched_type",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    label: Mapped[str | None] = mapped_column(String(256), nullable=True)
    section: Mapped[str | None] = mapped_column(String(64), nullable=True)
    element_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    readable_description: Mapped[str | None] = mapped_column(String(512), nullable=True)
