"""Redis-based rate limiting for auth endpoints.

Provides manual rate limiting using Redis when slowapi.storage is unavailable.
Used for login/signup endpoints with stricter limits.
"""

from __future__ import annotations

import time
from typing import Callable

from fastapi import HTTPException, Request
from redis import asyncio as aioredis

from app.core.config import settings

# Rate limits
LOGIN_LIMIT = 10  # requests per minute
SIGNUP_LIMIT = 10  # requests per minute
WINDOW_SECONDS = 60


async def get_redis() -> aioredis.Redis:
    """Get async Redis client."""
    return await aioredis.from_url(settings.REDIS_URL, decode_responses=True)


async def check_rate_limit(
    redis: aioredis.Redis,
    key: str,
    limit: int,
    window: int = WINDOW_SECONDS,
) -> bool:
    """Check if request is within rate limit using sliding window.

    Returns True if allowed, False if rate limited.
    """
    current = int(time.time())
    window_start = current - window

    # Use a sorted set for sliding window
    pipe = redis.pipeline()
    pipe.zremrangebyscore(key, 0, window_start)  # Remove old entries
    pipe.zadd(key, {str(current): current})  # Add current request
    pipe.zcard(key)  # Count requests in window
    pipe.expire(key, window)  # Auto cleanup
    results = await pipe.execute()

    count = results[2]
    return count <= limit


async def rate_limit_login(request: Request) -> None:
    """Rate limit login endpoint using Redis."""
    redis = await get_redis()
    identifier = request.client.host if request.client else "unknown"
    key = f"ratelimit:login:{identifier}"

    allowed = await check_rate_limit(redis, key, LOGIN_LIMIT)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Too many login attempts. Please try again later.",
        )


async def rate_limit_signup(request: Request) -> None:
    """Rate limit signup endpoint using Redis."""
    redis = await get_redis()
    identifier = request.client.host if request.client else "unknown"
    key = f"ratelimit:signup:{identifier}"

    allowed = await check_rate_limit(redis, key, SIGNUP_LIMIT)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Too many signup attempts. Please try again later.",
        )


async def rate_limit_gdpr_export(request: Request) -> None:
    """Rate limit GDPR export endpoint using Redis."""
    redis = await get_redis()
    identifier = request.client.host if request.client else "unknown"
    key = f"ratelimit:gdpr_export:{identifier}"

    allowed = await check_rate_limit(redis, key, 5, 60)  # 5 requests per minute
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Too many export attempts. Please try again later.",
        )
