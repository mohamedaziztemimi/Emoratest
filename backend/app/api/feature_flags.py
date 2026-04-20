"""Feature Flags API - CRUD, evaluation, and management.

Endpoints for creating, updating, and evaluating feature flags
with progressive rollouts, kill switches, and targeting rules.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import case
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.sdk import get_merchant_from_sdk_key
from app.core.auth import get_merchant_flexible
from app.core.database import get_db
from app.core.rate_limit import limiter
from app.models.feature_flag import FeatureFlag, FeatureFlagStatus
from app.models.flag_exposure import FlagExposure
from app.models.merchant import Merchant
from app.models.session import Session as SessionModel
from app.schemas.feature_flags import (
    BulkEvaluationRequest,
    BulkEvaluationResponse,
    ExposureStatsResponse,
    FeatureFlagCreateRequest,
    FeatureFlagListResponse,
    FeatureFlagOut,
    FeatureFlagUpdateRequest,
    FlagEvaluationRequest,
    FlagEvaluationResponse,
    FlagResultsResponse,
    KillSwitchRequest,
    RolloutUpdateRequest,
    VariantResult,
)
from app.services.feature_flag_service import FeatureFlagService

router = APIRouter(prefix="/flags", tags=["feature_flags"])
service = FeatureFlagService()


# ── LIST FLAGS ────────────────────────────────────────────────────────


@router.get("", response_model=FeatureFlagListResponse, summary="List all feature flags")
@limiter.limit("200/minute")
async def list_flags(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    status_filter: str | None = Query(None, description="Filter by status"),
    db: Any = Depends(get_db),
    merchant: Merchant = Depends(get_merchant_flexible),
):
    """List all feature flags with pagination.

    Optionally filter by status (active, inactive, archived).
    """

    # Build query
    from sqlalchemy import select

    async_db: AsyncSession = db
    query = select(FeatureFlag).where(FeatureFlag.merchant_id == merchant.id)

    if status_filter:
        if status_filter not in ("active", "inactive", "archived"):
            raise HTTPException(
                status_code=400, detail=f"Invalid status filter: {status_filter}"
            )
        query = query.where(FeatureFlag.status == status_filter)

    # Get total count
    from sqlalchemy import func
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await async_db.execute(count_query)
    total = total_result.scalar() or 0

    # Get paginated results
    query = query.order_by(FeatureFlag.created_at.desc()).limit(page_size).offset(
        (page - 1) * page_size
    )
    result = await async_db.execute(query)
    flags = result.scalars().all()

    return FeatureFlagListResponse(
        flags=[FeatureFlagOut.model_validate(flag.to_dict()) for flag in flags],
        total=total,
        page=page,
        page_size=page_size,
    )


# ── CREATE FLAG ────────────────────────────────────────────────────────


@router.post(
    "",
    response_model=FeatureFlagOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new feature flag",
)
@limiter.limit("100/minute")
async def create_flag(
    request: Request,
    body: FeatureFlagCreateRequest,
    db: Any = Depends(get_db),
    merchant: Merchant = Depends(get_merchant_flexible),
):
    """Create a new feature flag.

    Supports progressive rollouts, targeting rules, multivariate variants,
    and environment-specific configurations.
    """

    # Check for duplicate key
    from sqlalchemy import and_, select

    async_db: AsyncSession = db
    existing = await async_db.execute(
        select(FeatureFlag).where(
            and_(
                FeatureFlag.merchant_id == merchant.id,
                FeatureFlag.key == body.key,
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409, detail=f"Feature flag with key '{body.key}' already exists"
        )

    # Create flag
    # Convert Pydantic models to dicts for JSON storage
    variants_dict = [v.model_dump() for v in body.variants] if body.variants else None
    targeting_rules_dict = [r.model_dump() for r in body.targeting_rules] if body.targeting_rules else None

    flag = FeatureFlag(
        merchant_id=merchant.id,
        key=body.key,
        name=body.name,
        description=body.description,
        status=body.status or ("active" if body.rollout_percentage > 0 else "inactive"),
        rollout_percentage=body.rollout_percentage,
        targeting_rules=targeting_rules_dict,
        variants=variants_dict,
        kill_switch=body.kill_switch,
        environments=body.environments,
        created_by=body.created_by,
    )

    async_db.add(flag)
    await async_db.commit()
    await async_db.refresh(flag)

    return FeatureFlagOut.model_validate(flag.to_dict())


# ── GET FLAG ───────────────────────────────────────────────────────────


@router.get("/{key}", response_model=FeatureFlagOut, summary="Get feature flag details")
@limiter.limit("200/minute")
async def get_flag(
    request: Request,
    key: str,
    db: Any = Depends(get_db),
    merchant: Merchant = Depends(get_merchant_flexible),
):
    """Get detailed information about a specific feature flag."""

    from sqlalchemy import and_, select

    async_db: AsyncSession = db
    result = await async_db.execute(
        select(FeatureFlag).where(
            and_(FeatureFlag.merchant_id == merchant.id, FeatureFlag.key == key)
        )
    )
    flag = result.scalar_one_or_none()

    if not flag:
        raise HTTPException(status_code=404, detail=f"Feature flag '{key}' not found")

    return FeatureFlagOut.model_validate(flag.to_dict())


# ── UPDATE FLAG ───────────────────────────────────────────────────────


@router.patch(
    "/{key}",
    response_model=FeatureFlagOut,
    summary="Update a feature flag",
)
@limiter.limit("100/minute")
async def update_flag(
    request: Request,
    key: str,
    body: FeatureFlagUpdateRequest,
    db: Any = Depends(get_db),
    merchant: Merchant = Depends(get_merchant_flexible),
):
    """Update a feature flag.

    Partial update - only provided fields are modified.
    """

    from sqlalchemy import and_, select

    async_db: AsyncSession = db
    result = await async_db.execute(
        select(FeatureFlag).where(
            and_(FeatureFlag.merchant_id == merchant.id, FeatureFlag.key == key)
        )
    )
    flag = result.scalar_one_or_none()

    if not flag:
        raise HTTPException(status_code=404, detail=f"Feature flag '{key}' not found")

    # Update provided fields
    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(flag, field):
            setattr(flag, field, value)

    flag.updated_at = datetime.now(UTC)

    await async_db.commit()
    await async_db.refresh(flag)

    return FeatureFlagOut.model_validate(flag.to_dict())


# ── EVALUATE FLAG ───────────────────────────────────────────────────


@router.post(
    "/{key}/evaluate",
    response_model=FlagEvaluationResponse,
    summary="Evaluate feature flag for a user",
)
@limiter.limit("1000/minute")
async def evaluate_flag(
    request: Request,
    key: str,
    body: FlagEvaluationRequest,
    db: Any = Depends(get_db),
    merchant: Merchant = Depends(get_merchant_flexible),
):
    """Evaluate a feature flag for a specific user context.

    Returns whether the flag is enabled, which variant (if any),
    and the reason for the decision.
    """

    from sqlalchemy import and_, select

    async_db: AsyncSession = db
    result = await async_db.execute(
        select(FeatureFlag).where(
            and_(FeatureFlag.merchant_id == merchant.id, FeatureFlag.key == key)
        )
    )
    flag = result.scalar_one_or_none()

    if not flag:
        raise HTTPException(status_code=404, detail=f"Feature flag '{key}' not found")

    # Evaluate flag
    flag_result = service.evaluate(
        flag, body.user_context, body.environment or "production"
    )

    return FlagEvaluationResponse(
        flag_key=key,
        enabled=flag_result.enabled,
        variant=flag_result.variant,
        reason=flag_result.reason,
    )


# ── SDK EVALUATE (SDK key auth) ──────────────────────────────────────


@router.post(
    "/sdk/{key}/evaluate",
    response_model=FlagEvaluationResponse,
    summary="Evaluate feature flag via SDK (uses X-SDK-Key auth)",
)
@limiter.limit("2000/minute")
async def evaluate_flag_sdk(
    request: Request,
    key: str,
    body: FlagEvaluationRequest,
    db: Any = Depends(get_db),
    merchant: Merchant = Depends(get_merchant_from_sdk_key),
):
    """Evaluate a feature flag for SDK use cases.

    Authenticated via X-SDK-Key header (NOT JWT cookies).
    Returns deterministic variant assignment based on user_id.

    Request body should include:
    - user_context: dict with user_id for deterministic bucketing
    - environment: optional environment name (default "production")
    - session_id: optional session ID for linking exposures to sessions

    Returns:
        enabled: true if flag is enabled for this user
        variant: selected variant key (for multivariate flags)
        reason: explanation of the decision
    """
    from sqlalchemy import and_, select

    async_db: AsyncSession = db
    result = await async_db.execute(
        select(FeatureFlag).where(
            and_(FeatureFlag.merchant_id == merchant.id, FeatureFlag.key == key)
        )
    )
    flag = result.scalar_one_or_none()

    if not flag:
        raise HTTPException(status_code=404, detail=f"Feature flag '{key}' not found")

    visitor_id = body.user_context.get("visitor_id") or body.user_context.get("user_id", "")
    if not visitor_id:
        raise HTTPException(status_code=400, detail="visitor_id or user_id is required in user_context")

    # Check for existing exposure (return same variant for consistency)
    existing_exposure = await async_db.execute(
        select(FlagExposure).where(
            and_(
                FlagExposure.flag_id == flag.id,
                FlagExposure.visitor_id == visitor_id,
            )
        ).order_by(FlagExposure.created_at.desc()).limit(1)
    )
    existing = existing_exposure.scalar_one_or_none()

    if existing:
        # Return cached variant from DB
        return FlagEvaluationResponse(
            flag_key=key,
            enabled=existing.enabled,
            variant=existing.variant,
            reason=existing.reason or "cached_assignment",
        )

    # Build user context for service (service expects user_id, not visitor_id)
    evaluation_context = {**body.user_context, "user_id": visitor_id}

    # Evaluate flag
    flag_result = service.evaluate(
        flag, evaluation_context, body.environment or "production"
    )

    # Record exposure for new assignments
    session_id = body.user_context.get("session_id")
    if session_id:
        try:
            session_id_uuid = session_id if isinstance(session_id, uuid.UUID) else uuid.UUID(session_id)
        except (ValueError, AttributeError):
            session_id_uuid = None
    else:
        session_id_uuid = None

    exposure = FlagExposure(
        flag_id=flag.id,
        visitor_id=visitor_id,
        variant=flag_result.variant,
        session_id=session_id_uuid,
        enabled=flag_result.enabled,
        reason=flag_result.reason,
    )
    async_db.add(exposure)
    await async_db.commit()

    return FlagEvaluationResponse(
        flag_key=key,
        enabled=flag_result.enabled,
        variant=flag_result.variant,
        reason=flag_result.reason,
    )


# ── BULK EVALUATE ────────────────────────────────────────────────────


@router.post(
    "/evaluate-bulk",
    response_model=BulkEvaluationResponse,
    summary="Evaluate all flags for a user",
)
@limiter.limit("500/minute")
async def evaluate_bulk(
    request: Request,
    body: BulkEvaluationRequest,
    db: Any = Depends(get_db),
    merchant: Merchant = Depends(get_merchant_flexible),
):
    """Evaluate all feature flags for a user context.

    Returns a dictionary of flag_key to evaluation results.
    """

    from sqlalchemy import select

    async_db: AsyncSession = db
    result = await async_db.execute(
        select(FeatureFlag).where(FeatureFlag.merchant_id == merchant.id)
    )
    flags = result.scalars().all()

    # Evaluate all flags
    results = service.evaluate_all(
        flags, body.user_context, body.environment or "production"
    )

    return BulkEvaluationResponse(
        flags={
            k: {
                "enabled": v.enabled,
                "variant": v.variant,
                "reason": v.reason,
            }
            for k, v in results.items()
        },
        evaluated_at=datetime.now(UTC).isoformat(),
    )


# ── KILL SWITCH ────────────────────────────────────────────────────────


@router.post(
    "/{key}/kill",
    response_model=FeatureFlagOut,
    summary="Toggle kill switch for a flag",
)
@limiter.limit("100/minute")
async def toggle_kill_switch(
    request: Request,
    key: str,
    body: KillSwitchRequest,
    db: Any = Depends(get_db),
    merchant: Merchant = Depends(get_merchant_flexible),
):
    """Toggle the kill switch for a feature flag.

    When enabled, the flag always returns False regardless of
    rollout percentage or targeting rules.
    """

    from sqlalchemy import and_, select

    async_db: AsyncSession = db
    result = await async_db.execute(
        select(FeatureFlag).where(
            and_(FeatureFlag.merchant_id == merchant.id, FeatureFlag.key == key)
        )
    )
    flag = result.scalar_one_or_none()

    if not flag:
        raise HTTPException(status_code=404, detail=f"Feature flag '{key}' not found")

    flag.kill_switch = body.enabled
    flag.updated_at = datetime.now(UTC)

    await async_db.commit()
    await async_db.refresh(flag)

    return FeatureFlagOut.model_validate(flag.to_dict())


# ── UPDATE ROLLOUT ────────────────────────────────────────────────────


@router.post(
    "/{key}/rollout",
    response_model=FeatureFlagOut,
    summary="Update rollout percentage",
)
@limiter.limit("100/minute")
async def update_rollout(
    request: Request,
    key: str,
    body: RolloutUpdateRequest,
    db: Any = Depends(get_db),
    merchant: Merchant = Depends(get_merchant_flexible),
):
    """Update the rollout percentage for a feature flag.

    Percentage is clamped to 0-100 range.
    """

    from sqlalchemy import and_, select

    async_db: AsyncSession = db
    result = await async_db.execute(
        select(FeatureFlag).where(
            and_(FeatureFlag.merchant_id == merchant.id, FeatureFlag.key == key)
        )
    )
    flag = result.scalar_one_or_none()

    if not flag:
        raise HTTPException(status_code=404, detail=f"Feature flag '{key}' not found")

    flag.rollout_percentage = max(0.0, min(100.0, body.percentage))
    flag.updated_at = datetime.now(UTC)

    await async_db.commit()
    await async_db.refresh(flag)

    return FeatureFlagOut.model_validate(flag.to_dict())


# ── EXPOSURE STATS ─────────────────────────────────────────────────────


@router.get(
    "/{key}/stats",
    response_model=ExposureStatsResponse,
    summary="Get exposure statistics for a flag",
)
@limiter.limit("200/minute")
async def get_exposure_stats(
    request: Request,
    key: str,
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: Any = Depends(get_db),
    merchant: Merchant = Depends(get_merchant_flexible),
):
    """Get exposure statistics for a feature flag.

    Returns percentage of users exposed, variant breakdown,
    and total unique users.
    """

    from sqlalchemy import and_, func, select

    async_db: AsyncSession = db
    result = await async_db.execute(
        select(FeatureFlag).where(
            and_(FeatureFlag.merchant_id == merchant.id, FeatureFlag.key == key)
        )
    )
    flag = result.scalar_one_or_none()

    if not flag:
        raise HTTPException(status_code=404, detail=f"Feature flag '{key}' not found")

    # Get cutoff date
    cutoff = datetime.now(UTC) - timedelta(days=days)

    # Get total unique visitors
    total_result = await async_db.execute(
        select(func.count(func.distinct(FlagExposure.visitor_id))).where(
            and_(
                FlagExposure.flag_id == flag.id,
                FlagExposure.created_at >= cutoff,
            )
        )
    )
    total_users = total_result.scalar() or 0

    # Get exposed users (enabled=true)
    exposed_result = await async_db.execute(
        select(func.count(func.distinct(FlagExposure.visitor_id))).where(
            and_(
                FlagExposure.flag_id == flag.id,
                FlagExposure.created_at >= cutoff,
                FlagExposure.enabled.is_(True),
            )
        )
    )
    exposed_users = exposed_result.scalar() or 0

    # Get variant breakdown
    variant_result = await async_db.execute(
        select(
            FlagExposure.variant,
            func.count(func.distinct(FlagExposure.visitor_id)).label("count"),
        )
        .where(
            and_(
                FlagExposure.flag_id == flag.id,
                FlagExposure.created_at >= cutoff,
                FlagExposure.enabled.is_(True),
            )
        )
        .group_by(FlagExposure.variant)
    )
    variant_rows = variant_result.all()

    variant_breakdown = {
        variant or "default": count for variant, count in variant_rows
    }

    exposure_percentage = (exposed_users / total_users * 100) if total_users > 0 else 0.0

    return ExposureStatsResponse(
        flag_key=key,
        days=days,
        total_users=total_users,
        exposed_users=exposed_users,
        exposure_percentage=round(exposure_percentage, 2),
        variant_breakdown=variant_breakdown,
    )


# ── RESULTS / CONVERSION TRACKING ─────────────────────────────────────


@router.get(
    "/{key}/results",
    response_model=FlagResultsResponse,
    summary="Get conversion results by variant",
)
@limiter.limit("200/minute")
async def get_flag_results(
    request: Request,
    key: str,
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: Any = Depends(get_db),
    merchant: Merchant = Depends(get_merchant_flexible),
):
    """Get conversion statistics for a feature flag by variant.

    Joins exposure data with session outcomes to calculate
    conversion rates per variant.
    """

    from sqlalchemy import and_, func, select

    async_db: AsyncSession = db
    result = await async_db.execute(
        select(FeatureFlag).where(
            and_(FeatureFlag.merchant_id == merchant.id, FeatureFlag.key == key)
        )
    )
    flag = result.scalar_one_or_none()

    if not flag:
        raise HTTPException(status_code=404, detail=f"Feature flag '{key}' not found")

    # Get cutoff date
    cutoff = datetime.now(UTC) - timedelta(days=days)

    # Get exposures with conversions by variant
    # Left join with sessions to get outcomes
    query = (
        select(
            FlagExposure.variant,
            func.count(func.distinct(FlagExposure.visitor_id)).label("exposures"),
            func.count(
                func.distinct(
                    case(
                        (SessionModel.outcome == "purchase", SessionModel.id),
                        else_=None,
                    )
                )
            ).label("conversions"),
        )
        .outerjoin(
            SessionModel,
            and_(
                SessionModel.id == FlagExposure.session_id,
                SessionModel.outcome == "purchase",
            ),
        )
        .where(
            and_(
                FlagExposure.flag_id == flag.id,
                FlagExposure.enabled.is_(True),
                FlagExposure.created_at >= cutoff,
            )
        )
        .group_by(FlagExposure.variant)
    )

    variant_results = await async_db.execute(query)
    rows = variant_results.all()

    variants = []
    total_exposures = 0
    total_conversions = 0
    winning_variant = None
    best_rate = -1.0

    for variant, exposures, conversions in rows:
        variant_key = variant or "default"
        rate = (conversions / exposures * 100) if exposures > 0 else 0.0
        variants.append(
            VariantResult(
                variant=variant_key,
                exposures=exposures,
                conversions=conversions,
                conversion_rate=round(rate, 2),
            )
        )
        total_exposures += exposures
        total_conversions += conversions

        if rate > best_rate and exposures >= 5:  # Minimum 5 exposures to be winner
            best_rate = rate
            winning_variant = variant_key

    overall_rate = (total_conversions / total_exposures * 100) if total_exposures > 0 else 0.0

    return FlagResultsResponse(
        flag_key=key,
        flag_id=str(flag.id),
        days=days,
        variants=variants,
        winning_variant=winning_variant,
        total_exposures=total_exposures,
        total_conversions=total_conversions,
        overall_conversion_rate=round(overall_rate, 2),
    )


# ── ARCHIVE FLAG ──────────────────────────────────────────────────────


@router.post("/{key}/archive", status_code=status.HTTP_204_NO_CONTENT, summary="Archive a flag")
@limiter.limit("100/minute")
async def archive_flag(
    request: Request,
    key: str,
    db: Any = Depends(get_db),
    merchant: Merchant = Depends(get_merchant_flexible),
):
    """Archive a feature flag.

    Archived flags are read-only and no longer evaluated.
    """

    from sqlalchemy import and_, select

    async_db: AsyncSession = db
    result = await async_db.execute(
        select(FeatureFlag).where(
            and_(FeatureFlag.merchant_id == merchant.id, FeatureFlag.key == key)
        )
    )
    flag = result.scalar_one_or_none()

    if not flag:
        raise HTTPException(status_code=404, detail=f"Feature flag '{key}' not found")

    flag.status = FeatureFlagStatus.ARCHIVED
    flag.updated_at = datetime.now(UTC)

    await async_db.commit()
