"""Authentication & GDPR endpoints (Epic 6 — CONV-56 to CONV-60).

Provides:
    POST /auth/register  — create merchant account with password
    POST /auth/login     — authenticate and receive JWT
    GET  /auth/me        — get current merchant profile (JWT)
    POST /auth/gdpr/consent  — record GDPR consent
    GET  /auth/gdpr/export   — export all merchant data (GDPR Art. 20)
    DELETE /auth/gdpr/delete — delete all merchant data (GDPR Art. 17)
"""

import hashlib
import secrets
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import (
    create_access_token,
    get_current_merchant,
    hash_password,
    verify_password,
)
from app.core.database import get_db
from app.core.rate_limit import limiter
from app.models.event import Event
from app.models.experiment import Experiment
from app.models.intervention_result import InterventionResult
from app.models.merchant import Merchant
from app.models.session import Session
from app.models.session_features import SessionFeatures

router = APIRouter(prefix="/auth", tags=["auth"])


# ── Schemas ─────────────────────────────────────────────────────


class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    workspace_name: str = Field(min_length=3, max_length=255)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    shop_domain: str = Field(min_length=3, max_length=255)
    plan: str = "trial"
    gdpr_consent: bool = False


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    merchant_id: str
    email: str
    shop_domain: str
    plan: str
    sdk_key: str | None = None
    onboarding_completed: bool = False


class MerchantProfileResponse(BaseModel):
    id: str
    email: str
    shop_domain: str
    plan: str
    is_active: bool
    gdpr_consent: bool
    onboarding_completed: bool
    created_at: datetime


class GdprExportResponse(BaseModel):
    merchant: dict
    sessions_count: int
    events_count: int
    experiments_count: int
    exported_at: datetime


# ── POST /auth/register ─────────────────────────────────────────


@router.post("/register", response_model=AuthResponse, status_code=201)
@limiter.limit("10/minute")
async def register(
    request: Request,
    response: Response,
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """Register a new merchant with email + password."""
    # Check existing email
    existing = await db.execute(select(Merchant).where(Merchant.email == body.email))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="Email already registered")

    # Check existing domain
    existing_domain = await db.execute(
        select(Merchant).where(Merchant.shop_domain == body.shop_domain)
    )
    if existing_domain.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="Shop domain already registered")

    # Generate SDK key
    raw_sdk_key = secrets.token_hex(32)
    key_hash = hashlib.sha256(raw_sdk_key.encode()).hexdigest()
    now = datetime.now(UTC)

    merchant = Merchant(
        email=body.email,
        password_hash=hash_password(body.password),
        shop_domain=body.shop_domain,
        sdk_key_hash=key_hash,
        plan=body.plan,
        is_active=True,
        gdpr_consent=body.gdpr_consent,
        gdpr_consent_at=now if body.gdpr_consent else None,
        onboarding_completed=False,
        created_at=now,
        updated_at=now,
    )

    db.add(merchant)
    await db.commit()
    await db.refresh(merchant)

    token = create_access_token(str(merchant.id), merchant.email)

    # Set httpOnly cookie with JWT
    auth_response = AuthResponse(
        access_token=token,
        merchant_id=str(merchant.id),
        email=merchant.email,
        shop_domain=merchant.shop_domain,
        plan=merchant.plan,
        sdk_key=raw_sdk_key,
        onboarding_completed=False,
    )

    response = JSONResponse(content=auth_response.model_dump(mode="json"))
    response.set_cookie(
        key="auth_token",
        value=token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=60 * 60 * 24 * 7,  # 7 days
        path="/",  # Available on all paths
        domain=None,  # None means current host (localhost for dev)
    )
    return response


# ── POST /auth/signup ────────────────────────────────────────────


@router.post("/signup", response_model=AuthResponse, status_code=201)
@limiter.limit("10/minute")
async def signup(
    request: Request,
    response: Response,
    body: SignupRequest,
    db: AsyncSession = Depends(get_db),
):
    """Signup a new merchant. Alias for /auth/register with frontend-compatible field names."""
    # Check existing email
    existing = await db.execute(select(Merchant).where(Merchant.email == body.email))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="Email already registered")

    # Check existing domain
    existing_domain = await db.execute(
        select(Merchant).where(Merchant.shop_domain == body.workspace_name)
    )
    if existing_domain.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="Workspace name already registered")

    # Generate SDK key
    raw_sdk_key = secrets.token_hex(32)
    key_hash = hashlib.sha256(raw_sdk_key.encode()).hexdigest()
    now = datetime.now(UTC)

    merchant = Merchant(
        email=body.email,
        password_hash=hash_password(body.password),
        shop_domain=body.workspace_name,
        sdk_key_hash=key_hash,
        plan="trial",
        is_active=True,
        gdpr_consent=False,
        onboarding_completed=False,
        created_at=now,
        updated_at=now,
    )

    db.add(merchant)
    await db.commit()
    await db.refresh(merchant)

    token = create_access_token(str(merchant.id), merchant.email)

    # Set httpOnly cookie with JWT
    auth_response = AuthResponse(
        access_token=token,
        merchant_id=str(merchant.id),
        email=merchant.email,
        shop_domain=merchant.shop_domain,
        plan="trial",
        sdk_key=raw_sdk_key,
        onboarding_completed=False,
    )

    response = JSONResponse(content=auth_response.model_dump(mode="json"))
    response.set_cookie(
        key="auth_token",
        value=token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=60 * 60 * 24 * 7,  # 7 days
        path="/",  # Available on all paths
        domain=None,  # None means current host (localhost for dev)
    )
    return response


# ── POST /auth/login ────────────────────────────────────────────


@router.post("/login", response_model=AuthResponse)
@limiter.limit("20/minute")
async def login(
    request: Request,
    response: Response,
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate merchant and return JWT."""
    result = await db.execute(select(Merchant).where(Merchant.email == body.email))
    merchant = result.scalar_one_or_none()

    if merchant is None or merchant.password_hash is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not verify_password(body.password, merchant.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not merchant.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    token = create_access_token(str(merchant.id), merchant.email)

    # Set httpOnly cookie with JWT
    auth_response = AuthResponse(
        access_token=token,
        merchant_id=str(merchant.id),
        email=merchant.email,
        shop_domain=merchant.shop_domain,
        plan=merchant.plan,
        onboarding_completed=merchant.onboarding_completed,
    )

    response = JSONResponse(content=auth_response.model_dump(mode="json"))
    response.set_cookie(
        key="auth_token",
        value=token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=60 * 60 * 24 * 7,  # 7 days
        path="/",  # Available on all paths
        domain=None,  # None means current host (localhost for dev)
    )
    return response


# ── GET /auth/me ─────────────────────────────────────────────────


@router.get("/me", response_model=MerchantProfileResponse)
@limiter.limit("50/minute")
async def get_me(
    request: Request,
    merchant: Merchant = Depends(get_current_merchant),
):
    """Get authenticated merchant profile via JWT."""
    return MerchantProfileResponse(
        id=str(merchant.id),
        email=merchant.email,
        shop_domain=merchant.shop_domain,
        plan=merchant.plan,
        is_active=merchant.is_active,
        gdpr_consent=merchant.gdpr_consent,
        onboarding_completed=merchant.onboarding_completed,
        created_at=merchant.created_at,
    )


# ── POST /auth/onboarding-complete ──────────────────────────────


@router.post("/onboarding-complete")
@limiter.limit("10/minute")
async def complete_onboarding(
    request: Request,
    merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db),
):
    """Mark onboarding as completed and return SDK key."""
    merchant.onboarding_completed = True
    merchant.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(merchant)

    # Generate a new SDK key (one-time show after signup)
    raw_sdk_key = secrets.token_hex(32)
    key_hash = hashlib.sha256(raw_sdk_key.encode()).hexdigest()
    merchant.sdk_key_hash = key_hash
    await db.commit()

    return {
        "status": "ok",
        "sdk_key": raw_sdk_key,
        "shop_domain": merchant.shop_domain,
        "email": merchant.email,
    }


# ── GDPR endpoints (CONV-58, CONV-59, CONV-60) ──────────────────


@router.post("/gdpr/consent")
@limiter.limit("10/minute")
async def record_gdpr_consent(
    request: Request,
    merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db),
):
    """Record GDPR consent for data processing."""
    merchant.gdpr_consent = True
    merchant.gdpr_consent_at = datetime.now(UTC)
    merchant.updated_at = datetime.now(UTC)
    await db.commit()
    return {"status": "consent_recorded", "consented_at": merchant.gdpr_consent_at.isoformat()}


@router.get("/gdpr/export", response_model=GdprExportResponse)
@limiter.limit("5/minute")
async def export_merchant_data(
    request: Request,
    merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db),
):
    """Export all merchant data (GDPR Article 20 — data portability)."""
    sessions_count = (
        await db.execute(
            select(func.count()).select_from(
                select(Session.id).where(Session.merchant_id == merchant.id).subquery()
            )
        )
    ).scalar() or 0

    events_count = (
        await db.execute(
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
    ).scalar() or 0

    experiments_count = (
        await db.execute(
            select(func.count()).select_from(
                select(Experiment.id).where(Experiment.merchant_id == merchant.id).subquery()
            )
        )
    ).scalar() or 0

    return GdprExportResponse(
        merchant={
            "id": str(merchant.id),
            "email": merchant.email,
            "shop_domain": merchant.shop_domain,
            "plan": merchant.plan,
            "created_at": merchant.created_at.isoformat(),
            "gdpr_consent": merchant.gdpr_consent,
        },
        sessions_count=sessions_count,
        events_count=events_count,
        experiments_count=experiments_count,
        exported_at=datetime.now(UTC),
    )


@router.delete("/gdpr/delete")
@limiter.limit("2/minute")
async def delete_merchant_data(
    request: Request,
    merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db),
):
    """Delete all merchant data (GDPR Article 17 — right to erasure).

    This permanently deletes:
    - All sessions and their events/features
    - All experiments and intervention results
    - The merchant account itself
    """
    merchant_id = merchant.id
    session_ids = select(Session.id).where(Session.merchant_id == merchant_id)

    # Delete in dependency order
    await db.execute(delete(SessionFeatures).where(SessionFeatures.session_id.in_(session_ids)))
    await db.execute(delete(Event).where(Event.session_id.in_(session_ids)))
    await db.execute(
        delete(InterventionResult).where(InterventionResult.session_id.in_(session_ids))
    )
    await db.execute(delete(Session).where(Session.merchant_id == merchant_id))
    await db.execute(delete(Experiment).where(Experiment.merchant_id == merchant_id))
    await db.execute(delete(Merchant).where(Merchant.id == merchant_id))

    await db.commit()

    return {
        "status": "deleted",
        "message": "All your data has been permanently deleted.",
    }
