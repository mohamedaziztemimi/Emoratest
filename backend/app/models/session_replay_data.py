"""SessionReplayData model for rrweb-based session replay."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SessionReplayData(Base):
    """Stores rrweb DOM recording events for session replay visualization."""

    __tablename__ = "session_replay_data"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # One replay record per session
    )

    # rrweb events array (DOM recording data)
    rrweb_events: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)

    # Recording metadata
    events_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    compressed_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    recording_duration_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Page metadata
    page_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamp when this record was created
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()"
    )
