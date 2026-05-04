import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Merchant(Base):
    __tablename__ = "merchants"
    __table_args__ = (
        CheckConstraint(
            "plan IN ('free','growth','scale','enterprise')",
            name="ck_merchants_plan",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    shop_domain: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    sdk_key_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    test_sdk_key_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, server_default=text("'test_' || gen_random_uuid()::text"))
    plan: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default=text("'free'")
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    gdpr_consent: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    gdpr_consent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    onboarding_completed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    # Session limit fields
    monthly_session_limit: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("500")
    )
    sessions_this_month: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    session_month: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("EXTRACT(MONTH FROM NOW())")
    )
    session_year: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("EXTRACT(YEAR FROM NOW())")
    )
    # Password reset fields
    password_reset_token: Mapped[str | None] = mapped_column(
        String(255), nullable=True, unique=True
    )
    password_reset_expires: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Email verification fields
    email_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    email_verification_token: Mapped[str | None] = mapped_column(
        String(255), nullable=True, unique=True
    )
    email_verification_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Micro-survey configuration
    survey_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    survey_trigger: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default=text("'exit_intent'")
    )
    survey_sample_rate: Mapped[float] = mapped_column(
        Float, nullable=False, server_default=text("0.1")
    )
    survey_pages: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    __table_args__ = (
        CheckConstraint(
            "plan IN ('free','growth','scale','enterprise')",
            name="ck_merchants_plan",
        ),
        Index("ix_merchants_password_reset_token", "password_reset_token"),
        Index("ix_merchants_email_verification_token", "email_verification_token"),
    )
