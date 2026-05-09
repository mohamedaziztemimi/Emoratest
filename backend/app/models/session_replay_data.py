"""SessionReplayData model for emotion replay feature."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SessionReplayData(Base):
    """Stores mouse path and page metadata for session replay visualization."""

    __tablename__ = "session_replay_data"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # One replay record per session
    )
    # Mouse path: array of {x, y, timestamp, viewport_width, viewport_height, scroll_x, scroll_y}
    # and page_change events: {type: "page_change", url, timestamp}
    mouse_path: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Page metadata captured at session start
    page_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    page_title: Mapped[str | None] = mapped_column(Text, nullable=True)
    page_width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    device_pixel_ratio: Mapped[float | None] = mapped_column(Integer, nullable=True)

    # Timestamp when this record was created
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()"
    )
