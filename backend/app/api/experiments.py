"""Experiment CRUD & A/B Results API (CONV-38, CONV-41).

Provides full lifecycle management for experiments:
    POST   /experiments              — create experiment
    GET    /experiments              — list experiments (paginated)
    GET    /experiments/{id}         — get experiment detail
    PUT    /experiments/{id}         — update experiment
    DELETE /experiments/{id}         — delete experiment
    POST   /experiments/{id}/result  — record A/B test result
    GET    /experiments/{id}/stats   — statistical significance analysis

All endpoints are merchant-scoped via SDK key authentication.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import sanitize_text
from app.models.experiment import Experiment
from app.schemas.experiments import (
    ABResultRecordRequest,
    ABStatisticalSummary,
    ExperimentCreateRequest,
    ExperimentListResponse,
    ExperimentOut,
    ExperimentUpdateRequest,
)
from app.services.experiment_service import compute_ab_significance
from app.services.sdk_auth import authenticate_sdk_key, get_sdk_key_header

router = APIRouter(prefix="/experiments", tags=["experiments"])


def _experiment_to_out(exp: Experiment) -> ExperimentOut:
    return ExperimentOut(
        id=str(exp.id),
        merchant_id=str(exp.merchant_id),
        title=exp.title,
        hypothesis=exp.hypothesis,
        page_element=exp.page_element,
        friction_type=exp.friction_type,
        variant_a=exp.variant_a,
        variant_b=exp.variant_b,
        result=exp.result,
        conversion_delta=exp.conversion_delta,
        sample_size=exp.sample_size,
        ran_at=exp.ran_at,
        source=exp.source,
        created_at=exp.created_at,
    )


# ── CREATE ────────────────────────────────────────────────────────


@router.post("", response_model=ExperimentOut, status_code=201)
async def create_experiment(
    body: ExperimentCreateRequest,
    db: AsyncSession = Depends(get_db),
    sdk_key_hash: str = Depends(get_sdk_key_header),
):
    """Create a new experiment for the authenticated merchant."""
    merchant = await authenticate_sdk_key(db, sdk_key_hash)

    exp = Experiment(
        merchant_id=merchant.id,
        title=sanitize_text(body.title, max_length=256),
        hypothesis=sanitize_text(body.hypothesis, max_length=2000) if body.hypothesis else None,
        page_element=body.page_element,
        friction_type=body.friction_type,
        variant_a=sanitize_text(body.variant_a, max_length=2000) if body.variant_a else None,
        variant_b=sanitize_text(body.variant_b, max_length=2000) if body.variant_b else None,
        source="manual",
    )

    db.add(exp)
    await db.commit()
    await db.refresh(exp)

    return _experiment_to_out(exp)


# ── LIST ──────────────────────────────────────────────────────────


@router.get("", response_model=ExperimentListResponse)
async def list_experiments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    friction_type: str | None = Query(
        None, pattern=r"^(hesitation|rage_click|scroll_retreat|exit_intent|checkout_delay)$"
    ),
    result: str | None = Query(
        None, pattern=r"^(a_wins|b_wins|no_diff|inconclusive)$"
    ),
    db: AsyncSession = Depends(get_db),
    sdk_key_hash: str = Depends(get_sdk_key_header),
):
    """List experiments for the authenticated merchant with optional filters."""
    merchant = await authenticate_sdk_key(db, sdk_key_hash)

    query = select(Experiment).where(Experiment.merchant_id == merchant.id)

    if friction_type:
        query = query.where(Experiment.friction_type == friction_type)
    if result:
        query = query.where(Experiment.result == result)

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    offset = (page - 1) * page_size
    query = query.order_by(Experiment.created_at.desc()).offset(offset).limit(page_size)
    rows = await db.execute(query)
    experiments = rows.scalars().all()

    return ExperimentListResponse(
        experiments=[_experiment_to_out(e) for e in experiments],
        total=total,
        page=page,
        page_size=page_size,
    )


# ── GET ONE ───────────────────────────────────────────────────────


@router.get("/{experiment_id}", response_model=ExperimentOut)
async def get_experiment(
    experiment_id: str,
    db: AsyncSession = Depends(get_db),
    sdk_key_hash: str = Depends(get_sdk_key_header),
):
    """Get a single experiment by ID."""
    merchant = await authenticate_sdk_key(db, sdk_key_hash)

    try:
        eid = uuid.UUID(experiment_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid experiment ID") from exc

    result = await db.execute(
        select(Experiment).where(Experiment.id == eid, Experiment.merchant_id == merchant.id)
    )
    exp = result.scalar_one_or_none()
    if exp is None:
        raise HTTPException(status_code=404, detail="Experiment not found")

    return _experiment_to_out(exp)


# ── UPDATE ────────────────────────────────────────────────────────


@router.put("/{experiment_id}", response_model=ExperimentOut)
async def update_experiment(
    experiment_id: str,
    body: ExperimentUpdateRequest,
    db: AsyncSession = Depends(get_db),
    sdk_key_hash: str = Depends(get_sdk_key_header),
):
    """Update an existing experiment. Only provided fields are changed."""
    merchant = await authenticate_sdk_key(db, sdk_key_hash)

    try:
        eid = uuid.UUID(experiment_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid experiment ID") from exc

    # Build update values from non-None fields
    update_data = {}
    if body.title is not None:
        update_data["title"] = sanitize_text(body.title, max_length=256)
    if body.hypothesis is not None:
        update_data["hypothesis"] = sanitize_text(body.hypothesis, max_length=2000)
    if body.page_element is not None:
        update_data["page_element"] = body.page_element
    if body.friction_type is not None:
        update_data["friction_type"] = body.friction_type
    if body.variant_a is not None:
        update_data["variant_a"] = sanitize_text(body.variant_a, max_length=2000)
    if body.variant_b is not None:
        update_data["variant_b"] = sanitize_text(body.variant_b, max_length=2000)
    if body.result is not None:
        update_data["result"] = body.result
    if body.conversion_delta is not None:
        update_data["conversion_delta"] = body.conversion_delta
    if body.sample_size is not None:
        update_data["sample_size"] = body.sample_size
    if body.ran_at is not None:
        update_data["ran_at"] = body.ran_at

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    result = await db.execute(
        update(Experiment)
        .where(Experiment.id == eid, Experiment.merchant_id == merchant.id)
        .values(**update_data)
        .returning(Experiment.id)
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Experiment not found")

    await db.commit()

    # Reload
    reload_result = await db.execute(select(Experiment).where(Experiment.id == eid))
    exp = reload_result.scalar_one()
    return _experiment_to_out(exp)


# ── DELETE ────────────────────────────────────────────────────────


@router.delete("/{experiment_id}", status_code=204)
async def delete_experiment(
    experiment_id: str,
    db: AsyncSession = Depends(get_db),
    sdk_key_hash: str = Depends(get_sdk_key_header),
):
    """Delete an experiment. Associated intervention results are also removed."""
    merchant = await authenticate_sdk_key(db, sdk_key_hash)

    try:
        eid = uuid.UUID(experiment_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid experiment ID") from exc

    result = await db.execute(
        delete(Experiment)
        .where(Experiment.id == eid, Experiment.merchant_id == merchant.id)
        .returning(Experiment.id)
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Experiment not found")

    await db.commit()


# ── A/B RESULT RECORDING (CONV-41) ───────────────────────────────


@router.post("/{experiment_id}/result", response_model=ExperimentOut)
async def record_ab_result(
    experiment_id: str,
    body: ABResultRecordRequest,
    db: AsyncSession = Depends(get_db),
    sdk_key_hash: str = Depends(get_sdk_key_header),
):
    """Record the outcome of an A/B experiment."""
    merchant = await authenticate_sdk_key(db, sdk_key_hash)

    try:
        eid = uuid.UUID(experiment_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid experiment ID") from exc

    result = await db.execute(
        update(Experiment)
        .where(Experiment.id == eid, Experiment.merchant_id == merchant.id)
        .values(
            result=body.result,
            conversion_delta=body.conversion_delta,
            sample_size=body.sample_size,
            ran_at=body.ran_at,
        )
        .returning(Experiment.id)
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Experiment not found")

    await db.commit()

    reload_result = await db.execute(select(Experiment).where(Experiment.id == eid))
    exp = reload_result.scalar_one()
    return _experiment_to_out(exp)


# ── STATISTICAL SIGNIFICANCE (CONV-41) ───────────────────────────


@router.get("/{experiment_id}/stats", response_model=ABStatisticalSummary)
async def get_experiment_stats(
    experiment_id: str,
    db: AsyncSession = Depends(get_db),
    sdk_key_hash: str = Depends(get_sdk_key_header),
):
    """Compute statistical significance for an experiment's results."""
    merchant = await authenticate_sdk_key(db, sdk_key_hash)

    try:
        eid = uuid.UUID(experiment_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid experiment ID") from exc

    result = await db.execute(
        select(Experiment).where(Experiment.id == eid, Experiment.merchant_id == merchant.id)
    )
    exp = result.scalar_one_or_none()
    if exp is None:
        raise HTTPException(status_code=404, detail="Experiment not found")

    # If no result data, return summary with insufficient_data
    if exp.conversion_delta is None or exp.sample_size is None:
        return ABStatisticalSummary(
            experiment_id=str(exp.id),
            title=exp.title,
            result=exp.result,
            conversion_delta=exp.conversion_delta,
            sample_size=exp.sample_size,
            recommendation="insufficient_data",
        )

    stats = compute_ab_significance(
        conversion_delta=exp.conversion_delta,
        sample_size=exp.sample_size,
    )

    return ABStatisticalSummary(
        experiment_id=str(exp.id),
        title=exp.title,
        result=exp.result,
        conversion_delta=exp.conversion_delta,
        sample_size=exp.sample_size,
        confidence_level=stats["confidence_level"],
        is_significant=stats["is_significant"],
        p_value=stats["p_value"],
        power=stats["power"],
        recommendation=stats["recommendation"],
    )
