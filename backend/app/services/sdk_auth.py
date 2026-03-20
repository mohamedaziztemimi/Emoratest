"""SDK key authentication service (CONV-34)."""

from __future__ import annotations

from fastapi import Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.merchant import Merchant


async def authenticate_sdk_key(
    db: AsyncSession,
    sdk_key_hash: str,
) -> Merchant:
    """Look up a merchant by SDK key hash. Raise 401 if not found or inactive."""
    result = await db.execute(
        select(Merchant).where(
            Merchant.sdk_key_hash == sdk_key_hash,
            Merchant.is_active.is_(True),
        )
    )
    merchant = result.scalar_one_or_none()

    if merchant is None:
        raise HTTPException(status_code=401, detail="Invalid or inactive SDK key")

    return merchant


def get_sdk_key_header(
    x_sdk_key: str | None = Header(None, alias="X-SDK-Key"),
    sdk_key: str | None = None,  # query param fallback for sendBeacon
) -> str:
    """Extract SDK key hash from header or query param."""
    key = x_sdk_key or sdk_key
    if not key:
        raise HTTPException(status_code=401, detail="Missing SDK key")
    return key
