"""Unit tests for feature extraction functions (CONV-17)."""

from datetime import UTC, datetime, timedelta

import pytest

from src.features.extraction import (
    checkout_hesitation_s,
    exit_intent_count,
    extract_features,
    hesitation_score,
    price_dwell_time_s,
    rage_click_score,
    scroll_retreat_count,
    session_duration_s,
    velocity_variance,
)

# ── Helpers ──────────────────────────────────────────────────

NOW = datetime(2026, 3, 18, 12, 0, 0, tzinfo=UTC)


def _evt(type_: str, offset_s: float, **kwargs) -> dict:
    """Create an event dict at NOW + offset_s seconds."""
    return {
        "type": type_,
        "ts": NOW + timedelta(seconds=offset_s),
        "x": kwargs.get("x"),
        "y": kwargs.get("y"),
        "velocity": kwargs.get("velocity"),
        "element_id": kwargs.get("element_id"),
        "metadata": kwargs.get("metadata"),
    }


# ── session_duration_s ──────────────────────────────────────


class TestSessionDuration:
    def test_normal_duration(self):
        result = session_duration_s(NOW, NOW + timedelta(seconds=120))
        assert result == 120.0

    def test_zero_duration(self):
        assert session_duration_s(NOW, NOW) == 0.0

    def test_none_ended_at(self):
        assert session_duration_s(NOW, None) == 0.0

    def test_negative_clamps_to_zero(self):
        assert session_duration_s(NOW, NOW - timedelta(seconds=10)) == 0.0


# ── hesitation_score ─────────────────────────────────────────


class TestHesitationScore:
    def test_no_events(self):
        assert hesitation_score([]) == 0.0

    def test_no_clicks(self):
        events = [_evt("mouse_move", 0, x=100, y=100)]
        assert hesitation_score(events) == 0.0

    def test_no_mouse_moves(self):
        events = [_evt("click", 0, x=100, y=100, element_id="btn")]
        assert hesitation_score(events) == 0.0

    def test_short_hesitation(self):
        events = [
            _evt("mouse_move", 0, x=100, y=100),
            _evt("click", 1, x=100, y=100, element_id="btn"),
        ]
        score = hesitation_score(events)
        # 1s gap / 30s max = ~0.033
        assert 0.03 <= score <= 0.04

    def test_long_hesitation_capped_at_1(self):
        events = [
            _evt("mouse_move", 0, x=100, y=100),
            _evt("click", 60, x=100, y=100, element_id="btn"),
        ]
        assert hesitation_score(events) == 1.0

    def test_multiple_clicks_averaged(self):
        events = [
            _evt("mouse_move", 0, x=100, y=100),
            _evt("click", 3, x=100, y=100, element_id="btn1"),
            _evt("mouse_move", 5, x=200, y=200),
            _evt("click", 8, x=200, y=200, element_id="btn2"),
        ]
        score = hesitation_score(events)
        # avg gap = 3s, 3/30 = 0.1
        assert score == pytest.approx(0.1, abs=0.01)


# ── price_dwell_time_s ──────────────────────────────────────


class TestPriceDwellTime:
    def test_no_price_events(self):
        events = [_evt("click", 0, element_id="add-to-cart")]
        assert price_dwell_time_s(events) == 0.0

    def test_single_price_event(self):
        events = [_evt("click", 0, element_id="price-tag")]
        assert price_dwell_time_s(events) == 0.0

    def test_consecutive_price_events(self):
        events = [
            _evt("click", 0, element_id="price-tag"),
            _evt("mouse_move", 5, element_id="price-display"),
            _evt("click", 10, element_id="total-amount"),
        ]
        assert price_dwell_time_s(events) == 10.0

    def test_long_gap_excluded(self):
        events = [
            _evt("click", 0, element_id="price-tag"),
            _evt("click", 60, element_id="total-cost"),
        ]
        # 60s gap > 30s threshold, excluded
        assert price_dwell_time_s(events) == 0.0

    def test_mixed_events(self):
        events = [
            _evt("click", 0, element_id="price-tag"),
            _evt("click", 2, element_id="navbar"),  # not price-related
            _evt("click", 5, element_id="subtotal-display"),
        ]
        # Only price events: 0s and 5s, gap = 5s
        assert price_dwell_time_s(events) == 5.0


# ── rage_click_score ─────────────────────────────────────────


class TestRageClickScore:
    def test_no_clicks(self):
        assert rage_click_score([]) == 0.0

    def test_fewer_than_3_clicks(self):
        events = [
            _evt("click", 0, x=100, y=100),
            _evt("click", 0.5, x=100, y=100),
        ]
        assert rage_click_score(events) == 0.0

    def test_rage_cluster_detected(self):
        events = [
            _evt("click", 0, x=100, y=100),
            _evt("click", 0.3, x=110, y=105),
            _evt("click", 0.6, x=95, y=110),
        ]
        score = rage_click_score(events)
        assert score > 0.0

    def test_spread_clicks_no_rage(self):
        events = [
            _evt("click", 0, x=100, y=100),
            _evt("click", 5, x=500, y=500),  # far away + slow
            _evt("click", 10, x=900, y=900),
        ]
        score = rage_click_score(events)
        assert score == 0.0

    def test_mixed_clusters(self):
        events = [
            # Rage cluster: 3 clicks in 1s within 50px
            _evt("click", 0, x=100, y=100),
            _evt("click", 0.3, x=110, y=105),
            _evt("click", 0.6, x=95, y=110),
            # Normal click: far away and later
            _evt("click", 10, x=800, y=800),
        ]
        score = rage_click_score(events)
        assert 0.0 < score < 1.0


# ── scroll_retreat_count ─────────────────────────────────────


class TestScrollRetreatCount:
    def test_no_scrolls(self):
        assert scroll_retreat_count([]) == 0

    def test_only_down_scrolls(self):
        events = [
            _evt("scroll", 0, metadata={"direction": "down"}),
            _evt("scroll", 1, metadata={"direction": "down"}),
        ]
        assert scroll_retreat_count(events) == 0

    def test_single_retreat(self):
        events = [
            _evt("scroll", 0, metadata={"direction": "down"}),
            _evt("scroll", 1, metadata={"direction": "up"}),
        ]
        assert scroll_retreat_count(events) == 1

    def test_multiple_retreats(self):
        events = [
            _evt("scroll", 0, metadata={"direction": "down"}),
            _evt("scroll", 1, metadata={"direction": "up"}),
            _evt("scroll", 2, metadata={"direction": "down"}),
            _evt("scroll", 3, metadata={"direction": "up"}),
        ]
        assert scroll_retreat_count(events) == 2

    def test_consecutive_ups_count_once(self):
        events = [
            _evt("scroll", 0, metadata={"direction": "down"}),
            _evt("scroll", 1, metadata={"direction": "up"}),
            _evt("scroll", 2, metadata={"direction": "up"}),
        ]
        assert scroll_retreat_count(events) == 1


# ── exit_intent_count ────────────────────────────────────────


class TestExitIntentCount:
    def test_no_exit_intents(self):
        events = [_evt("click", 0, x=100, y=100)]
        assert exit_intent_count(events) == 0

    def test_counts_exit_intents(self):
        events = [
            _evt("exit_intent", 0, x=500, y=-10),
            _evt("click", 1, x=100, y=100),
            _evt("exit_intent", 5, x=400, y=-5),
            _evt("exit_intent", 8, x=300, y=-20),
        ]
        assert exit_intent_count(events) == 3


# ── checkout_hesitation_s ────────────────────────────────────


class TestCheckoutHesitation:
    def test_no_checkout_events(self):
        events = [_evt("click", 0, element_id="navbar")]
        assert checkout_hesitation_s(events) == 0.0

    def test_single_checkout_event(self):
        events = [_evt("click", 0, element_id="checkout-btn")]
        assert checkout_hesitation_s(events) == 0.0

    def test_quick_interaction_not_counted(self):
        events = [
            _evt("click", 0, element_id="checkout-btn"),
            _evt("click", 2, element_id="payment-form"),
        ]
        # 2s gap < 3s threshold
        assert checkout_hesitation_s(events) == 0.0

    def test_hesitation_detected(self):
        events = [
            _evt("click", 0, element_id="checkout-btn"),
            _evt("click", 10, element_id="payment-form"),
        ]
        # 10s gap > 3s
        assert checkout_hesitation_s(events) == 10.0

    def test_long_gap_capped_at_60(self):
        events = [
            _evt("click", 0, element_id="checkout-btn"),
            _evt("click", 120, element_id="shipping-form"),
        ]
        assert checkout_hesitation_s(events) == 60.0

    def test_multiple_hesitations_summed(self):
        events = [
            _evt("click", 0, element_id="checkout-btn"),
            _evt("click", 5, element_id="payment-form"),  # 5s gap
            _evt("click", 15, element_id="submit-order"),  # 10s gap
        ]
        assert checkout_hesitation_s(events) == 15.0


# ── velocity_variance ────────────────────────────────────────


class TestVelocityVariance:
    def test_no_mouse_moves(self):
        assert velocity_variance([]) == 0.0

    def test_single_move(self):
        events = [_evt("mouse_move", 0, velocity=100.0)]
        assert velocity_variance(events) == 0.0

    def test_constant_velocity(self):
        events = [
            _evt("mouse_move", 0, velocity=100.0),
            _evt("mouse_move", 1, velocity=100.0),
            _evt("mouse_move", 2, velocity=100.0),
        ]
        assert velocity_variance(events) == 0.0

    def test_varying_velocity(self):
        events = [
            _evt("mouse_move", 0, velocity=100.0),
            _evt("mouse_move", 1, velocity=300.0),
        ]
        result = velocity_variance(events)
        # var([100, 300]) = 10000
        assert result == 10000.0

    def test_ignores_non_mouse_events(self):
        events = [
            _evt("mouse_move", 0, velocity=100.0),
            _evt("click", 1, velocity=500.0),
            _evt("mouse_move", 2, velocity=100.0),
        ]
        assert velocity_variance(events) == 0.0


# ── extract_features (integration) ──────────────────────────


class TestExtractFeatures:
    def test_returns_all_8_keys(self):
        events = [
            _evt("mouse_move", 0, x=100, y=100, velocity=50.0),
            _evt("click", 2, x=100, y=100, element_id="price-tag"),
            _evt("scroll", 3, metadata={"direction": "down"}),
            _evt("scroll", 4, metadata={"direction": "up"}),
            _evt("exit_intent", 5, x=500, y=-10),
        ]
        ended = NOW + timedelta(seconds=60)
        result = extract_features(events, NOW, ended)

        expected_keys = {
            "hesitation_score",
            "price_dwell_time_s",
            "rage_click_score",
            "scroll_retreat_count",
            "exit_intent_count",
            "checkout_hesitation_s",
            "velocity_variance",
            "session_duration_s",
        }
        assert set(result.keys()) == expected_keys

    def test_session_duration_populated(self):
        result = extract_features([], NOW, NOW + timedelta(seconds=300))
        assert result["session_duration_s"] == 300.0

    def test_empty_events(self):
        result = extract_features([], NOW, NOW + timedelta(seconds=10))
        assert result["hesitation_score"] == 0.0
        assert result["rage_click_score"] == 0.0
        assert result["scroll_retreat_count"] == 0
        assert result["exit_intent_count"] == 0
        assert result["velocity_variance"] == 0.0
        assert result["session_duration_s"] == 10.0
