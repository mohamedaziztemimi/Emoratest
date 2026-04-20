"""Multi-Armed Bandit API - CRUD, arm selection, and optimization.

Endpoints for creating bandit experiments, selecting arms using
Thompson Sampling/UCB1/ε-greedy, recording outcomes, and checking convergence.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.core.auth import get_merchant_flexible
from app.core.database import get_db
from app.core.rate_limit import limiter
from app.models.bandit import Bandit, BanditStatus
from app.models.merchant import Merchant
from app.schemas.bandit import (
    BanditAllocationResponse,
    BanditArmSelectResponse,
    BanditConvergenceResponse,
    BanditCreateRequest,
    BanditListResponse,
    BanditOut,
    BanditRecordOutcomeRequest,
    BanditSelectArmRequest,
    BanditUpdateRequest,
    BanditVariantOut,
)
from app.services.bandit_service import (
    BanditAlgorithm,
    BanditArm,
    BanditService,
    BanditState,
)

router = APIRouter(prefix="/bandits", tags=["bandits"])
bandit_service = BanditService()


# ── Helper Functions ────────────────────────────────────────────────

def _bandit_to_out(bandit: Bandit) -> BanditOut:
    """Convert Bandit model to BanditOut schema."""
    # Convert variants to output format with computed stats
    variants_out: list[BanditVariantOut] = []

    if bandit.variants:
        total_trials = bandit.total_trials or 0

        for v in bandit.variants:
            successes = v.get("successes", 0)
            trials = v.get("trials", 0)
            conversion_rate = successes / trials if trials > 0 else 0.0
            allocation = (trials / total_trials * 100) if total_trials > 0 else (100.0 / len(bandit.variants))

            variants_out.append(
                BanditVariantOut(
                    name=v.get("name", ""),
                    variant_id=v.get("variant_id", ""),
                    successes=successes,
                    trials=trials,
                    conversion_rate=conversion_rate,
                    allocation_percentage=allocation,
                )
            )

    return BanditOut(
        id=str(bandit.id),
        merchant_id=str(bandit.merchant_id),
        name=bandit.name,
        description=bandit.description,
        algorithm=bandit.algorithm,
        epsilon=bandit.epsilon,
        exploration_factor=bandit.exploration_factor,
        min_samples_per_arm=bandit.min_samples_per_arm,
        variants=variants_out,
        status=bandit.status,
        total_trials=bandit.total_trials,
        converged=bandit.converged,
        winner_variant_id=bandit.winner_variant_id,
        created_by=bandit.created_by,
        created_at=bandit.created_at,
        updated_at=bandit.updated_at,
    )


def _bandit_to_state(bandit: Bandit) -> BanditState:
    """Convert Bandit model to BanditState for service layer."""
    arms: list[BanditArm] = []

    if bandit.arm_state:
        for arm_data in bandit.arm_state:
            arms.append(
                BanditArm(
                    arm_id=arm_data.get("arm_id", ""),
                    variant_id=arm_data.get("variant_id", ""),
                    successes=arm_data.get("successes", 0),
                    trials=arm_data.get("trials", 0),
                    alpha=arm_data.get("alpha", 1.0),
                    beta=arm_data.get("beta", 1.0),
                )
            )
    elif bandit.variants:
        # Initialize arms from variants
        for i, v in enumerate(bandit.variants):
            arms.append(
                BanditArm(
                    arm_id=f"arm_{i}",
                    variant_id=v.get("variant_id", ""),
                    successes=v.get("successes", 0),
                    trials=v.get("trials", 0),
                    alpha=1.0 + v.get("successes", 0),
                    beta=1.0 + v.get("trials", 0) - v.get("successes", 0),
                )
            )

    return BanditState(
        experiment_id=str(bandit.id),
        algorithm=BanditAlgorithm(bandit.algorithm),
        arms=arms,
        epsilon=bandit.epsilon,
        exploration_factor=bandit.exploration_factor,
        min_samples_per_arm=bandit.min_samples_per_arm,
        created_at=bandit.created_at,
        updated_at=bandit.updated_at,
    )


def _sync_state_to_bandit(bandit: Bandit, state: BanditState) -> None:
    """Sync BanditState back to Bandit model."""
    # Update arm_state
    bandit.arm_state = [arm.to_dict() for arm in state.arms]

    # Update variants with latest stats
    if bandit.variants:
        variant_map = {v.get("variant_id"): i for i, v in enumerate(bandit.variants)}

        for arm in state.arms:
            if arm.variant_id in variant_map:
                idx = variant_map[arm.variant_id]
                bandit.variants[idx]["successes"] = arm.successes
                bandit.variants[idx]["trials"] = arm.trials

    bandit.total_trials = state.total_trials
    bandit.updated_at = datetime.now(UTC)


# ── LIST BANDITS ────────────────────────────────────────────────────


@router.get("", response_model=BanditListResponse, summary="List all bandit experiments")
@limiter.limit("200/minute")
async def list_bandits(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    status_filter: str | None = Query(None, description="Filter by status"),
    db: Any = Depends(get_db),
    merchant: Merchant = Depends(get_merchant_flexible),
):
    """List all multi-armed bandit experiments with pagination.

    Optionally filter by status (active, paused, completed).
    """
    from sqlalchemy import func, select
    from sqlalchemy.ext.asyncio import AsyncSession

    async_db: AsyncSession = db
    query = select(Bandit).where(Bandit.merchant_id == merchant.id)

    if status_filter:
        if status_filter not in ("active", "paused", "completed"):
            raise HTTPException(
                status_code=400, detail=f"Invalid status filter: {status_filter}"
            )
        query = query.where(Bandit.status == status_filter)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await async_db.execute(count_query)
    total = total_result.scalar() or 0

    # Get paginated results
    query = query.order_by(Bandit.created_at.desc()).limit(page_size).offset(
        (page - 1) * page_size
    )
    result = await async_db.execute(query)
    bandits = result.scalars().all()

    return BanditListResponse(
        bandits=[_bandit_to_out(bandit) for bandit in bandits],
        total=total,
        page=page,
        page_size=page_size,
    )


# ── CREATE BANDIT ───────────────────────────────────────────────────


@router.post(
    "",
    response_model=BanditOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new bandit experiment",
)
@limiter.limit("100/minute")
async def create_bandit(
    request: Request,
    body: BanditCreateRequest,
    db: Any = Depends(get_db),
    merchant: Merchant = Depends(get_merchant_flexible),
):
    """Create a new multi-armed bandit experiment.

    Supports Thompson Sampling, UCB1, and ε-greedy algorithms
    for automatic variant optimization.
    """
    from sqlalchemy.ext.asyncio import AsyncSession

    async_db: AsyncSession = db

    # Convert variants to dict format
    variants_dict = [
        {
            "name": v.name,
            "variant_id": v.variant_id,
            "successes": v.successes,
            "trials": v.trials,
        }
        for v in body.variants
    ]

    # Create bandit
    bandit = Bandit(
        merchant_id=merchant.id,
        name=body.name,
        description=body.description,
        algorithm=body.algorithm,
        epsilon=body.epsilon,
        exploration_factor=body.exploration_factor,
        min_samples_per_arm=body.min_samples_per_arm,
        variants=variants_dict,
        status="active",
    )

    # Initialize arm_state using bandit service
    state = bandit_service.create_bandit(
        experiment_id=str(bandit.id),
        variant_ids=[v.variant_id for v in body.variants],
        algorithm=BanditAlgorithm(body.algorithm),
        epsilon=body.epsilon,
        exploration_factor=body.exploration_factor,
        min_samples_per_arm=body.min_samples_per_arm,
    )
    bandit.arm_state = [arm.to_dict() for arm in state.arms]

    async_db.add(bandit)
    await async_db.commit()
    await async_db.refresh(bandit)

    return _bandit_to_out(bandit)


# ── GET BANDIT ─────────────────────────────────────────────────────


@router.get("/{bandit_id}", response_model=BanditOut, summary="Get bandit details")
@limiter.limit("200/minute")
async def get_bandit(
    request: Request,
    bandit_id: str,
    db: Any = Depends(get_db),
    merchant: Merchant = Depends(get_merchant_flexible),
):
    """Get detailed information about a specific bandit experiment."""
    from sqlalchemy import and_, select
    from sqlalchemy.ext.asyncio import AsyncSession

    async_db: AsyncSession = db

    import uuid

    try:
        bandit_uuid = uuid.UUID(bandit_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid bandit ID format") from exc

    result = await async_db.execute(
        select(Bandit).where(
            and_(Bandit.merchant_id == merchant.id, Bandit.id == bandit_uuid)
        )
    )
    bandit = result.scalar_one_or_none()

    if not bandit:
        raise HTTPException(status_code=404, detail=f"Bandit '{bandit_id}' not found")

    return _bandit_to_out(bandit)


# ── UPDATE BANDIT ─────────────────────────────────────────────────


@router.patch(
    "/{bandit_id}",
    response_model=BanditOut,
    summary="Update a bandit experiment",
)
@limiter.limit("100/minute")
async def update_bandit(
    request: Request,
    bandit_id: str,
    body: BanditUpdateRequest,
    db: Any = Depends(get_db),
    merchant: Merchant = Depends(get_merchant_flexible),
):
    """Update a bandit experiment.

    Partial update - only provided fields are modified.
    """
    from sqlalchemy import and_, select
    from sqlalchemy.ext.asyncio import AsyncSession

    async_db: AsyncSession = db

    import uuid

    try:
        bandit_uuid = uuid.UUID(bandit_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid bandit ID format") from exc

    result = await async_db.execute(
        select(Bandit).where(
            and_(Bandit.merchant_id == merchant.id, Bandit.id == bandit_uuid)
        )
    )
    bandit = result.scalar_one_or_none()

    if not bandit:
        raise HTTPException(status_code=404, detail=f"Bandit '{bandit_id}' not found")

    # Update provided fields
    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(bandit, field):
            setattr(bandit, field, value)

    bandit.updated_at = datetime.now(UTC)

    await async_db.commit()
    await async_db.refresh(bandit)

    return _bandit_to_out(bandit)


# ── DELETE BANDIT ─────────────────────────────────────────────────


@router.delete(
    "/{bandit_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a bandit experiment",
)
@limiter.limit("100/minute")
async def delete_bandit(
    request: Request,
    bandit_id: str,
    db: Any = Depends(get_db),
    merchant: Merchant = Depends(get_merchant_flexible),
):
    """Delete a bandit experiment permanently."""
    from sqlalchemy import and_, select
    from sqlalchemy.ext.asyncio import AsyncSession

    async_db: AsyncSession = db

    import uuid

    try:
        bandit_uuid = uuid.UUID(bandit_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid bandit ID format") from exc

    result = await async_db.execute(
        select(Bandit).where(
            and_(Bandit.merchant_id == merchant.id, Bandit.id == bandit_uuid)
        )
    )
    bandit = result.scalar_one_or_none()

    if not bandit:
        raise HTTPException(status_code=404, detail=f"Bandit '{bandit_id}' not found")

    await async_db.delete(bandit)
    await async_db.commit()


# ── SELECT ARM ────────────────────────────────────────────────────


@router.post(
    "/{bandit_id}/select",
    response_model=BanditArmSelectResponse,
    summary="Select an arm using the bandit algorithm",
)
@limiter.limit("1000/minute")
async def select_arm(
    request: Request,
    bandit_id: str,
    body: BanditSelectArmRequest | None = None,
    db: Any = Depends(get_db),
    merchant: Merchant = Depends(get_merchant_flexible),
):
    """Select an arm (variant) using the configured bandit algorithm.

    Returns the selected variant_id based on:
    - Thompson Sampling: samples from Beta posteriors
    - UCB1: optimistic upper confidence bound
    - ε-greedy: explores with probability epsilon
    """
    from sqlalchemy import and_, select
    from sqlalchemy.ext.asyncio import AsyncSession

    async_db: AsyncSession = db

    import uuid

    try:
        bandit_uuid = uuid.UUID(bandit_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid bandit ID format") from exc

    result = await async_db.execute(
        select(Bandit).where(
            and_(Bandit.merchant_id == merchant.id, Bandit.id == bandit_uuid)
        )
    )
    bandit = result.scalar_one_or_none()

    if not bandit:
        raise HTTPException(status_code=404, detail=f"Bandit '{bandit_id}' not found")

    if bandit.status != BanditStatus.ACTIVE:
        raise HTTPException(
            status_code=400, detail=f"Bandit is not active (current status: {bandit.status})"
        )

    # Get current state
    state = _bandit_to_state(bandit)

    # Select arm
    selected_variant_id = bandit_service.select_arm(state)

    # Find the arm_id for response
    selected_arm = None
    for arm in state.arms:
        if arm.variant_id == selected_variant_id:
            selected_arm = arm
            break

    return BanditArmSelectResponse(
        bandit_id=bandit_id,
        selected_variant_id=selected_variant_id,
        selected_arm_id=selected_arm.arm_id if selected_arm else "",
        algorithm=bandit.algorithm,
        reason="arm_selected_via_" + bandit.algorithm,
    )


# ── RECORD OUTCOME ────────────────────────────────────────────────


@router.post(
    "/{bandit_id}/record",
    response_model=BanditOut,
    summary="Record a conversion outcome",
)
@limiter.limit("1000/minute")
async def record_outcome(
    request: Request,
    bandit_id: str,
    body: BanditRecordOutcomeRequest,
    db: Any = Depends(get_db),
    merchant: Merchant = Depends(get_merchant_flexible),
):
    """Record a reward outcome for a selected arm.

    Updates the arm's statistics and influences future selections.
    Reward should be 0.0 (no conversion) or 1.0 (conversion).
    """
    from sqlalchemy import and_, select
    from sqlalchemy.ext.asyncio import AsyncSession

    async_db: AsyncSession = db

    import uuid

    try:
        bandit_uuid = uuid.UUID(bandit_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid bandit ID format") from exc

    result = await async_db.execute(
        select(Bandit).where(
            and_(Bandit.merchant_id == merchant.id, Bandit.id == bandit_uuid)
        )
    )
    bandit = result.scalar_one_or_none()

    if not bandit:
        raise HTTPException(status_code=404, detail=f"Bandit '{bandit_id}' not found")

    # Get current state
    state = _bandit_to_state(bandit)

    # Find the arm
    arm_to_update = None
    for arm in state.arms:
        if arm.variant_id == body.variant_id:
            arm_to_update = arm
            break

    if not arm_to_update:
        raise HTTPException(
            status_code=400, detail=f"Variant '{body.variant_id}' not found in bandit"
        )

    # Record outcome
    updated_state = bandit_service.record_outcome(state, arm_to_update.arm_id, body.reward)

    # Sync back to bandit
    _sync_state_to_bandit(bandit, updated_state)

    await async_db.commit()
    await async_db.refresh(bandit)

    return _bandit_to_out(bandit)


# ── CHECK CONVERGENCE ─────────────────────────────────────────────


@router.get(
    "/{bandit_id}/convergence",
    response_model=BanditConvergenceResponse,
    summary="Check if bandit has converged",
)
@limiter.limit("200/minute")
async def check_convergence(
    request: Request,
    bandit_id: str,
    confidence: float = Query(0.95, ge=0.5, le=0.99, description="Confidence level"),
    min_trials: int = Query(1000, ge=100, description="Minimum trials before checking"),
    db: Any = Depends(get_db),
    merchant: Merchant = Depends(get_merchant_flexible),
):
    """Check if the bandit has converged to a winning variant.

    Uses Bayesian posterior analysis for Thompson Sampling and
    empirical confidence intervals for other algorithms.
    """
    from sqlalchemy import and_, select
    from sqlalchemy.ext.asyncio import AsyncSession

    async_db: AsyncSession = db

    import uuid

    try:
        bandit_uuid = uuid.UUID(bandit_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid bandit ID format") from exc

    result = await async_db.execute(
        select(Bandit).where(
            and_(Bandit.merchant_id == merchant.id, Bandit.id == bandit_uuid)
        )
    )
    bandit = result.scalar_one_or_none()

    if not bandit:
        raise HTTPException(status_code=404, detail=f"Bandit '{bandit_id}' not found")

    # Get current state
    state = _bandit_to_state(bandit)

    # Check convergence
    result = bandit_service.check_convergence(state, confidence=confidence, min_trials=min_trials)

    # Update bandit if converged
    if result.get("converged") and result.get("winner"):
        bandit.converged = True
        bandit.winner_variant_id = result["winner"]
        bandit.status = BanditStatus.COMPLETED
        await async_db.commit()

    return BanditConvergenceResponse(
        bandit_id=bandit_id,
        converged=result.get("converged", False),
        winner=result.get("winner"),
        confidence=result.get("confidence", 0.0),
        total_trials=state.total_trials,
        recommendation=result.get("reason", "continue_sampling"),
    )


# ── GET ALLOCATION ────────────────────────────────────────────────


@router.get(
    "/{bandit_id}/allocation",
    response_model=BanditAllocationResponse,
    summary="Get current traffic allocation percentages",
)
@limiter.limit("200/minute")
async def get_allocation(
    request: Request,
    bandit_id: str,
    db: Any = Depends(get_db),
    merchant: Merchant = Depends(get_merchant_flexible),
):
    """Get the current traffic allocation percentages per variant.

    Shows how traffic has been distributed based on historical performance.
    """
    from sqlalchemy import and_, select
    from sqlalchemy.ext.asyncio import AsyncSession

    async_db: AsyncSession = db

    import uuid

    try:
        bandit_uuid = uuid.UUID(bandit_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid bandit ID format") from exc

    result = await async_db.execute(
        select(Bandit).where(
            and_(Bandit.merchant_id == merchant.id, Bandit.id == bandit_uuid)
        )
    )
    bandit = result.scalar_one_or_none()

    if not bandit:
        raise HTTPException(status_code=404, detail=f"Bandit '{bandit_id}' not found")

    # Get current state
    state = _bandit_to_state(bandit)

    # Get allocation percentages
    allocations = bandit_service.get_allocation_percentages(state)

    return BanditAllocationResponse(
        bandit_id=bandit_id,
        allocations=allocations,
        total_trials=state.total_trials,
    )
