"""
Seed script for demo: Psychology-grounded behavioral data for dashboard testing.

Generates realistic e-commerce sessions with correlated behavioral signals,
experiments with real A/B test insights, and intervention results — all
grounded in the psychology framework (Kahneman, Cialdini, Schwartz, etc.).

Usage:
    cd backend && python -m scripts.seed_demo
"""

import asyncio
import json
import random
import uuid
from datetime import UTC, date, datetime, timedelta

import numpy as np
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

# ── Our test merchant ─────────────────────────────────────────
MERCHANT_ID = uuid.UUID("22c97348-8d1f-42a8-8344-da1407e50cc4")

# ── Configuration ─────────────────────────────────────────────
NUM_SESSIONS = 800
PURCHASE_RATE = 0.038  # 3.8% — realistic e-commerce conversion
BATCH_SIZE = 200

DEVICE_TYPES = ["desktop", "mobile", "tablet"]
DEVICE_WEIGHTS = [0.42, 0.48, 0.10]  # mobile-first reality

COUNTRIES = ["US", "GB", "DE", "FR", "CA", "AU", "NL", "SE", "JP", "BR"]
COUNTRY_WEIGHTS = [0.30, 0.15, 0.10, 0.10, 0.08, 0.07, 0.05, 0.05, 0.05, 0.05]

# Realistic e-commerce page URLs
PRODUCT_PAGES = [
    "/products/wireless-noise-cancelling-headphones",
    "/products/organic-cotton-oversized-tee",
    "/products/ceramic-pour-over-coffee-set",
    "/products/minimalist-leather-wallet",
    "/products/bamboo-yoga-mat-pro",
    "/products/smart-led-desk-lamp",
    "/products/merino-wool-running-socks-3pk",
    "/products/stainless-steel-water-bottle-750ml",
    "/products/handmade-soy-candle-set",
    "/products/portable-bluetooth-speaker",
]

COLLECTION_PAGES = [
    "/collections/summer-sale",
    "/collections/new-arrivals",
    "/collections/best-sellers",
    "/collections/under-50",
]

CHECKOUT_PAGES = ["/cart", "/checkout", "/checkout/shipping", "/checkout/payment"]

ELEMENTS = {
    "product": [
        "add-to-cart-btn", "buy-now-btn", "price-tag", "product-image",
        "size-selector", "color-picker", "review-section", "quantity-input",
        "product-description", "shipping-info", "returns-policy",
    ],
    "checkout": [
        "checkout-btn", "shipping-form", "payment-form", "promo-code-input",
        "continue-btn", "order-summary", "shipping-method-select",
        "card-number-input", "place-order-btn", "trust-badge",
    ],
    "navigation": [
        "navbar-logo", "search-bar", "cart-icon", "menu-toggle",
        "back-button", "breadcrumb",
    ],
}

# ── Psychology-based session archetypes ───────────────────────
# Each archetype represents a real behavioral pattern grounded in research

ARCHETYPES = {
    "decisive_buyer": {
        # Quick, confident path to purchase. Low friction throughout.
        "weight": 0.04,
        "outcome": "purchase",
        "intent": "deciding",
        "risk_range": (0.02, 0.15),
        "friction_range": (0.05, 0.20),
        "duration_range": (90, 300),
        "hesitation_range": (0.02, 0.15),
        "price_dwell_range": (2.0, 8.0),
        "rage_click_prob": 0.01,
        "exit_intent_range": (0, 0),
        "scroll_retreat_range": (0, 2),
        "checkout_hesitation_range": (1.0, 8.0),
        "velocity_var_range": (5000, 30000),
        "pages": CHECKOUT_PAGES,
        "event_count_range": (20, 45),
    },
    "loss_aversion_buyer": {
        # Hesitates at price but converts after seeing guarantees
        "weight": 0.03,
        "outcome": "purchase",
        "intent": "deciding",
        "risk_range": (0.15, 0.35),
        "friction_range": (0.25, 0.45),
        "duration_range": (180, 480),
        "hesitation_range": (0.25, 0.45),
        "price_dwell_range": (12.0, 25.0),
        "rage_click_prob": 0.05,
        "exit_intent_range": (0, 1),
        "scroll_retreat_range": (2, 5),
        "checkout_hesitation_range": (12.0, 25.0),
        "velocity_var_range": (20000, 60000),
        "pages": CHECKOUT_PAGES,
        "event_count_range": (25, 50),
    },
    "price_shock_abandoner": {
        # Prospect Theory: unexpected shipping cost triggers loss aversion → abandon
        "weight": 0.18,
        "outcome": "abandon",
        "intent": "deciding",
        "risk_range": (0.65, 0.92),
        "friction_range": (0.55, 0.85),
        "duration_range": (60, 200),
        "hesitation_range": (0.10, 0.30),
        "price_dwell_range": (18.0, 45.0),  # long price stare
        "rage_click_prob": 0.10,
        "exit_intent_range": (1, 3),
        "scroll_retreat_range": (1, 3),
        "checkout_hesitation_range": (2.0, 8.0),  # quick abandon after seeing total
        "velocity_var_range": (40000, 120000),
        "pages": ["/checkout/shipping", "/checkout/payment", "/cart"],
        "event_count_range": (12, 30),
    },
    "decision_fatigue_abandoner": {
        # Schwartz Paradox of Choice: too many options → ego depletion → abandon
        "weight": 0.15,
        "outcome": "abandon",
        "intent": "comparing",
        "risk_range": (0.55, 0.85),
        "friction_range": (0.50, 0.80),
        "duration_range": (300, 720),  # very long sessions
        "hesitation_range": (0.35, 0.70),
        "price_dwell_range": (5.0, 15.0),
        "rage_click_prob": 0.08,
        "exit_intent_range": (1, 4),
        "scroll_retreat_range": (5, 12),  # many back-and-forth scrolls
        "checkout_hesitation_range": (15.0, 60.0),
        "velocity_var_range": (30000, 80000),
        "pages": PRODUCT_PAGES + COLLECTION_PAGES,
        "event_count_range": (20, 50),
    },
    "trust_gap_abandoner": {
        # McKnight trust theory: no trust signals → won't enter payment info
        "weight": 0.12,
        "outcome": "abandon",
        "intent": "deciding",
        "risk_range": (0.60, 0.88),
        "friction_range": (0.45, 0.75),
        "duration_range": (120, 350),
        "hesitation_range": (0.30, 0.55),
        "price_dwell_range": (8.0, 20.0),
        "rage_click_prob": 0.05,
        "exit_intent_range": (1, 3),
        "scroll_retreat_range": (3, 7),
        "checkout_hesitation_range": (20.0, 50.0),  # long pause at payment
        "velocity_var_range": (25000, 70000),
        "pages": ["/checkout/payment", "/checkout", "/cart"],
        "event_count_range": (15, 35),
    },
    "ui_frustrated_abandoner": {
        # Nielsen usability: broken expectations → rage clicks → bounce
        "weight": 0.10,
        "outcome": "abandon",
        "intent": "exiting",
        "risk_range": (0.75, 0.98),
        "friction_range": (0.70, 0.98),
        "duration_range": (30, 150),
        "hesitation_range": (0.10, 0.25),
        "price_dwell_range": (1.0, 5.0),
        "rage_click_prob": 0.60,  # HIGH rage click probability
        "exit_intent_range": (2, 5),
        "scroll_retreat_range": (1, 4),
        "checkout_hesitation_range": (2.0, 10.0),
        "velocity_var_range": (80000, 250000),  # erratic mouse = frustration
        "pages": PRODUCT_PAGES + CHECKOUT_PAGES,
        "event_count_range": (8, 25),
    },
    "comparison_shopper": {
        # Tab-switching, multiple product views, comparing options
        "weight": 0.14,
        "outcome": "abandon",
        "intent": "comparing",
        "risk_range": (0.40, 0.70),
        "friction_range": (0.25, 0.50),
        "duration_range": (180, 500),
        "hesitation_range": (0.20, 0.40),
        "price_dwell_range": (10.0, 30.0),
        "rage_click_prob": 0.03,
        "exit_intent_range": (2, 6),  # tab switching = comparison shopping
        "scroll_retreat_range": (3, 8),
        "checkout_hesitation_range": (5.0, 20.0),
        "velocity_var_range": (15000, 50000),
        "pages": PRODUCT_PAGES,
        "event_count_range": (18, 40),
    },
    "casual_browser": {
        # No purchase intent, just looking. Low engagement.
        "weight": 0.20,
        "outcome": "abandon",
        "intent": "browsing",
        "risk_range": (0.30, 0.55),
        "friction_range": (0.10, 0.35),
        "duration_range": (15, 120),
        "hesitation_range": (0.05, 0.20),
        "price_dwell_range": (1.0, 6.0),
        "rage_click_prob": 0.02,
        "exit_intent_range": (0, 2),
        "scroll_retreat_range": (0, 3),
        "checkout_hesitation_range": (0.0, 3.0),
        "velocity_var_range": (5000, 25000),
        "pages": COLLECTION_PAGES + PRODUCT_PAGES[:3],
        "event_count_range": (5, 15),
    },
    "approach_avoidance": {
        # Lewin: wants to buy but fears regret → add-to-cart then remove
        "weight": 0.04,
        "outcome": "abandon",
        "intent": "deciding",
        "risk_range": (0.50, 0.80),
        "friction_range": (0.40, 0.70),
        "duration_range": (150, 400),
        "hesitation_range": (0.30, 0.55),
        "price_dwell_range": (8.0, 22.0),
        "rage_click_prob": 0.05,
        "exit_intent_range": (1, 3),
        "scroll_retreat_range": (4, 9),
        "checkout_hesitation_range": (10.0, 35.0),
        "velocity_var_range": (30000, 75000),
        "pages": ["/cart"] + PRODUCT_PAGES[:4],
        "event_count_range": (15, 35),
    },
}


# ── Session generation ────────────────────────────────────────


def pick_archetype() -> tuple[str, dict]:
    names = list(ARCHETYPES.keys())
    weights = [ARCHETYPES[n]["weight"] for n in names]
    chosen = random.choices(names, weights)[0]
    return chosen, ARCHETYPES[chosen]


def generate_session(arch_name: str, arch: dict) -> dict:
    session_id = uuid.uuid4()
    device = random.choices(DEVICE_TYPES, DEVICE_WEIGHTS)[0]
    country = random.choices(COUNTRIES, COUNTRY_WEIGHTS)[0]

    # Mobile has higher friction (fat finger, small screen)
    friction_boost = 0.08 if device == "mobile" else 0.0

    duration = random.uniform(*arch["duration_range"])
    risk = round(random.uniform(*arch["risk_range"]), 4)
    friction = round(min(random.uniform(*arch["friction_range"]) + friction_boost, 1.0), 4)

    started = datetime.now(UTC) - timedelta(
        days=random.randint(1, 45),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
    )
    ended = started + timedelta(seconds=duration)
    page_url = f"https://test-shop.myshopify.com{random.choice(arch['pages'])}"

    return {
        "id": session_id,
        "merchant_id": MERCHANT_ID,
        "page_url": page_url,
        "started_at": started,
        "ended_at": ended,
        "outcome": arch["outcome"],
        "abandonment_risk": risk,
        "friction_score": friction,
        "intent_label": arch["intent"],
        "country_code": country,
        "device_type": device,
        "expires_at": started + timedelta(days=90),
        "_archetype": arch_name,
    }


def generate_events(session: dict, arch: dict) -> list[dict]:
    started = session["started_at"]
    ended = session["ended_at"]
    duration = (ended - started).total_seconds()
    is_purchase = session["outcome"] == "purchase"
    n_events = random.randint(*arch["event_count_range"])

    page_url = session["page_url"]
    is_checkout = any(p in page_url for p in ["/cart", "/checkout"])
    elem_pool = ELEMENTS["checkout"] if is_checkout else ELEMENTS["product"]
    elem_pool = elem_pool + ELEMENTS["navigation"]

    events = []
    for _i in range(n_events):
        t_offset = random.uniform(0, duration)
        ts = started + timedelta(seconds=t_offset)

        # Event type distribution depends on archetype
        if is_purchase:
            etype = random.choices(
                ["mouse_move", "click", "scroll", "exit_intent", "visibility"],
                [0.35, 0.35, 0.20, 0.02, 0.08],
            )[0]
        elif session["intent_label"] == "exiting":
            etype = random.choices(
                ["mouse_move", "click", "scroll", "exit_intent", "visibility"],
                [0.20, 0.25, 0.15, 0.25, 0.15],
            )[0]
        else:
            etype = random.choices(
                ["mouse_move", "click", "scroll", "exit_intent", "visibility"],
                [0.28, 0.22, 0.25, 0.12, 0.13],
            )[0]

        x, y, velocity, element_id, metadata = None, None, None, None, None

        if etype == "mouse_move":
            x = round(random.uniform(0, 1920), 1)
            y = round(random.uniform(0, 1080), 1)
            velocity = round(random.uniform(50, 2500), 1)
            # Erratic velocity for frustrated users
            if session["_archetype"] == "ui_frustrated_abandoner":
                velocity = round(random.uniform(200, 4000), 1)

        elif etype == "click":
            x = round(random.uniform(100, 1800), 1)
            y = round(random.uniform(100, 900), 1)
            velocity = round(random.uniform(0, 500), 1)
            element_id = random.choice(elem_pool)

            # Rage clicks for frustrated users
            if random.random() < arch["rage_click_prob"]:
                metadata = {
                    "rage_click": True,
                    "click_count": random.randint(3, 9),
                    "target_element": element_id,
                }

            # Price element clicks with dwell for price-shocked users
            if (
                session["_archetype"] in ("price_shock_abandoner", "loss_aversion_buyer")
                and random.random() < 0.25
            ):
                    element_id = "price-tag"
                    metadata = {"dwell_ms": random.randint(3000, 15000)}

        elif etype == "scroll":
            # Decision fatigue = lots of scroll retreats
            if session["_archetype"] == "decision_fatigue_abandoner":
                direction = random.choices(["down", "up"], [0.45, 0.55])[0]
            else:
                direction = random.choices(["down", "up"], [0.65, 0.35])[0]
            metadata = {
                "direction": direction,
                "delta": round(random.uniform(50, 800), 1),
                "viewport_pct": round(random.uniform(0, 100), 1),
            }

        elif etype == "exit_intent":
            x = round(random.uniform(0, 1920), 1)
            y = round(random.uniform(-50, 0), 1)
            triggers = ["mouse_leave", "tab_switch", "back_button"]
            # Comparison shoppers tab-switch more
            if session["_archetype"] == "comparison_shopper":
                trigger = random.choices(triggers, [0.2, 0.7, 0.1])[0]
            else:
                trigger = random.choices(triggers, [0.5, 0.3, 0.2])[0]
            metadata = {"trigger": trigger}

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


def compute_features(session: dict, arch: dict, events: list[dict]) -> dict:
    duration = (session["ended_at"] - session["started_at"]).total_seconds()

    clicks = [e for e in events if e["type"] == "click"]
    exit_intents = [e for e in events if e["type"] == "exit_intent"]
    mouse_moves = [e for e in events if e["type"] == "mouse_move"]
    scrolls = [e for e in events if e["type"] == "scroll"]

    rage_clicks = sum(
        1 for c in clicks if c.get("metadata") and c["metadata"].get("rage_click")
    )
    rage_score = round(rage_clicks / max(len(clicks), 1), 4)

    retreat_count = sum(
        1 for s in scrolls
        if s.get("metadata") and s["metadata"].get("direction") == "up"
    )

    velocities = [m["velocity"] for m in mouse_moves if m.get("velocity")]
    vel_variance = round(float(np.var(velocities)), 2) if len(velocities) > 1 else 0.0

    return {
        "session_id": session["id"],
        "hesitation_score": round(random.uniform(*arch["hesitation_range"]), 4),
        "price_dwell_time_s": round(random.uniform(*arch["price_dwell_range"]), 2),
        "rage_click_score": max(rage_score, round(random.uniform(0, arch["rage_click_prob"]), 4)),
        "scroll_retreat_count": max(retreat_count, random.randint(*arch["scroll_retreat_range"])),
        "exit_intent_count": max(len(exit_intents), random.randint(*arch["exit_intent_range"])),
        "checkout_hesitation_s": round(random.uniform(*arch["checkout_hesitation_range"]), 2),
        "velocity_variance": max(vel_variance, random.uniform(*arch["velocity_var_range"])),
        "session_duration_s": round(duration, 2),
    }


# ── Experiments with real psychology-based insights ───────────

EXPERIMENTS = [
    {
        "title": "Exit-intent discount popup vs no popup",
        "hypothesis": (
            "Loss aversion: framing discount as 'Don't lose your 15% off'"
            " will reduce exit rate more than standard 'Get 15% off'"
            " (Kahneman & Tversky, Prospect Theory)"
        ),
        "page_element": "exit-intent-modal",
        "friction_type": "abandonment_intent",
        "variant_a": "Standard popup: 'Get 15% off your order today!'",
        "variant_b": (
            "Loss-framed popup: 'Don't lose your 15% discount"
            " — it expires when you leave'"
        ),
        "result": "b_wins",
        "conversion_delta": 0.18,
        "sample_size": 2400,
        "ran_at": date(2026, 2, 15),
    },
    {
        "title": "Shipping cost reveal: cart vs checkout",
        "hypothesis": (
            "Price shock at checkout triggers loss aversion."
            " Showing shipping cost earlier (in cart) reduces sticker"
            " shock and checkout abandonment (Thaler, Mental Accounting)"
        ),
        "page_element": "shipping-cost-display",
        "friction_type": "price_shock",
        "variant_a": "Show shipping cost only at checkout/shipping step",
        "variant_b": "Show estimated shipping cost in cart alongside subtotal",
        "result": "b_wins",
        "conversion_delta": 0.22,
        "sample_size": 3100,
        "ran_at": date(2026, 2, 28),
    },
    {
        "title": "Trust badges placement on payment page",
        "hypothesis": (
            "Trust gap at payment entry can be reduced by displaying"
            " security badges near card input"
            " (McKnight et al., Trust in E-Commerce)"
        ),
        "page_element": "trust-badge",
        "friction_type": "trust_gap",
        "variant_a": "Trust badges in footer only",
        "variant_b": "Trust badges inline next to credit card form + money-back guarantee text",
        "result": "b_wins",
        "conversion_delta": 0.13,
        "sample_size": 1800,
        "ran_at": date(2026, 3, 5),
    },
    {
        "title": "Product page: review count vs star display",
        "hypothesis": (
            "Social proof (Cialdini): showing '2,847 reviews' with"
            " average stars reduces decision uncertainty"
            " more than stars alone"
        ),
        "page_element": "review-section",
        "friction_type": "decision_uncertainty",
        "variant_a": "Star rating only (4.6 stars)",
        "variant_b": "Star rating + review count + top positive snippet",
        "result": "b_wins",
        "conversion_delta": 0.14,
        "sample_size": 4200,
        "ran_at": date(2026, 3, 10),
    },
    {
        "title": "Simplify color picker from 12 to 4 options",
        "hypothesis": (
            "Choice overload (Iyengar & Lepper): reducing options"
            " from 12 colors to 4 best-sellers reduces"
            " decision fatigue"
        ),
        "page_element": "color-picker",
        "friction_type": "decision_fatigue",
        "variant_a": "Show all 12 color swatches at once",
        "variant_b": "Show top 4 colors with 'See all colors' expandable",
        "result": "b_wins",
        "conversion_delta": 0.15,
        "sample_size": 2800,
        "ran_at": date(2026, 3, 12),
    },
    {
        "title": "Mobile checkout: single page vs multi-step",
        "hypothesis": (
            "Mobile users experience higher cognitive load."
            " Single-page checkout reduces form fatigue"
            " but may overwhelm (Baumeister, Ego Depletion)"
        ),
        "page_element": "checkout-form",
        "friction_type": "decision_fatigue",
        "variant_a": "Multi-step checkout (3 screens: shipping → payment → review)",
        "variant_b": "Single scrollable checkout page with progress indicator",
        "result": "a_wins",
        "conversion_delta": -0.06,
        "sample_size": 1500,
        "ran_at": date(2026, 3, 14),
    },
    {
        "title": "Add-to-cart button: urgency text vs neutral",
        "hypothesis": (
            "Scarcity principle (Cialdini): 'Only 3 left — Add to"
            " Cart' creates urgency but may feel manipulative"
        ),
        "page_element": "add-to-cart-btn",
        "friction_type": "approach_avoidance",
        "variant_a": "Neutral: 'Add to Cart'",
        "variant_b": "Urgency: 'Only 3 left — Add to Cart'",
        "result": "inconclusive",
        "conversion_delta": 0.02,
        "sample_size": 900,
        "ran_at": date(2026, 3, 16),
    },
    {
        "title": "Live chat widget on high-friction pages",
        "hypothesis": (
            "UI frustration (Nielsen usability heuristics): proactive"
            " live chat on pages with rage clicks reduces bounce"
            " (Ceaparu et al., Frustration with Technology)"
        ),
        "page_element": "live-chat-widget",
        "friction_type": "ui_frustration",
        "variant_a": "No chat widget, standard help link in footer",
        "variant_b": "Proactive chat bubble appears after 2+ rage clicks detected",
        "result": "b_wins",
        "conversion_delta": 0.20,
        "sample_size": 1200,
        "ran_at": date(2026, 3, 18),
    },
    {
        "title": "Installment payment option visibility",
        "hypothesis": (
            "Mental accounting (Thaler): breaking $120 into"
            " '4 payments of $30' reduces perceived cost"
            " and price shock"
        ),
        "page_element": "payment-form",
        "friction_type": "price_shock",
        "variant_a": "Show total price only: '$120.00'",
        "variant_b": "Show total + installment: '$120.00 or 4x $30.00 with Shop Pay'",
        "result": "b_wins",
        "conversion_delta": 0.19,
        "sample_size": 2200,
        "ran_at": date(2026, 3, 20),
    },
    {
        "title": "Return policy prominence on product page",
        "hypothesis": (
            "Approach-avoidance conflict (Lewin): prominent"
            " '30-day free returns' near buy button"
            " reduces purchase anxiety"
        ),
        "page_element": "returns-policy",
        "friction_type": "approach_avoidance",
        "variant_a": "Return policy link in footer",
        "variant_b": "'30-day free returns' badge directly below Buy Now button",
        "result": "b_wins",
        "conversion_delta": 0.17,
        "sample_size": 3400,
        "ran_at": date(2026, 3, 21),
    },
]

# ── Intervention results ──────────────────────────────────────

INTERVENTION_TYPES = [
    ("loss_frame_discount", "converted", 0.18),
    ("loss_frame_discount", "dismissed", 0.0),
    ("loss_frame_discount", "ignored", 0.0),
    ("money_back_guarantee", "converted", 0.12),
    ("money_back_guarantee", "dismissed", 0.0),
    ("simplify_choices", "converted", 0.15),
    ("simplify_choices", "bounced", 0.0),
    ("social_proof", "converted", 0.14),
    ("social_proof", "dismissed", 0.0),
    ("social_proof", "ignored", 0.0),
    ("live_help", "converted", 0.20),
    ("live_help", "dismissed", 0.0),
    ("live_help", "bounced", 0.0),
    ("exit_discount", "converted", 0.22),
    ("exit_discount", "dismissed", 0.0),
    ("exit_discount", "ignored", 0.0),
    ("save_cart", "converted", 0.09),
    ("save_cart", "ignored", 0.0),
    ("trust_reviews", "converted", 0.16),
    ("trust_reviews", "dismissed", 0.0),
    ("value_reframe", "converted", 0.14),
    ("value_reframe", "dismissed", 0.0),
    ("installment_offer", "converted", 0.19),
    ("installment_offer", "dismissed", 0.0),
    ("faq_nudge", "converted", 0.10),
    ("faq_nudge", "ignored", 0.0),
    ("low_risk_trial", "converted", 0.17),
    ("low_risk_trial", "dismissed", 0.0),
    ("comparison_assist", "converted", 0.10),
    ("comparison_assist", "ignored", 0.0),
    ("security_badges", "converted", 0.13),
    ("security_badges", "dismissed", 0.0),
    ("review_highlight", "converted", 0.11),
    ("review_highlight", "ignored", 0.0),
    ("report_issue", "converted", 0.08),
    ("report_issue", "bounced", 0.0),
]


# ── Database insertion ────────────────────────────────────────


async def insert_batch(session: AsyncSession, table: str, rows: list[dict]) -> None:
    if not rows:
        return
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
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with factory() as db:
        # Check existing data for this merchant
        result = await db.execute(
            text("SELECT COUNT(*) FROM sessions WHERE merchant_id = :mid"),
            {"mid": MERCHANT_ID},
        )
        count = result.scalar()
        if count and count >= 100:
            print(f"Merchant already has {count} sessions. Clearing old data first...")
            await db.execute(text(
                "DELETE FROM session_features WHERE session_id IN "
                "(SELECT id FROM sessions WHERE merchant_id = :mid)"
            ), {"mid": MERCHANT_ID})
            await db.execute(text(
                "DELETE FROM events WHERE session_id IN "
                "(SELECT id FROM sessions WHERE merchant_id = :mid)"
            ), {"mid": MERCHANT_ID})
            await db.execute(text(
                "DELETE FROM intervention_results WHERE merchant_id = :mid"
            ), {"mid": MERCHANT_ID})
            await db.execute(text(
                "DELETE FROM experiments WHERE merchant_id = :mid"
            ), {"mid": MERCHANT_ID})
            await db.execute(text(
                "DELETE FROM sessions WHERE merchant_id = :mid"
            ), {"mid": MERCHANT_ID})
            await db.commit()
            print("  Cleared.")

        print(f"Seeding demo data for merchant {MERCHANT_ID}...\n")

        # ── 1. Generate sessions ────────────────────────────
        random.seed(42)
        np.random.seed(42)

        all_sessions = []
        all_events = []
        all_features = []
        archetype_counts = {}

        for _ in range(NUM_SESSIONS):
            arch_name, arch = pick_archetype()
            archetype_counts[arch_name] = archetype_counts.get(arch_name, 0) + 1

            sess = generate_session(arch_name, arch)
            events = generate_events(sess, arch)
            features = compute_features(sess, arch, events)

            # Remove internal archetype field before DB insert
            sess_db = {k: v for k, v in sess.items() if not k.startswith("_")}
            all_sessions.append(sess_db)
            all_events.extend(events)
            all_features.append(features)

        # ── 2. Insert sessions ──────────────────────────────
        print(f"  Inserting {len(all_sessions)} sessions...")
        for i in range(0, len(all_sessions), BATCH_SIZE):
            await insert_batch(db, "sessions", all_sessions[i:i + BATCH_SIZE])
            await db.commit()

        print(f"  Inserting {len(all_events)} events...")
        for i in range(0, len(all_events), BATCH_SIZE):
            await insert_batch(db, "events", all_events[i:i + BATCH_SIZE])
            await db.commit()

        print(f"  Inserting {len(all_features)} session features...")
        for i in range(0, len(all_features), BATCH_SIZE):
            await insert_batch(db, "session_features", all_features[i:i + BATCH_SIZE])
            await db.commit()

        # ── 3. Insert experiments ───────────────────────────
        print(f"  Inserting {len(EXPERIMENTS)} experiments...")
        exp_ids = []
        for exp in EXPERIMENTS:
            exp_id = uuid.uuid4()
            exp_ids.append(exp_id)
            row = {
                "id": exp_id,
                "merchant_id": MERCHANT_ID,
                "title": exp["title"],
                "hypothesis": exp["hypothesis"],
                "page_element": exp["page_element"],
                "friction_type": exp["friction_type"],
                "variant_a": exp["variant_a"],
                "variant_b": exp["variant_b"],
                "result": exp["result"],
                "conversion_delta": exp["conversion_delta"],
                "sample_size": exp["sample_size"],
                "ran_at": exp["ran_at"],
                "source": "emoratest_ml",
                "created_at": datetime.now(UTC) - timedelta(days=random.randint(1, 30)),
            }
            await insert_batch(db, "experiments", [row])
        await db.commit()

        # ── 4. Insert intervention results ──────────────────
        print("  Inserting intervention results...")
        intervention_rows = []
        # Pick sessions that had interventions (non-browsers with risk > 0.4)
        candidate_sessions = [
            s for s in all_sessions if s["abandonment_risk"] > 0.4
        ]

        for sess in random.sample(candidate_sessions, min(250, len(candidate_sessions))):
            intv = random.choice(INTERVENTION_TYPES)
            intervention_rows.append({
                "id": uuid.uuid4(),
                "merchant_id": MERCHANT_ID,
                "experiment_id": random.choice(exp_ids),
                "intervention_id": intv[0][:16],
                "triggered_at": sess["started_at"] + timedelta(seconds=random.randint(10, 120)),
                "session_id": sess["id"],
                "outcome": intv[1],
                "conversion_delta": intv[2] if intv[1] == "converted" else None,
            })

        for i in range(0, len(intervention_rows), BATCH_SIZE):
            await insert_batch(db, "intervention_results", intervention_rows[i:i + BATCH_SIZE])
        await db.commit()

        # ── 5. Summary ─────────────────────────────────────
        purchases = sum(1 for s in all_sessions if s["outcome"] == "purchase")
        abandons = len(all_sessions) - purchases
        avg_events = len(all_events) / len(all_sessions)

        print("\n== Demo Seed Complete ═══════════════════════════")
        print(f"  Sessions:       {len(all_sessions)}")
        print(f"    Purchases:    {purchases} ({purchases/len(all_sessions)*100:.1f}%)")
        print(f"    Abandons:     {abandons} ({abandons/len(all_sessions)*100:.1f}%)")
        print(f"  Events:         {len(all_events)} (avg {avg_events:.1f}/session)")
        print(f"  Features:       {len(all_features)}")
        print(f"  Experiments:    {len(EXPERIMENTS)}")
        print(f"  Interventions:  {len(intervention_rows)}")
        print("\n  Archetype breakdown:")
        for name, cnt in sorted(archetype_counts.items(), key=lambda x: -x[1]):
            pct = cnt / len(all_sessions) * 100
            print(f"    {name:30s} {cnt:4d} ({pct:5.1f}%)")
        print("═════════════════════════════════════════════════")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
