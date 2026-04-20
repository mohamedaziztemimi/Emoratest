"""
Create Demo Merchant for EmoraTest Demo Store

This creates a test merchant with a known SDK key for demo purposes.

RUN THIS FROM: C:/Conversiono/backend
    python -m scripts.create_demo_merchant

AFTER RUNNING: The SDK key below will be active:
    demo_store_key_12345

Then update the demo store .env.local with this key.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from app.core.database import async_session
from app.core.security import hash_sdk_key
from app.models.merchant import Merchant


async def create_demo_merchant():
    async with async_session() as db:
        result = await db.execute(
            select(Merchant).where(Merchant.email == "demo@store.com")
        )
        merchant = result.scalar_one_or_none()

        sdk_key = "demo_store_key_12345"

        if merchant:
            merchant.sdk_key_hash = hash_sdk_key(sdk_key)
            merchant.is_active = True
            merchant.company_name = "Demo Store"
            await db.commit()
            await db.refresh(merchant)
            print("✓ Updated existing demo merchant")
        else:
            merchant = Merchant(
                email="demo@store.com",
                company_name="Demo Store",
                sdk_key_hash=hash_sdk_key(sdk_key),
                is_active=True,
                plan="free",
            )
            db.add(merchant)
            await db.commit()
            await db.refresh(merchant)
            print("✓ Created new demo merchant")

        print(f"\n{'='*60}")
        print("DEMO MERCHANT CREATED")
        print(f"{'='*60}")
        print("Email:        demo@store.com")
        print("Company:      Demo Store")
        print(f"Merchant ID:  {merchant.id}")
        print("\nSDK KEY (use this in demo store):")
        print(f"  {sdk_key}")
        print("\nAdd this to C:/emoratest-demo-store/.env.local:")
        print(f"  NEXT_PUBLIC_SDK_KEY={sdk_key}")
        print(f"{'='*60}\n")

        return merchant


async def main():
    await create_demo_merchant()


if __name__ == "__main__":
    asyncio.run(main())
