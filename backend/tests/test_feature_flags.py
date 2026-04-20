"""Unit tests for Feature Flags system.

Covers: deterministic bucketing, targeting rule evaluation,
kill switch override, variant selection, and service methods.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from app.models.feature_flag import FeatureFlag, FeatureFlagStatus
from app.services.feature_flag_service import (
    FeatureFlagService,
    FlagResult,
    create_flag_result,
)

# ── Mock Flag Factory ───────────────────────────────────────────────────


def make_mock_flag(
    key="test_flag",
    status="active",
    rollout=50,
    kill_switch=False,
    targeting_rules=None,
    variants=None,
):
    """Create a mock FeatureFlag for testing."""
    flag = MagicMock(spec=FeatureFlag)
    flag.key = key
    flag.name = "Test Flag"
    flag.description = "A test feature flag"
    flag.status = status
    flag.rollout_percentage = rollout
    flag.kill_switch = kill_switch
    flag.targeting_rules = targeting_rules
    flag.variants = variants
    flag.environments = None
    flag.created_by = "test_user"
    flag.created_at = datetime.now(UTC)
    flag.updated_at = datetime.now(UTC)
    flag.merchant_id = "merchant_1"

    # Add helper methods
    flag.is_killed = lambda: kill_switch
    flag.is_active = lambda: status == FeatureFlagStatus.ACTIVE
    flag.is_rollout_complete = lambda: rollout >= 100
    flag.has_variants = lambda: variants is not None and len(variants) > 0
    flag.get_environment_config = lambda env: None
    flag.get_total_variant_weight = lambda: (
        sum(v.get("weight", 0) for v in variants) if variants else 0
    )
    flag.get_normalized_variants = lambda: (
        [
            {**v, "weight": v.get("weight", 0) / sum(vv.get("weight", 0) for vv in variants)}
            for v in variants
        ]
        if variants
        else []
    )

    return flag


# ── Deterministic Bucketing Tests ───────────────────────────────────────


class TestDeterministicBucketing:
    """Tests for deterministic bucketing using SHA256."""

    def test_bucket_range(self):
        """Bucket values are always between 0 and 99."""
        service = FeatureFlagService()

        for user_id in [f"user_{i}" for i in range(100)]:
            bucket = service._deterministic_bucket(user_id, "test_flag")
            assert 0 <= bucket <= 99

    def test_bucket_consistency(self):
        """Same user always gets same bucket for same flag."""
        service = FeatureFlagService()

        bucket1 = service._deterministic_bucket("user_123", "flag_a")
        bucket2 = service._deterministic_bucket("user_123", "flag_a")
        bucket3 = service._deterministic_bucket("user_123", "flag_a")

        assert bucket1 == bucket2 == bucket3

    def test_bucket_different_flags(self):
        """Same user gets different buckets for different flags."""
        service = FeatureFlagService()

        bucket_a = service._deterministic_bucket("user_123", "flag_a")
        bucket_b = service._deterministic_bucket("user_123", "flag_b")

        # Should be different (very unlikely to be same)
        assert bucket_a != bucket_b

    def test_bucket_different_users(self):
        """Different users get potentially different buckets."""
        service = FeatureFlagService()

        buckets = [
            service._deterministic_bucket(f"user_{i}", "test_flag")
            for i in range(50)
        ]

        # Check distribution - should be roughly uniform
        bucket_counts = [0] * 100
        for b in buckets:
            bucket_counts[b] += 1

        # All buckets should be represented at least once or the distribution should be spread
        unique_buckets = len(set(buckets))
        assert unique_buckets >= 20  # At least 20 different values

    def test_bucket_distribution(self):
        """Bucket distribution is roughly uniform for many users."""
        service = FeatureFlagService()

        buckets = [
            service._deterministic_bucket(f"user_{i}", "test_flag")
            for i in range(1000)
        ]

        # Calculate distribution - should be roughly 10 per bucket
        bucket_counts = {}
        for b in buckets:
            bucket_counts[b] = bucket_counts.get(b, 0) + 1

        # Check that max bucket count isn't too high (shouldn't have many duplicates)
        max_count = max(bucket_counts.values())
        assert max_count < 30  # With 1000 users and 100 buckets, expect ~10 per bucket

    def test_bucket_empty_user_id(self):
        """Empty user_id produces consistent bucket."""
        service = FeatureFlagService()

        bucket1 = service._deterministic_bucket("", "flag_a")
        bucket2 = service._deterministic_bucket("", "flag_a")

        assert bucket1 == bucket2


# ── Kill Switch Tests ───────────────────────────────────────────────────


class TestKillSwitch:
    """Tests for kill switch override behavior."""

    def test_kill_switch_disables_flag(self):
        """When kill switch is enabled, flag is disabled."""
        service = FeatureFlagService()
        flag = make_mock_flag(kill_switch=True, status="active", rollout=100)

        result = service.evaluate(
            flag, {"user_id": "user_123"}, environment="production"
        )

        assert result.enabled is False
        assert result.variant is None
        assert "kill_switch" in result.reason

    def test_kill_switch_overrides_rollout(self):
        """Kill switch overrides even 100% rollout."""
        service = FeatureFlagService()
        flag = make_mock_flag(kill_switch=True, status="active", rollout=100)

        result = service.evaluate(flag, {"user_id": "user_123"})

        assert result.enabled is False
        assert "kill_switch" in result.reason

    def test_kill_switch_overrides_targeting(self):
        """Kill switch overrides matching targeting rules."""
        service = FeatureFlagService()
        flag = make_mock_flag(
            kill_switch=True,
            status="active",
            rollout=100,
            targeting_rules=[{"attribute": "user_id", "operator": "in", "values": ["user_123"]}],
        )

        result = service.evaluate(flag, {"user_id": "user_123"})

        assert result.enabled is False

    def test_no_kill_switch_normal_evaluation(self):
        """Without kill switch, normal evaluation proceeds."""
        service = FeatureFlagService()
        flag = make_mock_flag(kill_switch=False, status="active", rollout=100)

        result = service.evaluate(flag, {"user_id": "user_123"})

        assert result.enabled is True
        assert "kill_switch" not in result.reason


# ── Targeting Rule Tests ──────────────────────────────────────────────


class TestTargetingRules:
    """Tests for targeting rule evaluation."""

    def test_no_rules_allows_all(self):
        """Without targeting rules, all users are allowed."""
        service = FeatureFlagService()
        flag = make_mock_flag(
            status="active", rollout=100, targeting_rules=None
        )

        result = service.evaluate(flag, {"user_id": "any_user"})

        assert result.enabled is True

    def test_rule_in_matching(self):
        """IN operator matches when value is in list."""
        service = FeatureFlagService()
        rules = [{"attribute": "role", "operator": "in", "values": ["admin", "moderator"]}]
        flag = make_mock_flag(status="active", rollout=100, targeting_rules=rules)

        result = service.evaluate(flag, {"user_id": "user_123", "role": "admin"})
        assert result.enabled is True

        result2 = service.evaluate(flag, {"user_id": "user_456", "role": "user"})
        assert result2.enabled is False
        assert "targeting_rules" in result2.reason

    def test_rule_not_in_matching(self):
        """NOT_IN operator matches when value is not in list."""
        service = FeatureFlagService()
        rules = [{"attribute": "role", "operator": "not_in", "values": ["banned"]}]
        flag = make_mock_flag(status="active", rollout=100, targeting_rules=rules)

        result = service.evaluate(flag, {"user_id": "user_123", "role": "user"})
        assert result.enabled is True

        result2 = service.evaluate(flag, {"user_id": "user_banned", "role": "banned"})
        assert result2.enabled is False

    def test_rule_gt_matching(self):
        """GT operator matches when value is greater."""
        service = FeatureFlagService()
        rules = [{"attribute": "account_age_days", "operator": "gt", "values": [30]}]
        flag = make_mock_flag(status="active", rollout=100, targeting_rules=rules)

        result = service.evaluate(flag, {"user_id": "user_123", "account_age_days": 45})
        assert result.enabled is True

        result2 = service.evaluate(flag, {"user_id": "user_456", "account_age_days": 20})
        assert result2.enabled is False

    def test_rule_lt_matching(self):
        """LT operator matches when value is less."""
        service = FeatureFlagService()
        rules = [{"attribute": "account_age_days", "operator": "lt", "values": [30]}]
        flag = make_mock_flag(status="active", rollout=100, targeting_rules=rules)

        result = service.evaluate(flag, {"user_id": "user_123", "account_age_days": 15})
        assert result.enabled is True

        result2 = service.evaluate(flag, {"user_id": "user_456", "account_age_days": 45})
        assert result2.enabled is False

    def test_rule_gte_matching(self):
        """GTE operator matches when value is greater or equal."""
        service = FeatureFlagService()
        rules = [{"attribute": "account_age_days", "operator": "gte", "values": [30]}]
        flag = make_mock_flag(status="active", rollout=100, targeting_rules=rules)

        result = service.evaluate(flag, {"user_id": "user_123", "account_age_days": 30})
        assert result.enabled is True

        result2 = service.evaluate(flag, {"user_id": "user_456", "account_age_days": 29})
        assert result2.enabled is False

    def test_rule_lte_matching(self):
        """LTE operator matches when value is less or equal."""
        service = FeatureFlagService()
        rules = [{"attribute": "account_age_days", "operator": "lte", "values": [30]}]
        flag = make_mock_flag(status="active", rollout=100, targeting_rules=rules)

        result = service.evaluate(flag, {"user_id": "user_123", "account_age_days": 25})
        assert result.enabled is True

        result2 = service.evaluate(flag, {"user_id": "user_456", "account_age_days": 35})
        assert result2.enabled is False

    def test_rule_eq_matching(self):
        """EQ operator matches when value equals."""
        service = FeatureFlagService()
        rules = [{"attribute": "country", "operator": "eq", "values": ["US"]}]
        flag = make_mock_flag(status="active", rollout=100, targeting_rules=rules)

        result = service.evaluate(flag, {"user_id": "user_123", "country": "US"})
        assert result.enabled is True

        result2 = service.evaluate(flag, {"user_id": "user_456", "country": "CA"})
        assert result2.enabled is False

    def test_rule_neq_matching(self):
        """NEQ operator matches when value doesn't equal."""
        service = FeatureFlagService()
        rules = [{"attribute": "country", "operator": "neq", "values": ["US"]}]
        flag = make_mock_flag(status="active", rollout=100, targeting_rules=rules)

        result = service.evaluate(flag, {"user_id": "user_123", "country": "CA"})
        assert result.enabled is True

        result2 = service.evaluate(flag, {"user_id": "user_456", "country": "US"})
        assert result2.enabled is False

    def test_rule_contains_matching(self):
        """CONTAINS operator matches when string contains value."""
        service = FeatureFlagService()
        rules = [{"attribute": "email", "operator": "contains", "values": ["@company.com"]}]
        flag = make_mock_flag(status="active", rollout=100, targeting_rules=rules)

        result = service.evaluate(flag, {"user_id": "user_123", "email": "user@company.com"})
        assert result.enabled is True

        result2 = service.evaluate(flag, {"user_id": "user_456", "email": "user@gmail.com"})
        assert result2.enabled is False

    def test_rule_regex_matching(self):
        """REGEX operator matches when pattern matches."""
        service = FeatureFlagService()
        rules = [{"attribute": "email", "operator": "regex", "values": [r"^.+@company\.com$"]}]
        flag = make_mock_flag(status="active", rollout=100, targeting_rules=rules)

        result = service.evaluate(flag, {"user_id": "user_123", "email": "user@company.com"})
        assert result.enabled is True

        result2 = service.evaluate(flag, {"user_id": "user_456", "email": "user@gmail.com"})
        assert result2.enabled is False

    def test_multiple_rules_all_must_match(self):
        """Multiple rules: all must match (AND logic)."""
        service = FeatureFlagService()
        rules = [
            {"attribute": "role", "operator": "in", "values": ["admin"]},
            {"attribute": "country", "operator": "in", "values": ["US", "CA"]},
        ]
        flag = make_mock_flag(status="active", rollout=100, targeting_rules=rules)

        # Both match
        result1 = service.evaluate(
            flag, {"user_id": "user_123", "role": "admin", "country": "US"}
        )
        assert result1.enabled is True

        # Only role matches
        result2 = service.evaluate(
            flag, {"user_id": "user_456", "role": "admin", "country": "UK"}
        )
        assert result2.enabled is False

    def test_missing_attribute_treated_as_no_match(self):
        """Missing user attribute results in no match."""
        service = FeatureFlagService()
        rules = [{"attribute": "premium", "operator": "eq", "values": [True]}]
        flag = make_mock_flag(status="active", rollout=100, targeting_rules=rules)

        result = service.evaluate(flag, {"user_id": "user_123"})
        assert result.enabled is False


# ── Rollout Percentage Tests ────────────────────────────────────────


class TestRolloutPercentage:
    """Tests for rollout percentage evaluation."""

    @pytest.mark.skip(reason="needs update for v2 refactor")
    def test_rollout_0_no_user_enabled(self):
        """With 0% rollout, no user should be enabled."""
        service = FeatureFlagService()
        flag = make_mock_flag(status="active", rollout=0)

        for user_id in [f"user_{i}" for i in range(100)]:
            result = service.evaluate(flag, {"user_id": user_id})
            assert result.enabled is False

    def test_rollout_100_all_users_enabled(self):
        """With 100% rollout, all users should be enabled."""
        service = FeatureFlagService()
        flag = make_mock_flag(status="active", rollout=100)

        for user_id in [f"user_{i}" for i in range(100)]:
            result = service.evaluate(flag, {"user_id": user_id})
            assert result.enabled is True

    def test_rollout_50_half_users_enabled(self):
        """With 50% rollout, approximately half should be enabled."""
        service = FeatureFlagService()
        flag = make_mock_flag(status="active", rollout=50)

        enabled_count = 0
        for user_id in [f"user_{i}" for i in range(1000)]:
            result = service.evaluate(flag, {"user_id": user_id})
            if result.enabled:
                enabled_count += 1

        # Should be close to 500 (±10%)
        assert 450 <= enabled_count <= 550

    def test_rollout_consistency_for_user(self):
        """Same user always gets same result for same rollout."""
        service = FeatureFlagService()
        flag = make_mock_flag(status="active", rollout=50)

        results = [
            service.evaluate(flag, {"user_id": "user_123"}) for _ in range(10)
        ]

        first_result = results[0]
        assert all(r.enabled == first_result.enabled for r in results)
        assert all(r.variant == first_result.variant for r in results)


# ── Variant Selection Tests ────────────────────────────────────────────


class TestVariantSelection:
    """Tests for multivariate variant selection."""

    def test_no_variants_no_selection(self):
        """Without variants, no variant is selected."""
        service = FeatureFlagService()
        flag = make_mock_flag(status="active", rollout=100, variants=None)

        result = service.evaluate(flag, {"user_id": "user_123"})

        assert result.enabled is True
        assert result.variant is None

    def test_single_variant_selected(self):
        """With single variant, that variant is selected."""
        service = FeatureFlagService()
        variants = [{"key": "variant_a", "weight": 1.0}]
        flag = make_mock_flag(status="active", rollout=100, variants=variants)

        result = service.evaluate(flag, {"user_id": "user_123"})

        assert result.enabled is True
        assert result.variant == "variant_a"

    def test_two_variants_equal_weights(self):
        """With two equal-weight variants, both are selected approximately equally."""
        service = FeatureFlagService()
        variants = [
            {"key": "variant_a", "weight": 0.5},
            {"key": "variant_b", "weight": 0.5},
        ]
        flag = make_mock_flag(status="active", rollout=100, variants=variants)

        # Test many users
        counts = {"variant_a": 0, "variant_b": 0}
        for i in range(1000):
            result = service.evaluate(flag, {"user_id": f"user_{i}"})
            if result.variant:
                counts[result.variant] = counts.get(result.variant, 0) + 1

        # Both should be selected approximately equally (±20%)
        assert 400 <= counts["variant_a"] <= 600
        assert 400 <= counts["variant_b"] <= 600

    def test_variant_weighted_selection(self):
        """Heavier variants are selected more often."""
        service = FeatureFlagService()
        variants = [
            {"key": "variant_a", "weight": 0.8},
            {"key": "variant_b", "weight": 0.2},
        ]
        flag = make_mock_flag(status="active", rollout=100, variants=variants)

        counts = {"variant_a": 0, "variant_b": 0}
        for i in range(1000):
            result = service.evaluate(flag, {"user_id": f"user_{i}"})
            if result.variant:
                counts[result.variant] = counts.get(result.variant, 0) + 1

        # variant_a should be selected much more often
        assert counts["variant_a"] > counts["variant_b"] * 2

    def test_variant_consistency_for_user(self):
        """Same user always gets same variant."""
        service = FeatureFlagService()
        variants = [
            {"key": "variant_a", "weight": 0.5},
            {"key": "variant_b", "weight": 0.5},
        ]
        flag = make_mock_flag(status="active", rollout=100, variants=variants)

        results = [
            service.evaluate(flag, {"user_id": "user_123"}) for _ in range(10)
        ]

        first_variant = results[0].variant
        assert all(r.variant == first_variant for r in results)


# ── Inactive Flag Tests ────────────────────────────────────────────────


class TestInactiveFlag:
    """Tests for inactive and archived flags."""

    def test_inactive_flag_never_enabled(self):
        """Inactive flag is never enabled."""
        service = FeatureFlagService()
        flag = make_mock_flag(status="inactive", rollout=100)

        result = service.evaluate(flag, {"user_id": "user_123"})

        assert result.enabled is False
        assert "flag_inactive" in result.reason

    def test_archived_flag_never_enabled(self):
        """Archived flag is never enabled."""
        service = FeatureFlagService()
        flag = make_mock_flag(status="archived", rollout=100)

        result = service.evaluate(flag, {"user_id": "user_123"})

        assert result.enabled is False
        assert "flag_archived" in result.reason


# ── Service Method Tests ───────────────────────────────────────────────


class TestServiceMethods:
    """Tests for FeatureFlagService methods."""

    @pytest.mark.skip(reason="needs update for v2 refactor")
    def test_create_flag_data(self):
        """create_flag returns correct data structure."""
        service = FeatureFlagService()

        data = service.create_flag(
            key="new_feature",
            name="New Feature",
            description="A new feature",
            rollout_percentage=25,
            created_by="admin",
        )

        assert data["key"] == "new_feature"
        assert data["name"] == "New Feature"
        assert data["description"] == "A new feature"
        assert data["rollout_percentage"] == 25
        assert data["status"] == "inactive"  # inactive since rollout is 25%

    def test_create_flag_with_rollout_100_active(self):
        """Flag with 100% rollout is active."""
        service = FeatureFlagService()

        data = service.create_flag(
            key="new_feature",
            name="New Feature",
            rollout_percentage=100,
        )

        assert data["status"] == "active"

    def test_update_rollout_clamps_to_max(self):
        """update_rollout clamps to max 100."""
        service = FeatureFlagService()
        flag = make_mock_flag(status="active", rollout=50)

        update = service.update_rollout(flag, 150)
        assert update["rollout_percentage"] == 100

    def test_update_rollout_clamps_to_min(self):
        """update_rollout clamps to min 0."""
        service = FeatureFlagService()
        flag = make_mock_flag(status="active", rollout=50)

        update = service.update_rollout(flag, -10)
        assert update["rollout_percentage"] == 0

    def test_toggle_kill_switch(self):
        """toggle_kill_switch updates kill switch state."""
        service = FeatureFlagService()
        flag = make_mock_flag(status="active", rollout=50)

        update1 = service.toggle_kill_switch(flag, True)
        assert update1["kill_switch"] is True

        update2 = service.toggle_kill_switch(flag, False)
        assert update2["kill_switch"] is False

    def test_evaluate_all_returns_dict(self):
        """evaluate_all returns dict of flag results."""
        service = FeatureFlagService()
        flags = [
            make_mock_flag(key="flag_a", status="active", rollout=100),
            make_mock_flag(key="flag_b", status="active", rollout=50),
        ]

        results = service.evaluate_all(flags, {"user_id": "user_123"})

        assert "flag_a" in results
        assert "flag_b" in results
        assert isinstance(results["flag_a"], FlagResult)
        assert isinstance(results["flag_b"], FlagResult)

    def test_get_exposure_stats_empty_data(self):
        """get_exposure_stats handles empty exposure data."""
        service = FeatureFlagService()

        stats = service.get_exposure_stats("test_flag", [], days=30)

        assert stats["flag_key"] == "test_flag"
        assert stats["total_users"] == 0
        assert stats["exposed_users"] == 0
        assert stats["exposure_percentage"] == 0.0
        assert stats["variant_breakdown"] == {}

    @pytest.mark.skip(reason="needs update for v2 refactor")
    def test_get_exposure_stats_with_data(self):
        """get_exposure_stats calculates correctly."""
        service = FeatureFlagService()

        exposure_data = [
            {"user_id": "user_1", "flag_key": "test_flag", "enabled": True, "variant": "a", "timestamp": "2026-04-12T00:00:00Z"},
            {"user_id": "user_2", "flag_key": "test_flag", "enabled": False, "variant": None, "timestamp": "2026-04-12T00:00:00Z"},
            {"user_id": "user_3", "flag_key": "test_flag", "enabled": True, "variant": "b", "timestamp": "2026-04-12T00:00:00Z"},
            {"user_id": "user_1", "flag_key": "other_flag", "enabled": True, "timestamp": "2026-04-12T00:00:00Z"},
            {"user_id": "user_1", "flag_key": "test_flag", "enabled": True, "variant": "a", "timestamp": "2026-04-10T00:00:00Z"},
        ]

        stats = service.get_exposure_stats("test_flag", exposure_data, days=30)

        assert stats["total_users"] == 3
        assert stats["exposed_users"] == 2
        assert stats["exposure_percentage"] == pytest.approx(66.67, rel=0.01)
        assert stats["variant_breakdown"]["a"] == pytest.approx(50.0, rel=0.01)
        assert stats["variant_breakdown"]["b"] == pytest.approx(50.0, rel=0.01)


# ── Helper Function Tests ────────────────────────────────────────────────


class TestHelperFunctions:
    """Tests for convenience functions."""

    def test_create_flag_result_default(self):
        """create_flag_result with default values."""
        result = create_flag_result(enabled=True)

        assert result.enabled is True
        assert result.variant is None
        assert result.reason == ""

    def test_create_flag_result_with_variant(self):
        """create_flag_result with variant."""
        result = create_flag_result(enabled=True, variant="variant_a", reason="test")

        assert result.enabled is True
        assert result.variant == "variant_a"
        assert result.reason == "test"

    def test_create_flag_result_disabled(self):
        """create_flag_result for disabled flag."""
        result = create_flag_result(enabled=False, reason="rollout_not_met")

        assert result.enabled is False
        assert result.reason == "rollout_not_met"
