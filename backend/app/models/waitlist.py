"""Waitlist model — for users interested in paid plans."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class WaitlistEntry(Base):
    __tablename__ = "waitlist"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    plan_interest: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default=text("'growth'")
    )
    current_sessions_monthly: Mapped[int | None] = mapped_column(Integer, nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default=text("'pending'")
    )
    created_at: Mapped[datetime] = mapped_column(
        datetime, nullable=False, server_default=text("now()")
    )
