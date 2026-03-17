import uuid
from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Experiment(Base):
    __tablename__ = "experiments"
    __table_args__ = (
        CheckConstraint(
            "result IN ('a_wins','b_wins','no_diff','inconclusive')",
            name="ck_experiments_result",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    merchant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    hypothesis: Mapped[str | None] = mapped_column(Text)
    page_element: Mapped[str | None] = mapped_column(String(128))
    friction_type: Mapped[str | None] = mapped_column(String(64))
    variant_a: Mapped[str | None] = mapped_column(Text)
    variant_b: Mapped[str | None] = mapped_column(Text)
    result: Mapped[str | None] = mapped_column(String(16))
    conversion_delta: Mapped[float | None] = mapped_column(Float)
    sample_size: Mapped[int | None] = mapped_column(Integer)
    ran_at: Mapped[date | None] = mapped_column(Date)
    # embedding VECTOR(384) added via raw SQL in migration (pgvector)
    source: Mapped[str | None] = mapped_column(String(32), server_default="manual")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
