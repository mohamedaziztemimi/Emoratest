"""Pydantic schemas for Multi-Armed Bandit CRUD and operations."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

# ── Enums & Literals ──────────────────────────────────────────────

BanditAlgorithm = Literal["thompson_sampling", "ucb1", "epsilon_greedy"]
BanditStatus = Literal["active", "paused", "completed"]


# ── Variant Schema ────────────────────────────────────────────────

class BanditVariant(BaseModel):
    """A single variant (arm) in a bandit experiment."""

    name: str = Field(..., min_length=1, max_length=255)
    variant_id: str = Field(..., min_length=1, max_length=255)
    successes: int = Field(default=0, ge=0)
    trials: int = Field(default=0, ge=0)

    @property
    def conversion_rate(self) -> float:
        """Calculate conversion rate."""
        if self.trials == 0:
            return 0.0
        return self.successes / self.trials


class BanditArmState(BaseModel):
    """State of a single arm for algorithm calculations."""

    arm_id: str
    variant_id: str
    successes: int = 0
    trials: int = 0
    alpha: float = 1.0
    beta: float = 1.0


# ── Request Schemas ───────────────────────────────────────────────

class BanditCreateRequest(BaseModel):
    """Request to create a new bandit experiment."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=2000)
    algorithm: BanditAlgorithm = Field(default="thompson_sampling")
    epsilon: float = Field(default=0.1, ge=0.0, le=1.0)
    exploration_factor: float = Field(default=2.0, ge=0.0)
    min_samples_per_arm: int = Field(default=100, ge=0)
    variants: list[BanditVariant] = Field(..., min_length=2, max_length=10)

    @field_validator("variants")
    @classmethod
    def validate_variants(cls, v: list[BanditVariant]) -> list[BanditVariant]:
        """Ensure variants have unique IDs."""
        variant_ids = [variant.variant_id for variant in v]
        if len(variant_ids) != len(set(variant_ids)):
            raise ValueError("Variant IDs must be unique")
        return v


class BanditUpdateRequest(BaseModel):
    """Request to update a bandit experiment."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=2000)
    status: BanditStatus | None = None
    epsilon: float | None = Field(None, ge=0.0, le=1.0)
    exploration_factor: float | None = Field(None, ge=0.0)
    min_samples_per_arm: int | None = Field(None, ge=0)


class BanditRecordOutcomeRequest(BaseModel):
    """Record a conversion outcome for a bandit arm."""

    variant_id: str = Field(..., min_length=1)
    reward: float = Field(..., ge=0.0, le=1.0)


class BanditSelectArmRequest(BaseModel):
    """Request to select an arm using the bandit algorithm."""

    user_context: dict | None = None


# ── Response Schemas ──────────────────────────────────────────────

class BanditVariantOut(BaseModel):
    """Variant output with computed statistics."""

    name: str
    variant_id: str
    successes: int
    trials: int
    conversion_rate: float
    allocation_percentage: float = 0.0


class BanditOut(BaseModel):
    """Bandit experiment output."""

    id: str
    merchant_id: str
    name: str
    description: str | None = None
    algorithm: BanditAlgorithm
    epsilon: float
    exploration_factor: float
    min_samples_per_arm: int
    variants: list[BanditVariantOut]
    status: BanditStatus
    total_trials: int
    converged: bool
    winner_variant_id: str | None = None
    created_by: str | None = None
    created_at: datetime
    updated_at: datetime


class BanditListResponse(BaseModel):
    """Paginated list of bandit experiments."""

    bandits: list[BanditOut]
    total: int
    page: int
    page_size: int


class BanditArmSelectResponse(BaseModel):
    """Response from arm selection."""

    bandit_id: str
    selected_variant_id: str
    selected_arm_id: str
    algorithm: BanditAlgorithm
    reason: str


class BanditConvergenceResponse(BaseModel):
    """Convergence check response."""

    bandit_id: str
    converged: bool
    winner: str | None = None
    confidence: float = 0.0
    total_trials: int
    recommendation: str = "continue_sampling"


class BanditAllocationResponse(BaseModel):
    """Current traffic allocation percentages."""

    bandit_id: str
    allocations: dict[str, float]  # variant_id -> percentage
    total_trials: int
