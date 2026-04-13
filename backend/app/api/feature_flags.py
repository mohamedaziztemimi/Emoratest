"""Feature Flags API - CRUD, evaluation, and management.

Endpoints for creating, updating, and evaluating feature flags
with progressive rollouts, kill switches, and targeting rules.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field, field_validator

from app.core.database import get_db
from app.core.rate_limit import limiter
from app.models.feature_flag import FeatureFlag, FeatureFlagStatus
from app.models.merchant import Merchant
from app.schemas.feature_flags import (
    FeatureFlagCreateRequest,
    FeatureFlagUpdateRequest,
    FeatureFlagOut,
    FeatureFlagListResponse,
    FlagEvaluationRequest,
    FlagEvaluationResponse,
    BulkEvaluationRequest,
    BulkEvaluationResponse,
    KillSwitchRequest,
    RolloutUpdateRequest,
    ExposureStatsResponse,
)
from app.services.feature_flag_service import FeatureFlagService, FlagResult
from app.services.sdk_auth import authenticate_sdk_key, get_sdk_key_header

router = APIRouter(prefix="/api/v1/flags", tags=["feature_flags"])
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
    sdk_key_hash: str = Depends(get_sdk_key_header),
):
    """List all feature flags with pagination.

    Optionally filter by status (active, inactive, archived).
    """
    merchant = await authenticate_sdk_key(db, sdk_key_hash)

    # Build query
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession

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
    sdk_key_hash: str = Depends(get_sdk_key_header),
):
    """Create a new feature flag.

    Supports progressive rollouts, targeting rules, multivariate variants,
    and environment-specific configurations.
    """
    merchant = await authenticate_sdk_key(db, sdk_key_hash)

    # Check for duplicate key
    from sqlalchemy import select, and_
    from sqlalchemy.ext.asyncio import AsyncSession

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
    flag = FeatureFlag(
        merchant_id=merchant.id,
        key=body.key,
        name=body.name,
        description=body.description,
        status=body.status or ("active" if body.rollout_percentage > 0 else "inactive"),
        rollout_percentage=body.rollout_percentage,
        targeting_rules=body.targeting_rules,
        variants=body.variants,
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
    sdk_key_hash: str = Depends(get_sdk_key_header),
):
    """Get detailed information about a specific feature flag."""
    merchant = await authenticate_sdk_key(db, sdk_key_hash)

    from sqlalchemy import select, and_
    from sqlalchemy.ext.asyncio import AsyncSession

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
    sdk_key_hash: str = Depends(get_sdk_key_header),
):
    """Update a feature flag.

    Partial update - only provided fields are modified.
    """
    merchant = await authenticate_sdk_key(db, sdk_key_hash)

    from sqlalchemy import select, and_
    from sqlalchemy.ext.asyncio import AsyncSession

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
    sdk_key_hash: str = Depends(get_sdk_key_header),
):
    """Evaluate a feature flag for a specific user context.

    Returns whether the flag is enabled, which variant (if any),
    and the reason for the decision.
    """
    merchant = await authenticate_sdk_key(db, sdk_key_hash)

    from sqlalchemy import select, and_
    from sqlalchemy.ext.asyncio import AsyncSession

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
    sdk_key_hash: str = Depends(get_sdk_key_header),
):
    """Evaluate all feature flags for a user context.

    Returns a dictionary of flag_key to evaluation results.
    """
    merchant = await authenticate_sdk_key(db, sdk_key_hash)

    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession

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
    sdk_key_hash: str = Depends(get_sdk_key_header),
):
    """Toggle the kill switch for a feature flag.

    When enabled, the flag always returns False regardless of
    rollout percentage or targeting rules.
    """
    merchant = await authenticate_sdk_key(db, sdk_key_hash)

    from sqlalchemy import select, and_
    from sqlalchemy.ext.asyncio import AsyncSession

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
    sdk_key_hash: str = Depends(get_sdk_key_header),
):
    """Update the rollout percentage for a feature flag.

    Percentage is clamped to 0-100 range.
    """
    merchant = await authenticate_sdk_key(db, sdk_key_hash)

    from sqlalchemy import select, and_
    from sqlalchemy.ext.asyncio import AsyncSession

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
    sdk_key_hash: str = Depends(get_sdk_key_header),
):
    """Get exposure statistics for a feature flag.

    Returns percentage of users exposed, variant breakdown,
    and total unique users.
    """
    merchant = await authenticate_sdk_key(db, sdk_key_hash)

    from sqlalchemy import select, and_
    from sqlalchemy.ext.asyncio import AsyncSession

    async_db: AsyncSession = db
    result = await async_db.execute(
        select(FeatureFlag).where(
            and_(FeatureFlag.merchant_id == merchant.id, FeatureFlag.key == key)
        )
    )
    flag = result.scalar_one_or_none()

    if not flag:
        raise HTTPException(status_code=404, detail=f"Feature flag '{key}' not found")

    # TODO: Implement exposure tracking in separate table
    # For now, return mock data structure
    return ExposureStatsResponse(
        flag_key=key,
        days=days,
        total_users=0,
        exposed_users=0,
        exposure_percentage=0.0,
        variant_breakdown={},
    )


# ── ARCHIVE FLAG ──────────────────────────────────────────────────────


@router.post("/{key}/archive", status_code=status.HTTP_204_NO_CONTENT, summary="Archive a flag")
@limiter.limit("100/minute")
async def archive_flag(
    request: Request,
    key: str,
    db: Any = Depends(get_db),
    sdk_key_hash: str = Depends(get_sdk_key_header),
):
    """Archive a feature flag.

    Archived flags are read-only and no longer evaluated.
    """
    merchant = await authenticate_sdk_key(db, sdk_key_hash)

    from sqlalchemy import select, and_
    from sqlalchemy.ext.asyncio import AsyncSession

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
