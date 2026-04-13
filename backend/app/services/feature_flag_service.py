"""Feature flag service for progressive rollouts and kill switches.

Provides evaluation logic with targeting rules, deterministic bucketing,
and multivariate variant selection.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.models.feature_flag import FeatureFlag


# ── Enums & Data Classes ────────────────────────────────────────────────


class RuleOperator(str, Enum):
    """Operators for targeting rule evaluation."""

    IN = "in"
    NOT_IN = "not_in"
    GT = "gt"
    LT = "lt"
    GTE = "gte"
    LTE = "lte"
    EQ = "eq"
    NEQ = "neq"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    REGEX = "regex"
    NOT_REGEX = "not_regex"


@dataclass
class FlagResult:
    """Result of evaluating a feature flag for a user context."""

    enabled: bool
    variant: str | None = None
    reason: str = ""
    flag_key: str = ""


# ── Feature Flag Service ───────────────────────────────────────────────────


class FeatureFlagService:
    """Service for evaluating feature flags with targeting and rollout.

    Evaluation order:
    1. Kill switch check (if killed, always returns False)
    2. Environment override (if environment-specific config exists)
    3. Targeting rules (user attributes vs. rule conditions)
    4. Rollout percentage (deterministic hashing)
    5. Variant selection (for multivariate flags)
    """

    def __init__(self):
        """Initialize feature flag service."""
        pass

    def evaluate(
        self,
        flag: FeatureFlag,
        user_context: dict[str, Any],
        environment: str = "production",
    ) -> FlagResult:
        """Evaluate a feature flag for a specific user context.

        Args:
            flag: FeatureFlag to evaluate.
            user_context: User attributes for targeting (e.g., user_id, email, role).
            environment: Environment name (default "production").

        Returns:
            FlagResult with enabled status, variant, and reason.
        """
        result = FlagResult(enabled=False, flag_key=flag.key)

        # 1. Kill switch check
        if flag.is_killed():
            result.reason = "kill_switch_enabled"
            return result

        # 2. Status check
        if not flag.is_active():
            result.reason = f"flag_{flag.status}"
            return result

        # 3. Environment override
        env_config = flag.get_environment_config(environment)
        if env_config:
            result.enabled = env_config.get("enabled", False)
            result.variant = env_config.get("variant")
            result.reason = "environment_override"
            return result

        # 4. Targeting rules
        if flag.targeting_rules:
            if not self._evaluate_targeting_rules(flag.targeting_rules, user_context):
                result.reason = "targeting_rules_not_matched"
                return result

        # 5. Rollout percentage
        user_id = user_context.get("user_id", "")
        bucket = self._deterministic_bucket(user_id, flag.key)

        if bucket > flag.rollout_percentage:
            result.reason = f"rollout_percentage_not_met ({bucket} > {flag.rollout_percentage})"
            return result

        # 6. Enabled - check for variants
        result.enabled = True
        result.reason = f"rollout_bucket_met ({bucket} <= {flag.rollout_percentage})"

        if flag.has_variants():
            selected_variant = self._select_variant(flag, bucket)
            result.variant = selected_variant
            result.reason += f" | variant: {selected_variant}"

        return result

    def evaluate_all(
        self,
        flags: list[FeatureFlag],
        user_context: dict[str, Any],
        environment: str = "production",
    ) -> dict[str, FlagResult]:
        """Evaluate all flags for a user context.

        Args:
            flags: List of FeatureFlag objects.
            user_context: User attributes for targeting.
            environment: Environment name.

        Returns:
            Dict mapping flag_key to FlagResult.
        """
        results = {}
        for flag in flags:
            results[flag.key] = self.evaluate(flag, user_context, environment)
        return results

    def create_flag(
        self,
        key: str,
        name: str,
        merchant_id: str | None = None,
        description: str | None = None,
        rollout_percentage: float = 0.0,
        targeting_rules: list[dict] | None = None,
        variants: list[dict] | None = None,
        kill_switch: bool = False,
        environments: dict | None = None,
        created_by: str | None = None,
    ) -> dict:
        """Create a feature flag data dictionary.

        Args:
            key: Unique slug for the flag.
            name: Human-readable name.
            merchant_id: Owner merchant ID.
            description: Flag description.
            rollout_percentage: Initial rollout (0-100).
            targeting_rules: List of targeting rule objects.
            variants: Multivariate variant configurations.
            kill_switch: Initial kill switch state.
            environments: Environment-specific overrides.
            created_by: Creator identifier.

        Returns:
            Dict with flag data for model creation.
        """
        return {
            "key": key,
            "name": name,
            "description": description,
            "status": "active" if rollout_percentage > 0 or kill_switch else "inactive",
            "rollout_percentage": rollout_percentage,
            "targeting_rules": targeting_rules,
            "variants": variants,
            "kill_switch": kill_switch,
            "environments": environments,
            "created_by": created_by,
        }

    def update_rollout(
        self,
        flag: FeatureFlag,
        percentage: float,
    ) -> dict:
        """Update rollout percentage for a flag.

        Args:
            flag: FeatureFlag to update.
            percentage: New rollout percentage (0-100).

        Returns:
            Dict with update data.
        """
        return {
            "rollout_percentage": max(0.0, min(100.0, percentage)),
        }

    def toggle_kill_switch(
        self,
        flag: FeatureFlag,
        enabled: bool,
    ) -> dict:
        """Toggle kill switch for a flag.

        Args:
            flag: FeatureFlag to update.
            enabled: New kill switch state.

        Returns:
            Dict with update data.
        """
        return {"kill_switch": enabled}

    def get_exposure_stats(
        self,
        flag_key: str,
        exposure_data: list[dict],
        days: int = 30,
    ) -> dict:
        """Calculate exposure statistics for a feature flag.

        Args:
            flag_key: Feature flag key.
            exposure_data: List of exposure records with user_id, variant, timestamp.
            days: Number of days to consider (default 30).

        Returns:
            Dict with exposure percentages and variant breakdown.
        """
        cutoff = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff_str = cutoff.isoformat()

        # Filter by date
        filtered = [
            e
            for e in exposure_data
            if e.get("flag_key") == flag_key and e.get("timestamp", "") > cutoff_str
        ]

        if not filtered:
            return {
                "flag_key": flag_key,
                "days": days,
                "total_users": 0,
                "exposed_users": 0,
                "exposure_percentage": 0.0,
                "variant_breakdown": {},
            }

        total_unique = len(set(e.get("user_id") for e in filtered))
        exposed_unique = len(
            set(e.get("user_id") for e in filtered if e.get("enabled", False))
        )

        # Variant breakdown
        variant_counts: dict[str, int] = {}
        for e in filtered:
            if e.get("enabled", False):
                variant = e.get("variant", "default")
                variant_counts[variant] = variant_counts.get(variant, 0) + 1

        return {
            "flag_key": flag_key,
            "days": days,
            "total_users": total_unique,
            "exposed_users": exposed_unique,
            "exposure_percentage": (
                (exposed_unique / total_unique * 100) if total_unique > 0 else 0.0
            ),
            "variant_breakdown": {
                k: (v / exposed_unique * 100) if exposed_unique > 0 else 0.0
                for k, v in variant_counts.items()
            },
        }

    # ── Private Methods ────────────────────────────────────────────────

    @staticmethod
    def _deterministic_bucket(user_id: str, flag_key: str) -> int:
        """Calculate deterministic bucket (0-99) using SHA256.

        Ensures same user always gets same bucket for a flag.

        Args:
            user_id: User identifier.
            flag_key: Feature flag key.

        Returns:
            Integer bucket value (0-99).
        """
        # Create deterministic hash
        hash_input = f"{user_id}:{flag_key}".encode()
        hash_bytes = hashlib.sha256(hash_input).digest()

        # Convert first 4 bytes to integer and modulo 100
        bucket_int = int.from_bytes(hash_bytes[:4], byteorder="big", signed=False)
        return bucket_int % 100

    def _evaluate_targeting_rules(
        self, rules: list[dict], user_context: dict[str, Any]
    ) -> bool:
        """Evaluate targeting rules against user context.

        All rules must match (AND logic) for the user to be targeted.

        Args:
            rules: List of rule objects with attribute, operator, values.
            user_context: User attributes to evaluate against.

        Returns:
            True if all rules match, False otherwise.
        """
        for rule in rules:
            attribute = rule.get("attribute")
            operator = rule.get("operator")
            values = rule.get("values", [])

            if not attribute or not operator:
                continue

            user_value = user_context.get(attribute)

            if not self._evaluate_rule(user_value, operator, values):
                return False

        return True

    def _evaluate_rule(
        self, user_value: Any, operator: str, expected_values: list
    ) -> bool:
        """Evaluate a single targeting rule.

        Args:
            user_value: Actual value from user context.
            operator: Rule operator (IN, NOT_IN, GT, LT, etc.).
            expected_values: Expected values from rule.

        Returns:
            True if rule evaluates to True.
        """
        try:
            op = RuleOperator(operator)

            if op == RuleOperator.IN:
                return user_value in expected_values

            elif op == RuleOperator.NOT_IN:
                return user_value not in expected_values

            elif op == RuleOperator.GT:
                return (
                    isinstance(user_value, (int, float))
                    and user_value > (expected_values[0] if expected_values else 0)
                )

            elif op == RuleOperator.GTE:
                return (
                    isinstance(user_value, (int, float))
                    and user_value >= (expected_values[0] if expected_values else 0)
                )

            elif op == RuleOperator.LT:
                return (
                    isinstance(user_value, (int, float))
                    and user_value < (expected_values[0] if expected_values else 0)
                )

            elif op == RuleOperator.LTE:
                return (
                    isinstance(user_value, (int, float))
                    and user_value <= (expected_values[0] if expected_values else 0)
                )

            elif op == RuleOperator.EQ:
                return user_value == (expected_values[0] if expected_values else None)

            elif op == RuleOperator.NEQ:
                return user_value != (expected_values[0] if expected_values else None)

            elif op == RuleOperator.CONTAINS:
                if not isinstance(user_value, str):
                    return False
                return any(v in user_value for v in expected_values if isinstance(v, str))

            elif op == RuleOperator.NOT_CONTAINS:
                if not isinstance(user_value, str):
                    return True
                return not any(v in user_value for v in expected_values if isinstance(v, str))

            elif op == RuleOperator.REGEX:
                if not isinstance(user_value, str):
                    return False
                pattern = expected_values[0] if expected_values else ""
                return bool(re.search(pattern, user_value))

            elif op == RuleOperator.NOT_REGEX:
                if not isinstance(user_value, str):
                    return True
                pattern = expected_values[0] if expected_values else ""
                return not bool(re.search(pattern, user_value))

            return False

        except (ValueError, TypeError, re.error):
            # Invalid operator or type mismatch
            return False

    def _select_variant(self, flag: FeatureFlag, bucket: int) -> str | None:
        """Select a variant based on normalized weights and bucket.

        Args:
            flag: FeatureFlag with variants.
            bucket: Deterministic bucket (0-99).

        Returns:
            Selected variant key or None.
        """
        if not flag.has_variants():
            return None

        normalized = flag.get_normalized_variants()

        # Use bucket to select variant (bucket is 0-99, scale to cumulative weights)
        cumulative = 0.0
        scaled_bucket = bucket / 100.0

        for variant in normalized:
            cumulative += variant["weight"]
            if scaled_bucket <= cumulative:
                return variant.get("key", "default")

        # Fallback to first variant
        return normalized[0].get("key", "default") if normalized else None


# ── Convenience Functions ────────────────────────────────────────────────


def create_flag_result(enabled: bool, variant: str | None = None, reason: str = "") -> FlagResult:
    """Create a FlagResult instance.

    Args:
        enabled: Whether the flag is enabled.
        variant: Selected variant (optional).
        reason: Explanation for the decision.

    Returns:
        FlagResult instance.
    """
    return FlagResult(enabled=enabled, variant=variant, reason=reason)
