import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Float, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        CheckConstraint(
            "type IN ('mouse_move','click','scroll','exit_intent','visibility')",
            name="ck_events_type",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    x: Mapped[float | None] = mapped_column(Float)
    y: Mapped[float | None] = mapped_column(Float)
    velocity: Mapped[float | None] = mapped_column(Float)
    element_id: Mapped[str | None] = mapped_column(String(128))
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB)
