"""Experiment model supporting A/B/n, MVT, split URL, multi-page, and server-side tests."""

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from pydantic import ValidationError as PydanticValidationError
from sqlalchemy import (
    JSON,
    Boolean,
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

if TYPE_CHECKING:
    pass


class Experiment(Base):
    """Experiment model for A/B/n, MVT, split URL, multi-page, and server-side experiments.

    Supports flicker-free delivery via async snippet or edge computing.
    """

    __tablename__ = "experiments"
    __table_args__ = (
        CheckConstraint(
            "experiment_type IN ('ab','mvt','split_url','multipage','server_side')",
            name="ck_experiments_type",
        ),
        CheckConstraint(
            "result IN ('a_wins','b_wins','no_diff','inconclusive')",
            name="ck_experiments_result",
        ),
        CheckConstraint(
            "n_variants >= 2 AND n_variants <= 10",
            name="ck_experiments_n_variants",
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

    # ── New fields for full experiment type coverage (CONV-X1) ──

    experiment_type: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        server_default=text("'ab'"),
    )
    n_variants: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("2")
    )
    flicker_free: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    page_urls: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    split_url_config: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    server_side_key: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # ── Timestamps ──

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    # ── Validation methods ──

    def validate_experiment_config(self) -> None:
        """Validate experiment configuration based on experiment_type.

        Raises:
            PydanticValidationError: If configuration is invalid for the experiment type.
        """
        errors: list[str] = []

        # Validate n_variants
        if not (2 <= self.n_variants <= 10):
            errors.append("n_variants must be between 2 and 10")

        # Type-specific validation
        if self.experiment_type == "split_url":
            if not self.split_url_config:
                errors.append("split_url type requires split_url_config")
            else:
                required_keys = {"control_url", "variant_urls"}
                provided_keys = set(self.split_url_config.keys()) if isinstance(self.split_url_config, dict) else set()
                if not required_keys.issubset(provided_keys):
                    missing = required_keys - provided_keys
                    errors.append(f"split_url_config missing keys: {missing}")

                # Validate variant_urls is a non-empty list
                if "variant_urls" in self.split_url_config:
                    variant_urls = self.split_url_config["variant_urls"]
                    if not isinstance(variant_urls, list) or len(variant_urls) == 0:
                        errors.append("split_url_config.variant_urls must be a non-empty list")

        elif self.experiment_type == "multipage":
            if not self.page_urls:
                errors.append("multipage type requires page_urls")
            elif isinstance(self.page_urls, list) and len(self.page_urls) == 0:
                errors.append("page_urls cannot be empty for multipage experiments")

        elif self.experiment_type == "server_side":
            if not self.server_side_key:
                errors.append("server_side type requires server_side_key")

        if errors:
            raise PydanticValidationError.from_exception_data(
                "Experiment", {"_errors": errors}
            )

    def is_flicker_free_enabled(self) -> bool:
        """Check if flicker-free delivery is enabled."""
        return self.flicker_free is True

    def get_variant_count(self) -> int:
        """Get the number of variants for this experiment."""
        return max(2, min(10, self.n_variants))

    def is_multi_page(self) -> bool:
        """Check if this is a multi-page experiment."""
        return self.experiment_type == "multipage"

    def is_server_side(self) -> bool:
        """Check if this is a server-side experiment."""
        return self.experiment_type == "server_side"

    def is_split_url(self) -> bool:
        """Check if this is a split URL experiment."""
        return self.experiment_type == "split_url"

    def is_mvt(self) -> bool:
        """Check if this is a multivariate experiment."""
        return self.experiment_type == "mvt"
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
