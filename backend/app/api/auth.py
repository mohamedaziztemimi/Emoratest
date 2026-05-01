"""Authentication & GDPR endpoints (Epic 6 — CONV-56 to CONV-60).

Provides:
    POST /auth/register  — create merchant account with password
    POST /auth/login     — authenticate and receive JWT
    GET  /auth/me        — get current merchant profile (JWT)
    POST /auth/forgot-password  — request password reset email
    POST /auth/reset-password    — reset password with token
    POST /auth/gdpr/consent  — record GDPR consent
    GET  /auth/gdpr/export   — export all merchant data (GDPR Art. 20)
    DELETE /auth/gdpr/delete — delete all merchant data (GDPR Art. 17)
"""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field, validator
from redis import asyncio as aioredis
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import (
    create_access_token,
    get_current_merchant,
    hash_password,
    verify_password,
)
from app.core.config import settings
from app.core.database import get_db
from app.core.redis_rate_limit import (
    rate_limit_gdpr_export,
    rate_limit_login,
    rate_limit_signup,
)
from app.models.event import Event
from app.models.experiment import Experiment
from app.models.intervention_result import InterventionResult
from app.models.merchant import Merchant
from app.models.session import Session
from app.models.session_features import SessionFeatures
from app.services.email import email_service

router = APIRouter(prefix="/auth", tags=["auth"])

# Login lockout settings
MAX_FAILED_ATTEMPTS = 10
LOCKOUT_MINUTES = 15
LOCKOUT_SECONDS = LOCKOUT_MINUTES * 60


async def get_redis() -> aioredis.Redis:
    """Get async Redis client for login lockout tracking."""
    return await aioredis.from_url(settings.REDIS_URL, decode_responses=True)


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


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=1, max_length=255)
    new_password: str = Field(min_length=8, max_length=128)

    @validator("new_password")
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


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


class UsageResponse(BaseModel):
    plan: str
    sessions_used: int
    sessions_limit: int
    reset_date: str


# ── POST /auth/register ─────────────────────────────────────────


@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(
    request: Request,
    response: Response,
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """Register a new merchant with email + password."""
    # Manual rate limiting via Redis
    await rate_limit_signup(request)
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
        plan="free",
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

    # Send welcome email
    try:
        await email_service.send_welcome(merchant.email, merchant.shop_domain)
    except Exception as e:
        # Don't fail registration if email fails
        pass

    # Set httpOnly cookie with JWT
    auth_response = AuthResponse(
        access_token=token,
        merchant_id=str(merchant.id),
        email=merchant.email,
        shop_domain=merchant.shop_domain,
        plan="free",
        sdk_key=raw_sdk_key,
        onboarding_completed=False,
    )

    response = JSONResponse(content=auth_response.model_dump(mode="json"))
    response.set_cookie(
        key="auth_token",
        value=token,
        httponly=True,
        secure=settings.COOKIE_SECURE,  # True in production (HTTPS), False in dev
        samesite=settings.COOKIE_SAMESITE,  # "none" for cross-domain, "lax" for same-site
        max_age=60 * 60 * 24 * 7,  # 7 days
        path="/",  # Available on all paths
        domain=settings.COOKIE_DOMAIN,  # ".emoratest.com" in production for subdomain sharing
    )
    return response


# ── POST /auth/signup ────────────────────────────────────────────


@router.post("/signup", response_model=AuthResponse, status_code=201)
async def signup(
    request: Request,
    response: Response,
    body: SignupRequest,
    db: AsyncSession = Depends(get_db),
):
    """Signup a new merchant. Alias for /auth/register with frontend-compatible field names."""
    # Manual rate limiting via Redis
    await rate_limit_signup(request)

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
        plan="free",
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

    # Send welcome email
    try:
        await email_service.send_welcome(merchant.email, merchant.shop_domain)
    except Exception as e:
        # Don't fail registration if email fails
        pass

    # Set httpOnly cookie with JWT
    auth_response = AuthResponse(
        access_token=token,
        merchant_id=str(merchant.id),
        email=merchant.email,
        shop_domain=merchant.shop_domain,
        plan="free",
        sdk_key=raw_sdk_key,
        onboarding_completed=False,
    )

    response = JSONResponse(content=auth_response.model_dump(mode="json"))
    response.set_cookie(
        key="auth_token",
        value=token,
        httponly=True,
        secure=settings.COOKIE_SECURE,  # True in production (HTTPS), False in dev
        samesite=settings.COOKIE_SAMESITE,  # "none" for cross-domain, "lax" for same-site
        max_age=60 * 60 * 24 * 7,  # 7 days
        path="/",  # Available on all paths
        domain=settings.COOKIE_DOMAIN,  # ".emoratest.com" in production for subdomain sharing
    )
    return response


# ── POST /auth/login ────────────────────────────────────────────


@router.post("/login", response_model=AuthResponse)
async def login(
    request: Request,
    response: Response,
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate merchant and return JWT.

    Implements account lockout after 10 failed attempts for 15 minutes.
    """
    # Manual rate limiting via Redis
    await rate_limit_login(request)

    redis = await get_redis()
    email = body.email

    # Check if account is locked out
    lockout_key = f"login_lockout:{email}"
    if await redis.exists(lockout_key):
        ttl = await redis.ttl(lockout_key)
        raise HTTPException(
            status_code=429,
            detail=f"Account locked due to too many failed attempts. Try again in {ttl} seconds.",
        )

    result = await db.execute(select(Merchant).where(Merchant.email == email))
    merchant = result.scalar_one_or_none()

    # Check credentials
    password_valid = False
    if merchant is not None and merchant.password_hash is not None:
        password_valid = verify_password(body.password, merchant.password_hash)

    if not password_valid:
        # Track failed attempt
        attempts_key = f"login_attempts:{email}"
        attempts = await redis.incr(attempts_key)
        await redis.expire(attempts_key, LOCKOUT_SECONDS)

        if attempts >= MAX_FAILED_ATTEMPTS:
            # Set lockout
            await redis.setex(lockout_key, LOCKOUT_SECONDS, "1")
            await redis.delete(attempts_key)
            raise HTTPException(
                status_code=429,
                detail=f"Too many failed attempts. Account locked for {LOCKOUT_MINUTES} minutes.",
            )

        remaining = MAX_FAILED_ATTEMPTS - attempts
        raise HTTPException(
            status_code=401,
            detail=f"Invalid email or password ({remaining} attempts remaining)",
        )

    if not merchant.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    # Successful login - clear failed attempts
    attempts_key = f"login_attempts:{email}"
    await redis.delete(attempts_key)

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
        secure=settings.COOKIE_SECURE,  # True in production (HTTPS), False in dev
        samesite=settings.COOKIE_SAMESITE,  # "none" for cross-domain, "lax" for same-site
        max_age=60 * 60 * 24 * 7,  # 7 days
        path="/",  # Available on all paths
        domain=settings.COOKIE_DOMAIN,  # ".emoratest.com" in production for subdomain sharing
    )
    return response


# ── POST /auth/forgot-password ───────────────────────────────────


@router.post("/forgot-password")
async def forgot_password(
    request: Request,
    body: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Request a password reset email.

    Always returns success to prevent email enumeration.
    If email exists, sends reset link with token valid for 30 minutes.
    """
    result = await db.execute(select(Merchant).where(Merchant.email == body.email))
    merchant = result.scalar_one_or_none()

    if merchant:
        # Generate secure reset token
        reset_token = secrets.token_urlsafe(32)
        reset_expires = datetime.now(UTC) + timedelta(
            minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES
        )

        # Store token in database
        await db.execute(
            update(Merchant)
            .where(Merchant.id == merchant.id)
            .values(
                password_reset_token=reset_token,
                password_reset_expires=reset_expires,
                updated_at=datetime.now(UTC),
            )
        )
        await db.commit()

        # Send password reset email
        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        await email_service.send_password_reset(
            to=merchant.email,
            reset_link=reset_link,
            expiry_minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES,
        )

    # Always return success to prevent email enumeration
    return {
        "status": "ok",
        "message": "If an account exists with that email, a password reset link has been sent.",
    }


# ── POST /auth/reset-password ────────────────────────────────────


@router.post("/reset-password")
async def reset_password(
    body: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Reset password using a valid reset token.

    Token must be valid and not expired.
    """
    # Find merchant with this reset token
    result = await db.execute(
        select(Merchant).where(Merchant.password_reset_token == body.token)
    )
    merchant = result.scalar_one_or_none()

    if not merchant:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired reset token"
        )

    # Check if token has expired
    if merchant.password_reset_expires and merchant.password_reset_expires < datetime.now(UTC):
        # Clear expired token
        await db.execute(
            update(Merchant)
            .where(Merchant.id == merchant.id)
            .values(
                password_reset_token=None,
                password_reset_expires=None,
            )
        )
        await db.commit()
        raise HTTPException(
            status_code=400,
            detail="Reset token has expired. Please request a new one."
        )

    # Update password
    await db.execute(
        update(Merchant)
        .where(Merchant.id == merchant.id)
        .values(
            password_hash=hash_password(body.new_password),
            password_reset_token=None,  # Clear the token
            password_reset_expires=None,
            updated_at=datetime.now(UTC),
        )
    )
    await db.commit()

    return {
        "status": "ok",
        "message": "Password has been reset successfully. You can now log in with your new password."
    }


# ── GET /auth/me ─────────────────────────────────────────────────


@router.get("/me", response_model=MerchantProfileResponse)
async def get_me(
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


@router.get("/usage", response_model=UsageResponse)
async def get_usage(
    merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db),
):
    """Get current account usage and limits."""
    now = datetime.now(UTC)
    current_month = now.month
    current_year = now.year

    # Calculate reset date (first of next month)
    if current_month == 12:
        reset_month = 1
        reset_year = current_year + 1
    else:
        reset_month = current_month + 1
        reset_year = current_year

    reset_date = f"{reset_year:04d}-{reset_month:02d}-01"

    # Calculate actual session count for current month from database
    month_start = datetime(now.year, now.month, 1, tzinfo=UTC)
    count_result = await db.execute(
        select(func.count()).select_from(
            select(Session.id).where(
                Session.merchant_id == merchant.id,
                Session.started_at >= month_start,
            ).subquery()
        )
    )
    actual_sessions_used = count_result.scalar() or 0

    return UsageResponse(
        plan=merchant.plan,
        sessions_used=actual_sessions_used,
        sessions_limit=merchant.monthly_session_limit,
        reset_date=reset_date,
    )


# ── POST /auth/onboarding-complete ──────────────────────────────


@router.post("/onboarding-complete")
async def complete_onboarding(
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
async def record_gdpr_consent(
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
async def export_merchant_data(
    request: Request,
    merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db),
):
    """Export all merchant data (GDPR Article 20 — data portability)."""
    # Manual rate limiting via Redis
    await rate_limit_gdpr_export(request)
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
async def delete_merchant_data(
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
