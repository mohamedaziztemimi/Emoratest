"""
Seed script for CONV-16: Load labeled session data into Postgres.

Generates 5,000+ synthetic labeled sessions with correlated behavioral
events and features for ML training baseline.

Usage:
    DATABASE_URL=postgresql+asyncpg://... python -m scripts.seed_sessions
"""

import asyncio
import hashlib
import json
import random
import uuid
from datetime import UTC, datetime, timedelta

import numpy as np
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

# ── Configuration ────────────────────────────────────────────

NUM_MERCHANTS = 3
NUM_SESSIONS = 5_000
PURCHASE_RATE = 0.04  # 4% conversion rate
BATCH_SIZE = 500

DEVICE_TYPES = ["desktop", "mobile", "tablet"]
DEVICE_WEIGHTS = [0.45, 0.45, 0.10]

COUNTRIES = ["US", "GB", "DE", "FR", "CA", "AU", "NL", "SE", "JP", "BR"]
COUNTRY_WEIGHTS = [0.30, 0.15, 0.10, 0.10, 0.08, 0.07, 0.05, 0.05, 0.05, 0.05]

PAGES = [
    "/products/{pid}",
    "/collections/summer-sale",
    "/cart",
    "/checkout",
    "/checkout/shipping",
    "/checkout/payment",
    "/",
    "/collections/new-arrivals",
    "/products/{pid}/reviews",
    "/account/login",
]

EVENT_TYPES = ["mouse_move", "click", "scroll", "exit_intent", "visibility"]

ELEMENTS = [
    "add-to-cart-btn", "buy-now-btn", "price-tag", "product-image",
    "size-selector", "color-picker", "checkout-btn", "shipping-form",
    "payment-form", "navbar-logo", "search-bar", "review-section",
    "quantity-input", "promo-code-input", "continue-btn",
]

# ── Helpers ──────────────────────────────────────────────────


def generate_merchants() -> list[dict]:
    merchants = []
    domains = ["acme-store.myshopify.com", "trendy-fashion.com", "gadget-hub.io"]
    emails = ["admin@acme-store.com", "hello@trendy-fashion.com", "ops@gadget-hub.io"]
    plans = ["growth", "scale", "starter"]

    for i in range(NUM_MERCHANTS):
        merchants.append({
            "id": uuid.uuid4(),
            "email": emails[i],
            "shop_domain": domains[i],
            "sdk_key_hash": hashlib.sha256(f"seed-key-{i}".encode()).hexdigest()[:64],
            "plan": plans[i],
            "is_active": True,
            "created_at": datetime.now(UTC) - timedelta(days=30),
            "updated_at": datetime.now(UTC),
        })
    return merchants


def generate_session(merchant_id: uuid.UUID, is_purchase: bool) -> dict:
    """Generate a single session with outcome-correlated fields."""
    session_id = uuid.uuid4()
    device = random.choices(DEVICE_TYPES, DEVICE_WEIGHTS)[0]
    country = random.choices(COUNTRIES, COUNTRY_WEIGHTS)[0]

    # Sessions that convert tend to be longer and on desktop
    if is_purchase:
        duration_s = random.uniform(120, 600)
        risk = random.uniform(0.0, 0.3)
        friction = random.uniform(0.0, 0.35)
        page = random.choice(PAGES[2:6])  # cart/checkout pages
    else:
        duration_s = random.uniform(10, 400)
        risk = random.uniform(0.3, 1.0)
        friction = random.uniform(0.2, 1.0)
        page = random.choice(PAGES)

    started = datetime.now(UTC) - timedelta(
        days=random.randint(1, 60),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
    )
    ended = started + timedelta(seconds=duration_s)
    expires = started + timedelta(days=90)

    pid = random.randint(1000, 9999)
    domain = random.choice(["acme-store.myshopify.com", "trendy-fashion.com", "gadget-hub.io"])
    page_url = f"https://{domain}{page.format(pid=pid)}"

    intent_labels = ["browsing", "comparing", "buying", "returning"]
    intent = "buying" if is_purchase else random.choices(
        intent_labels, [0.5, 0.3, 0.05, 0.15]
    )[0]

    return {
        "id": session_id,
        "merchant_id": merchant_id,
        "page_url": page_url,
        "started_at": started,
        "ended_at": ended,
        "outcome": "purchase" if is_purchase else "abandon",
        "abandonment_risk": round(risk, 4),
        "friction_score": round(friction, 4),
        "intent_label": intent,
        "country_code": country,
        "device_type": device,
        "expires_at": expires,
    }


def generate_events(session: dict) -> list[dict]:
    """Generate correlated events for a session."""
    is_purchase = session["outcome"] == "purchase"
    started = session["started_at"]
    ended = session["ended_at"]
    duration = (ended - started).total_seconds()

    # Purchasers have more deliberate events, abandoners have more erratic ones
    n_events = random.randint(15, 40) if is_purchase else random.randint(5, 25)

    events = []
    for _ in range(n_events):
        t_offset = random.uniform(0, duration)
        ts = started + timedelta(seconds=t_offset)

        # Weight event types based on outcome
        if is_purchase:
            etype = random.choices(
                EVENT_TYPES, [0.35, 0.35, 0.20, 0.02, 0.08]
            )[0]
        else:
            etype = random.choices(
                EVENT_TYPES, [0.25, 0.20, 0.25, 0.15, 0.15]
            )[0]

        x, y, velocity, element_id, metadata = None, None, None, None, None

        if etype in ("mouse_move", "click"):
            x = round(random.uniform(0, 1920), 1)
            y = round(random.uniform(0, 1080), 1)
            velocity = round(random.uniform(0, 2000), 1)
            if etype == "click":
                element_id = random.choice(ELEMENTS)
                # Rage clicks: rapid clicks in same area (more common in abandons)
                if not is_purchase and random.random() < 0.15:
                    metadata = {"rage_click": True, "click_count": random.randint(3, 8)}

        elif etype == "scroll":
            metadata = {
                "direction": random.choice(["up", "down"]),
                "delta": round(random.uniform(50, 800), 1),
                "viewport_pct": round(random.uniform(0, 100), 1),
            }

        elif etype == "exit_intent":
            x = round(random.uniform(0, 1920), 1)
            y = round(random.uniform(-50, 0), 1)  # mouse leaving viewport top
            metadata = {"trigger": random.choice(["mouse_leave", "tab_switch", "back_button"])}

        elif etype == "visibility":
            metadata = {"state": random.choice(["visible", "hidden"])}

        events.append({
            "session_id": session["id"],
            "type": etype,
            "ts": ts,
            "x": x,
            "y": y,
            "velocity": velocity,
            "element_id": element_id,
            "metadata": metadata,
        })

    return events


def compute_features(session: dict, events: list[dict]) -> dict:
    """Compute session_features from events, correlated with outcome."""
    is_purchase = session["outcome"] == "purchase"
    duration = (session["ended_at"] - session["started_at"]).total_seconds()

    clicks = [e for e in events if e["type"] == "click"]
    exit_intents = [e for e in events if e["type"] == "exit_intent"]
    mouse_moves = [e for e in events if e["type"] == "mouse_move"]
    scrolls = [e for e in events if e["type"] == "scroll"]

    # Rage click score: ratio of rage clicks
    rage_clicks = sum(
        1 for c in clicks if c.get("metadata") and c["metadata"].get("rage_click")
    )
    rage_score = round(rage_clicks / max(len(clicks), 1), 4)

    # Hesitation: purchasers hesitate less
    if is_purchase:
        hesitation = round(random.uniform(0.0, 0.3), 4)
        price_dwell = round(random.uniform(2.0, 15.0), 2)
        checkout_hesitation = round(random.uniform(0.0, 10.0), 2)
    else:
        hesitation = round(random.uniform(0.2, 1.0), 4)
        price_dwell = round(random.uniform(0.5, 45.0), 2)
        checkout_hesitation = round(random.uniform(5.0, 120.0), 2)

    # Scroll retreats: scrolling up after scrolling down
    retreat_count = sum(
        1 for s in scrolls
        if s.get("metadata") and s["metadata"].get("direction") == "up"
    )

    # Velocity variance from mouse moves
    velocities = [m["velocity"] for m in mouse_moves if m["velocity"] is not None]
    vel_variance = round(float(np.var(velocities)), 2) if len(velocities) > 1 else 0.0

    return {
        "session_id": session["id"],
        "hesitation_score": hesitation,
        "price_dwell_time_s": price_dwell,
        "rage_click_score": rage_score,
        "scroll_retreat_count": retreat_count,
        "exit_intent_count": len(exit_intents),
        "checkout_hesitation_s": checkout_hesitation,
        "velocity_variance": vel_variance,
        "session_duration_s": round(duration, 2),
    }


# ── Database insertion ───────────────────────────────────────


async def insert_batch(
    session: AsyncSession,
    table: str,
    rows: list[dict],
) -> None:
    """Insert rows using raw SQL for performance (bulk ORM is slower for seeds)."""
    if not rows:
        return

    # Serialize dicts/lists to JSON strings for JSONB columns (asyncpg requirement)
    for row in rows:
        for key, val in row.items():
            if isinstance(val, (dict, list)):
                row[key] = json.dumps(val)

    columns = list(rows[0].keys())
    col_names = ", ".join(columns)
    placeholders = ", ".join(f":{c}" for c in columns)
    stmt = text(f"INSERT INTO {table} ({col_names}) VALUES ({placeholders})")

    await session.execute(stmt, rows)


async def seed() -> None:
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session_factory() as db:
        # Check if data already exists
        result = await db.execute(text("SELECT COUNT(*) FROM sessions"))
        count = result.scalar()
        if count and count >= NUM_SESSIONS:
            print(f"Database already has {count} sessions. Skipping seed.")
            await engine.dispose()
            return

        print("Seeding Conversiono database...")

        # 1. Seed merchants
        merchants = generate_merchants()
        # Upsert merchants (skip if exist)
        for m in merchants:
            existing = await db.execute(
                text("SELECT id FROM merchants WHERE email = :email"),
                {"email": m["email"]},
            )
            if existing.scalar() is None:
                await insert_batch(db, "merchants", [m])
                print(f"  Created merchant: {m['shop_domain']}")
            else:
                print(f"  Merchant exists: {m['shop_domain']}")
        await db.commit()

        # Reload merchant IDs (in case they existed already)
        result = await db.execute(text("SELECT id FROM merchants"))
        merchant_ids = [row[0] for row in result.fetchall()]

        # 2. Generate sessions, events, features
        rng = np.random.default_rng(42)
        outcomes = rng.random(NUM_SESSIONS) < PURCHASE_RATE

        all_sessions = []
        all_events = []
        all_features = []

        print(f"  Generating {NUM_SESSIONS} sessions...")
        for i in range(NUM_SESSIONS):
            merchant_id = random.choice(merchant_ids)
            is_purchase = bool(outcomes[i])

            sess = generate_session(merchant_id, is_purchase)
            events = generate_events(sess)
            features = compute_features(sess, events)

            all_sessions.append(sess)
            all_events.extend(events)
            all_features.append(features)

        # 3. Insert in batches
        print(f"  Inserting {len(all_sessions)} sessions...")
        for i in range(0, len(all_sessions), BATCH_SIZE):
            batch = all_sessions[i : i + BATCH_SIZE]
            await insert_batch(db, "sessions", batch)
            await db.commit()

        print(f"  Inserting {len(all_events)} events...")
        # Events don't have 'id' — it's autoincrement, so remove it if present
        for i in range(0, len(all_events), BATCH_SIZE):
            batch = all_events[i : i + BATCH_SIZE]
            await insert_batch(db, "events", batch)
            await db.commit()

        print(f"  Inserting {len(all_features)} session_features...")
        for i in range(0, len(all_features), BATCH_SIZE):
            batch = all_features[i : i + BATCH_SIZE]
            await insert_batch(db, "session_features", batch)
            await db.commit()

        # 4. Summary
        purchases = sum(1 for s in all_sessions if s["outcome"] == "purchase")
        abandons = len(all_sessions) - purchases
        avg_events = len(all_events) / len(all_sessions)

        print("\n== Seed Complete ==============================")
        print(f"  Merchants:   {len(merchants)}")
        print(f"  Sessions:    {len(all_sessions)}")
        print(f"    Purchases: {purchases} ({purchases/len(all_sessions)*100:.1f}%)")
        print(f"    Abandons:  {abandons} ({abandons/len(all_sessions)*100:.1f}%)")
        print(f"  Events:      {len(all_events)} (avg {avg_events:.1f}/session)")
        print(f"  Features:    {len(all_features)}")
        print("===============================================")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
