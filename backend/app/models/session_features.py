import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SessionFeatures(Base):
    __tablename__ = "session_features"

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True
    )
    hesitation_score: Mapped[float | None] = mapped_column(Float)
    price_dwell_time_s: Mapped[float | None] = mapped_column(Float)
    rage_click_score: Mapped[float | None] = mapped_column(Float)
    scroll_retreat_count: Mapped[int | None] = mapped_column(Integer)
    exit_intent_count: Mapped[int | None] = mapped_column(Integer)
    checkout_hesitation_s: Mapped[float | None] = mapped_column(Float)
    velocity_variance: Mapped[float | None] = mapped_column(Float)
    session_duration_s: Mapped[float | None] = mapped_column(Float)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
