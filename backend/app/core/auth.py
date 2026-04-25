"""JWT authentication for merchant dashboard (Epic 6 — CONV-56).

Provides password hashing, JWT token creation/verification,
and FastAPI dependency for protecting dashboard endpoints.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.merchant import Merchant

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(merchant_id: str, email: str) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": merchant_id,
        "email": email,
        "exp": expire,
        "iat": datetime.now(UTC),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc


async def get_current_merchant(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Merchant:
    """FastAPI dependency: extract and validate JWT from cookie or header, return Merchant."""
    # First try to get token from httpOnly cookie
    token = request.cookies.get("auth_token")

    # Fall back to Authorization header
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer " prefix

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    payload = decode_token(token)
    merchant_id = payload.get("sub")
    if not merchant_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    result = await db.execute(
        select(Merchant).where(
            Merchant.id == merchant_id,
            Merchant.is_active.is_(True),
        )
    )
    merchant = result.scalar_one_or_none()
    if merchant is None:
        raise HTTPException(status_code=401, detail="Merchant not found or inactive")
    return merchant


async def get_merchant_id(
    merchant: Merchant = Depends(get_current_merchant),
) -> str:
    """FastAPI dependency: return merchant ID as string for use in endpoints."""
    return merchant.id


async def get_merchant_flexible(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Merchant:
    """Accept either JWT cookie or SDK key auth for dashboard/SDK interoperability.

    Tries JWT cookie first, then falls back to X-SDK-Key header.
    Returns the authenticated Merchant or raises 401.
    """
    # Try JWT cookie first
    token = request.cookies.get("auth_token")
    if token:
        try:
            payload = decode_token(token)
            merchant_id = payload.get("sub")
            if merchant_id:
                result = await db.execute(
                    select(Merchant).where(
                        Merchant.id == merchant_id,
                        Merchant.is_active.is_(True),
                    )
                )
                merchant = result.scalar_one_or_none()
                if merchant:
                    return merchant
        except HTTPException:
            pass  # Fall through to SDK key auth
        except Exception:
            pass  # Fall through to SDK key auth

    # Try SDK key header (for SDK/server-side use)
    sdk_key = request.headers.get("X-SDK-Key")
    if sdk_key:
        key_hash = hashlib.sha256(sdk_key.encode()).hexdigest()
        result = await db.execute(
            select(Merchant).where(
                Merchant.sdk_key_hash == key_hash,
                Merchant.is_active.is_(True),
            )
        )
        merchant = result.scalar_one_or_none()
        if merchant:
            return merchant

    # Also check query param fallback for sendBeacon
    sdk_key_param = request.query_params.get("sdk_key")
    if sdk_key_param:
        key_hash = hashlib.sha256(sdk_key_param.encode()).hexdigest()
        result = await db.execute(
            select(Merchant).where(
                Merchant.sdk_key_hash == key_hash,
                Merchant.is_active.is_(True),
            )
        )
        merchant = result.scalar_one_or_none()
        if merchant:
            return merchant

    raise HTTPException(
        status_code=401,
        detail="Authentication required",
    )
