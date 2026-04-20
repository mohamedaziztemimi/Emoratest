"""Merchant API Key Management (CONV-43).

Provides:
    POST /merchants/rotate-key  — rotate SDK key (invalidate old, issue new)
    GET  /merchants/me           — get current merchant profile
    GET  /merchants/usage        — API usage summary

All endpoints authenticated via existing SDK key.
"""

import hashlib
import secrets
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_merchant_flexible
from app.core.database import get_db
from app.core.rate_limit import limiter
from app.models.event import Event
from app.models.experiment import Experiment
from app.models.merchant import Merchant
from app.models.session import Session

router = APIRouter(prefix="/merchants", tags=["merchants"])


# ── Schemas ───────────────────────────────────────────────────────


class MerchantProfile(BaseModel):
    id: str
    email: str
    shop_domain: str
    plan: str
    is_active: bool
    created_at: datetime


class KeyRotationResponse(BaseModel):
    new_sdk_key: str
    message: str
    rotated_at: datetime


class MerchantCreateRequest(BaseModel):
    email: EmailStr
    shop_domain: str
    plan: str = "free"


class MerchantCreateResponse(BaseModel):
    id: str
    email: str
    shop_domain: str
    plan: str
    sdk_key: str
    message: str
    created_at: datetime


class UsageSummary(BaseModel):
    total_sessions: int
    total_events: int
    total_experiments: int
    active_sessions_today: int
    plan: str
    checked_at: datetime


# ── POST / — create merchant + issue initial SDK key (CONV-43) ────


@router.post("", response_model=MerchantCreateResponse, status_code=201)
@limiter.limit("10/minute")
async def create_merchant(
    request: Request,
    body: MerchantCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new merchant and issue their first SDK key.

    The raw SDK key is returned ONCE — it cannot be retrieved again.
    The database stores only the SHA-256 hash.
    """
    # Check if email already exists
    existing = await db.execute(
        select(Merchant).where(Merchant.email == body.email)
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="A merchant with this email already exists")

    # Check if shop_domain already exists
    existing_domain = await db.execute(
        select(Merchant).where(Merchant.shop_domain == body.shop_domain)
    )
    if existing_domain.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=409,
            detail="A merchant with this shop domain already exists",
        )

    # Generate SDK key
    raw_key = secrets.token_hex(32)
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

    now = datetime.now(UTC)

    merchant = Merchant(
        email=body.email,
        shop_domain=body.shop_domain,
        plan=body.plan,
        sdk_key_hash=key_hash,
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    db.add(merchant)
    await db.commit()
    await db.refresh(merchant)

    return MerchantCreateResponse(
        id=str(merchant.id),
        email=merchant.email,
        shop_domain=merchant.shop_domain,
        plan=merchant.plan,
        sdk_key=raw_key,
        message="Merchant created. Store the SDK key securely — it cannot be retrieved again.",
        created_at=merchant.created_at,
    )


# ── GET /me ───────────────────────────────────────────────────────


@router.get("/me", response_model=MerchantProfile)
@limiter.limit("50/minute")
async def get_merchant_profile(
    request: Request,
    db: AsyncSession = Depends(get_db),
    merchant: Merchant = Depends(get_merchant_flexible),
):
    """Get the authenticated merchant's profile."""

    return MerchantProfile(
        id=str(merchant.id),
        email=merchant.email,
        shop_domain=merchant.shop_domain,
        plan=merchant.plan,
        is_active=merchant.is_active,
        created_at=merchant.created_at,
    )


# ── POST /rotate-key ─────────────────────────────────────────────


@router.post("/rotate-key", response_model=KeyRotationResponse)
@limiter.limit("50/minute")
async def rotate_sdk_key(
    request: Request,
    db: AsyncSession = Depends(get_db),
    merchant: Merchant = Depends(get_merchant_flexible),
):
    """Rotate the merchant's SDK key.

    Generates a new 32-byte hex key, hashes it with SHA-256,
    and updates the merchant record. The old key is immediately invalidated.

    The raw key is returned ONCE in the response — it cannot be retrieved again.
    """

    # Generate new key
    new_raw_key = secrets.token_hex(32)
    new_hash = hashlib.sha256(new_raw_key.encode()).hexdigest()

    now = datetime.now(UTC)

    await db.execute(
        update(Merchant)
        .where(Merchant.id == merchant.id)
        .values(sdk_key_hash=new_hash, updated_at=now)
    )
    await db.commit()

    return KeyRotationResponse(
        new_sdk_key=new_raw_key,
        message=(
            "SDK key rotated successfully."
            " Store this key securely — it cannot be retrieved again."
        ),
        rotated_at=now,
    )


# ── GET /usage ────────────────────────────────────────────────────


@router.get("/usage", response_model=UsageSummary)
@limiter.limit("50/minute")
async def get_usage_summary(
    request: Request,
    db: AsyncSession = Depends(get_db),
    merchant: Merchant = Depends(get_merchant_flexible),
):
    """Get API usage summary for the authenticated merchant."""

    # Total sessions
    sess_result = await db.execute(
        select(func.count()).select_from(
            select(Session.id).where(Session.merchant_id == merchant.id).subquery()
        )
    )
    total_sessions = sess_result.scalar() or 0

    # Total events (across all merchant sessions)
    events_result = await db.execute(
        select(func.count()).select_from(
            select(Event.id)
            .where(
                Event.session_id.in_(
                    select(Session.id).where(Session.merchant_id == merchant.id)
                )
            )
            .subquery()
        )
    )
    total_events = events_result.scalar() or 0

    # Total experiments
    exp_result = await db.execute(
        select(func.count()).select_from(
            select(Experiment.id).where(Experiment.merchant_id == merchant.id).subquery()
        )
    )
    total_experiments = exp_result.scalar() or 0

    # Active sessions today

    today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    active_result = await db.execute(
        select(func.count()).select_from(
            select(Session.id)
            .where(
                Session.merchant_id == merchant.id,
                Session.started_at >= today_start,
            )
            .subquery()
        )
    )
    active_today = active_result.scalar() or 0

    return UsageSummary(
        total_sessions=total_sessions,
        total_events=total_events,
        total_experiments=total_experiments,
        active_sessions_today=active_today,
        plan=merchant.plan,
        checked_at=datetime.now(UTC),
    )
