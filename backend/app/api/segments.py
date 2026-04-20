"""Segments API - CRUD, evaluation, and CRM sync.

Endpoints for creating, updating, and evaluating segments
with flexible condition-based targeting for experiments.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.core.auth import get_merchant_flexible
from app.core.database import get_db
from app.core.rate_limit import limiter
from app.models.merchant import Merchant
from app.models.segment import Segment
from app.schemas.segments import (
    CRMSyncRequest,
    CRMSyncResponse,
    EmotionalCohortRequest,
    EmotionalCohortResponse,
    EmotionProfileOut,
    SampleUser,
    SegmentCreateRequest,
    SegmentEvaluateRequest,
    SegmentEvaluateResponse,
    SegmentListResponse,
    SegmentOut,
    SegmentPreviewResponse,
    SegmentUpdateRequest,
)
from app.services.targeting_service import (
    TargetingService,
)

router = APIRouter(prefix="/segments", tags=["segments"])
service = TargetingService()


# ── LIST SEGMENTS ───────────────────────────────────────────────


@router.get("", response_model=SegmentListResponse, summary="List all segments")
@limiter.limit("200/minute")
async def list_segments(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    type_filter: str | None = Query(None, description="Filter by segment type"),
    db: Any = Depends(get_db),
    merchant: Merchant = Depends(get_merchant_flexible),
):
    """List all segments with pagination.

    Optionally filter by type (static, dynamic, emotional).
    """
    from sqlalchemy import func, select
    from sqlalchemy.ext.asyncio import AsyncSession

    # Note: For SDK access, use authenticate_sdk_key like other endpoints
    # For now, we skip auth for simplicity

    async_db: AsyncSession = db

    # Build query
    # Get all segments (or filter by merchant when auth is added)
    query = select(Segment).where(Segment.merchant_id == merchant.id)

    if type_filter:
        if type_filter not in ("static", "dynamic", "emotional"):
            raise HTTPException(
                status_code=400, detail=f"Invalid type filter: {type_filter}"
            )
        query = query.where(Segment.segment_type == type_filter)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await async_db.execute(count_query)
    total = total_result.scalar() or 0

    # Get paginated results
    query = query.order_by(Segment.created_at.desc()).limit(page_size).offset(
        (page - 1) * page_size
    )
    result = await async_db.execute(query)
    segments = result.scalars().all()

    return SegmentListResponse(
        segments=[SegmentOut.model_validate(s.to_dict()) for s in segments],
        total=total,
        page=page,
        page_size=page_size,
    )


# ── CREATE SEGMENT ───────────────────────────────────────────────


@router.post(
    "",
    response_model=SegmentOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new segment",
)
@limiter.limit("100/minute")
async def create_segment(
    request: Request,
    body: SegmentCreateRequest,
    db: Any = Depends(get_db),
    merchant: Merchant = Depends(get_merchant_flexible),
):
    """Create a new segment with condition-based targeting.

    Supports nested AND/OR conditions up to 5 levels deep.
    Attributes can be from user, session, event, or custom namespaces.
    """

    from sqlalchemy.ext.asyncio import AsyncSession

    async_db: AsyncSession = db

    # Get merchant (when auth is added)
    # merchant = await authenticate_sdk_key(db, sdk_key_hash)
    merchant_id = merchant.id

    # Convert conditions to dict format
    conditions_dict = body.conditions.model_dump()

    segment = Segment(
        merchant_id=merchant_id,
        name=body.name,
        description=body.description,
        conditions=conditions_dict,
        segment_type=body.segment_type,
    )

    async_db.add(segment)
    await async_db.commit()
    await async_db.refresh(segment)

    return SegmentOut.model_validate(segment.to_dict())


# ── GET SEGMENT ─────────────────────────────────────────────────


@router.get("/{segment_id}", response_model=SegmentOut, summary="Get segment details")
@limiter.limit("200/minute")
async def get_segment(
    request: Request,
    segment_id: str,
    db: Any = Depends(get_db),
):
    """Get detailed information about a specific segment."""
    from uuid import UUID

    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession

    async_db: AsyncSession = db

    try:
        segment_uuid = UUID(segment_id)
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid segment ID format"
        ) from None

    result = await async_db.execute(
        select(Segment).where(Segment.id == segment_uuid)
    )
    segment = result.scalar_one_or_none()

    if not segment:
        raise HTTPException(status_code=404, detail=f"Segment '{segment_id}' not found")

    return SegmentOut.model_validate(segment.to_dict())


# ── GET SEGMENT WITH EMOTION PROFILE ──────────────────────────


@router.get(
    "/{segment_id}/with-profile",
    response_model=dict,
    summary="Get segment details with emotion profile",
)
@limiter.limit("100/minute")
async def get_segment_with_profile(
    request: Request,
    segment_id: str,
    days: int = Query(30, ge=1, le=365, description="Days to analyze"),
    db: Any = Depends(get_db),
):
    """Get segment details along with emotional profile."""
    from uuid import UUID

    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession

    async_db: AsyncSession = db

    try:
        segment_uuid = UUID(segment_id)
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid segment ID format"
        ) from None

    result = await async_db.execute(
        select(Segment).where(Segment.id == segment_uuid)
    )
    segment = result.scalar_one_or_none()

    if not segment:
        raise HTTPException(status_code=404, detail=f"Segment '{segment_id}' not found")

    # Get emotion profile
    emotion_profile = await service.get_segment_emotion_profile(
        segment_id, async_db, days
    )

    return {
        "segment": SegmentOut.model_validate(segment.to_dict()),
        "emotion_profile": EmotionProfileOut.model_validate(emotion_profile.to_dict())
        if emotion_profile
        else None,
    }


# ── UPDATE SEGMENT ───────────────────────────────────────────────


@router.patch("/{segment_id}", response_model=SegmentOut, summary="Update a segment")
@limiter.limit("100/minute")
async def update_segment(
    request: Request,
    segment_id: str,
    body: SegmentUpdateRequest,
    db: Any = Depends(get_db),
):
    """Update a segment.

    Partial update - only provided fields are modified.
    """
    from uuid import UUID

    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession

    async_db: AsyncSession = db

    try:
        segment_uuid = UUID(segment_id)
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid segment ID format"
        ) from None

    result = await async_db.execute(
        select(Segment).where(Segment.id == segment_uuid)
    )
    segment = result.scalar_one_or_none()

    if not segment:
        raise HTTPException(status_code=404, detail=f"Segment '{segment_id}' not found")

    # Update provided fields
    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "conditions" and value:
            # Convert Pydantic model to dict
            segment.conditions = value.model_dump()
        elif hasattr(segment, field):
            setattr(segment, field, value)

    segment.updated_at = datetime.now(UTC)

    await async_db.commit()
    await async_db.refresh(segment)

    return SegmentOut.model_validate(segment.to_dict())


# ── DELETE SEGMENT ───────────────────────────────────────────────


@router.delete(
    "/{segment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a segment",
)
@limiter.limit("100/minute")
async def delete_segment(
    request: Request,
    segment_id: str,
    db: Any = Depends(get_db),
):
    """Delete a segment."""
    from uuid import UUID

    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession

    async_db: AsyncSession = db

    try:
        segment_uuid = UUID(segment_id)
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid segment ID format"
        ) from None

    result = await async_db.execute(
        select(Segment).where(Segment.id == segment_uuid)
    )
    segment = result.scalar_one_or_none()

    if not segment:
        raise HTTPException(status_code=404, detail=f"Segment '{segment_id}' not found")

    await async_db.delete(segment)
    await async_db.commit()


# ── EVALUATE SEGMENT ───────────────────────────────────────────


@router.post(
    "/{segment_id}/evaluate",
    response_model=SegmentEvaluateResponse,
    summary="Test segment against sample user context",
)
@limiter.limit("500/minute")
async def evaluate_segment(
    request: Request,
    segment_id: str,
    body: SegmentEvaluateRequest,
    db: Any = Depends(get_db),
):
    """Test if a sample user context matches a segment.

    Useful for validating segment conditions before deployment.
    Returns which conditions matched and which failed.
    """
    from uuid import UUID

    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession

    async_db: AsyncSession = db

    try:
        segment_uuid = UUID(segment_id)
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid segment ID format"
        ) from None

    result = await async_db.execute(
        select(Segment).where(Segment.id == segment_uuid)
    )
    segment = result.scalar_one_or_none()

    if not segment:
        raise HTTPException(status_code=404, detail=f"Segment '{segment_id}' not found")

    # Evaluate segment
    matches = service.evaluate_segment(segment, body.user_context)

    # For detailed response, we'd need to track which conditions matched
    # For now, return simplified response
    return SegmentEvaluateResponse(
        segment_id=segment_id,
        matches=matches,
        matched_conditions=None,
        failed_conditions=None,
    )


# ── SYNC CRM ATTRIBUTES ───────────────────────────────────────────


@router.post(
    "/sync-crm",
    response_model=CRMSyncResponse,
    summary="Bulk sync CRM attributes",
)
@limiter.limit("50/minute")
async def sync_crm_attributes(
    request: Request,
    body: CRMSyncRequest,
    db: Any = Depends(get_db),
):
    """Bulk sync CRM attributes for multiple users.

    Attributes are stored under the custom.* namespace and can be
    used in segment conditions (e.g., custom.plan, custom.tier).
    """
    from sqlalchemy.ext.asyncio import AsyncSession

    async_db: AsyncSession = db

    synced = 0
    failed = 0
    errors: list[str] = []

    # Process in parallel for performance
    tasks = []
    for sync in body.syncs:
        tasks.append(
            service.sync_crm_attributes(sync.user_id, sync.attributes, async_db)
        )

    results = await asyncio.gather(*tasks, return_exceptions=True)

    for i, result in enumerate(results):
        if isinstance(result, Exception):
            failed += 1
            errors.append(f"User {body.syncs[i].user_id}: {str(result)}")
        else:
            synced += 1

    return CRMSyncResponse(
        synced=synced,
        failed=failed,
        errors=errors[:10],  # Limit errors in response
    )


# ── PREVIEW SEGMENT ───────────────────────────────────────────────


@router.get(
    "/{segment_id}/preview",
    response_model=SegmentPreviewResponse,
    summary="Preview segment size and sample users",
)
@limiter.limit("100/minute")
async def preview_segment(
    request: Request,
    segment_id: str,
    days: int = Query(30, ge=1, le=90, description="Days to sample"),
    db: Any = Depends(get_db),
):
    """Preview estimated segment size with anonymized sample users.

    Useful for understanding who a segment targets before deployment.
    """
    import hashlib
    from uuid import UUID

    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession

    async_db: AsyncSession = db

    try:
        segment_uuid = UUID(segment_id)
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid segment ID format"
        ) from None

    result = await async_db.execute(
        select(Segment).where(Segment.id == segment_uuid)
    )
    segment = result.scalar_one_or_none()

    if not segment:
        raise HTTPException(status_code=404, detail=f"Segment '{segment_id}' not found")

    # Estimate size
    size_estimate = await service.estimate_segment_size(segment, async_db, days)

    # Generate sample users (anonymized)
    # In production, would fetch from database
    sample_users: list[SampleUser] = []

    for i in range(min(10, size_estimate.sample_size)):
        # Create anonymized sample
        user_id_hash = hashlib.sha256(
            f"{segment_id}_{i}".encode()
        ).hexdigest()[:16]

        # Extract matched attributes from conditions
        matched_attrs = {}
        if "conditions" in segment.conditions:
            for cond in segment.conditions["conditions"]:
                if isinstance(cond, dict) and "attribute" in cond:
                    attr = cond["attribute"]
                    matched_attrs[attr] = "[sample_value]"

        sample_users.append(
            SampleUser(user_id_hash=user_id_hash, matched_attributes=matched_attrs)
        )

    return SegmentPreviewResponse(
        segment_id=segment_id,
        estimated_size=size_estimate.estimated_size,
        sample_size=size_estimate.sample_size,
        confidence=size_estimate.confidence,
        sample_users=sample_users,
    )


# ── CREATE EMOTIONAL COHORT ─────────────────────────────────────


@router.post(
    "/emotional-cohort",
    response_model=EmotionalCohortResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an emotional cohort segment",
)
@limiter.limit("50/minute")
async def create_emotional_cohort(
    request: Request,
    body: EmotionalCohortRequest,
    db: Any = Depends(get_db),
    merchant: Merchant = Depends(get_merchant_flexible),
):
    """Auto-create a dynamic segment based on emotion scores.

    Creates a segment that matches users with a specific emotion
    score threshold for a given experiment.
    """
    from uuid import uuid4

    from sqlalchemy.ext.asyncio import AsyncSession

    async_db: AsyncSession = db

    # Get merchant (when auth is added)
    merchant_id = uuid4()  # Placeholder

    segment = await service.create_emotional_cohort(
        emotion=body.emotion,
        min_score=body.min_score,
        experiment_id=body.experiment_id,
        merchant_id=merchant_id,
        db=async_db,
    )

    return EmotionalCohortResponse(
        segment_id=str(segment.id),
        name=segment.name,
        description=segment.description,
        conditions=segment.conditions,
        segment_type=segment.segment_type,  # type: ignore
    )


# ── REFRESH ESTIMATED SIZE ───────────────────────────────────────


@router.post(
    "/{segment_id}/refresh-size",
    response_model=SegmentOut,
    summary="Refresh estimated segment size",
)
@limiter.limit("50/minute")
async def refresh_segment_size(
    request: Request,
    segment_id: str,
    days: int = Query(30, ge=1, le=90),
    db: Any = Depends(get_db),
):
    """Refresh the estimated_size for a segment.

    Normally updated by background task every 6 hours for dynamic segments.
    Can be triggered manually via this endpoint.
    """
    from uuid import UUID

    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession

    async_db: AsyncSession = db

    try:
        segment_uuid = UUID(segment_id)
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid segment ID format"
        ) from None

    result = await async_db.execute(
        select(Segment).where(Segment.id == segment_uuid)
    )
    segment = result.scalar_one_or_none()

    if not segment:
        raise HTTPException(status_code=404, detail=f"Segment '{segment_id}' not found")

    # Re-estimate size
    size_estimate = await service.estimate_segment_size(segment, async_db, days)
    segment.estimated_size = size_estimate.estimated_size
    segment.updated_at = datetime.now(UTC)

    await async_db.commit()
    await async_db.refresh(segment)

    return SegmentOut.model_validate(segment.to_dict())
