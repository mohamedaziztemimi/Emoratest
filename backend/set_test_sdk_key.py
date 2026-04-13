"""Set a known test SDK key for the first merchant in the database."""

import asyncio
import hashlib

from sqlalchemy import select, update

from app.core.database import async_session
from app.models.merchant import Merchant

TEST_SDK_KEY = "test_sdk_key_123456"  # Use this in the test page


async def set_test_sdk_key():
    """Set a known test SDK key for the first active merchant."""
    async with async_session() as db:
        # Get first active merchant
        result = await db.execute(
            select(Merchant).where(Merchant.is_active.is_(True)).limit(1)
        )
        merchant = result.scalar_one_or_none()

        if not merchant:
            print("No active merchants found!")
            return

        # Compute hash
        key_hash = hashlib.sha256(TEST_SDK_KEY.encode()).hexdigest()

        # Update merchant
        await db.execute(
            update(Merchant)
            .where(Merchant.id == merchant.id)
            .values(sdk_key_hash=key_hash)
        )
        await db.commit()

        print(f"✅ Set SDK key for merchant: {merchant.email}")
        print(f"   SDK Key: {TEST_SDK_KEY}")
        print(f"   Hash: {key_hash}")
        print("\nUse this SDK key in the test page: http://localhost:8000/static/test-page.html")


if __name__ == "__main__":
    asyncio.run(set_test_sdk_key())
