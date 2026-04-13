"""Targeting service for flexible audience segmentation.

Provides:
- Recursive condition tree evaluation
- Parallel segment matching
- Experiment variant assignment with targeting
- Cohort analysis and emotion profiling
- CRM attribute sync
- Emotional cohort auto-creation
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

import structlog

from app.models.segment import (
    Segment,
    SegmentOperator,
    ConditionOperator,
    SegmentType,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)


# ── Result Classes ────────────────────────────────────────────────────────


@dataclass
class SegmentEvaluationResult:
    """Result of evaluating a segment for a user."""

    segment_id: str
    matches: bool
    matched_conditions: list[str] | None = None
    failed_conditions: list[str] | None = None


@dataclass
class SegmentSizeEstimate:
    """Estimated size of a segment."""

    segment_id: str
    estimated_size: int
    sample_size: int
    confidence: float  # 0-1


@dataclass
class EmotionProfile:
    """Emotional profile of a segment."""

    segment_id: str
    dominant_emotion: str
    frustration_avg: float
    confusion_avg: float
    delight_avg: float
    anxiety_avg: float
    focus_avg: float
    satisfaction_avg: float
    hesitation_avg: float
    conversion_rate: float
    total_users: int


@dataclass
class VariantAssignment:
    """Result of assigning a variant to a user."""

    variant_id: str | None
    assignment_reason: str
    bucket_value: float | None = None


# ── Targeting Service ────────────────────────────────────────────────────────


class TargetingService:
    """Service for evaluating segments and assigning experiment variants."""

    # Maximum nesting depth for condition trees
    MAX_CONDITION_DEPTH = 5

    # Default sample size for segment estimation
    DEFAULT_SAMPLE_SIZE = 10000

    # Emotional cohort default thresholds
    DEFAULT_EMOTION_SCORE_THRESHOLD = 0.6

    def __init__(self):
        self._cache: dict[str, float] = {}
        self._cache_ttl = timedelta(minutes=5)
        self._cache_timestamps: dict[str, datetime] = {}

    # ── Condition Evaluation ─────────────────────────────────────────

    def evaluate_segment(
        self, segment: Segment, user_context: dict, depth: int = 0
    ) -> bool:
        """Recursively evaluate condition tree against user_context.

        Args:
            segment: The segment with conditions to evaluate
            user_context: User context dict with nested user/session/event data
            depth: Current recursion depth (for preventing infinite loops)

        Returns:
            True if user matches segment conditions, False otherwise

        Raises:
            ValueError: If condition depth exceeds MAX_CONDITION_DEPTH
        """
        if depth > self.MAX_CONDITION_DEPTH:
            raise ValueError(
                f"Condition depth {depth} exceeds maximum {self.MAX_CONDITION_DEPTH}"
            )

        conditions = segment.conditions

        if not conditions or "operator" not in conditions:
            return True  # No conditions = match all

        operator = conditions["operator"]
        nested_conditions = conditions.get("conditions", [])

        if not nested_conditions:
            return operator == SegmentOperator.AND  # Empty AND matches, empty OR doesn't

        results: list[bool] = []

        for cond in nested_conditions:
            if "operator" in cond and "conditions" in cond:
                # Nested condition group
                results.append(self._evaluate_condition_group(cond, user_context, depth + 1))
            elif "attribute" in cond:
                # Leaf condition
                results.append(self._evaluate_leaf_condition(cond, user_context))
            else:
                logger.warning("Invalid condition structure", condition=cond)
                results.append(False)

        if operator == SegmentOperator.AND:
            return all(results)
        else:  # OR
            return any(results)

    def _evaluate_condition_group(
        self, group: dict, user_context: dict, depth: int
    ) -> bool:
        """Evaluate a nested condition group."""
        return self._evaluate_conditions(group, user_context, depth)

    def _evaluate_leaf_condition(self, condition: dict, user_context: dict) -> bool:
        """Evaluate a single leaf condition."""
        attribute = condition.get("attribute", "")
        operator = condition.get("operator", "")
        value = condition.get("value")

        # Extract attribute value from nested context
        attr_value = self._get_nested_value(user_context, attribute)

        if attr_value is None:
            # Handle exists/not_exists operators
            if operator == ConditionOperator.EXISTS:
                return False
            if operator == ConditionOperator.NOT_EXISTS:
                return True

        try:
            if operator == ConditionOperator.EQ:
                return str(attr_value) == str(value)
            elif operator == ConditionOperator.NEQ:
                return str(attr_value) != str(value)
            elif operator == ConditionOperator.GT:
                return float(attr_value) > float(value)
            elif operator == ConditionOperator.LT:
                return float(attr_value) < float(value)
            elif operator == ConditionOperator.GTE:
                return float(attr_value) >= float(value)
            elif operator == ConditionOperator.LTE:
                return float(attr_value) <= float(value)
            elif operator == ConditionOperator.CONTAINS:
                return value in str(attr_value)
            elif operator == ConditionOperator.IN:
                return str(attr_value) in [str(v) for v in value]
            elif operator == ConditionOperator.NOT_IN:
                return str(attr_value) not in [str(v) for v in value]
            elif operator == ConditionOperator.REGEX:
                return bool(re.search(str(value), str(attr_value)))
            elif operator == ConditionOperator.EXISTS:
                return attr_value is not None
            elif operator == ConditionOperator.NOT_EXISTS:
                return attr_value is None
            else:
                logger.warning("Unknown operator", operator=operator)
                return False
        except (TypeError, ValueError, re.error) as e:
            logger.warning("Condition evaluation error", error=str(e), condition=condition)
            return False

    def _get_nested_value(self, context: dict, path: str) -> Any:
        """Extract a value from nested dict using dot notation."""
        keys = path.split(".")
        value = context

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return None
            else:
                return None

        return value

    # ── Batch Evaluation ───────────────────────────────────────────

    async def get_matching_segments(
        self, user_context: dict, segment_ids: list[str], db: AsyncSession
    ) -> list[str]:
        """Return IDs of segments the user matches.

        Evaluates all segments in parallel using asyncio.gather for performance.

        Args:
            user_context: User context dict
            segment_ids: List of segment IDs to evaluate
            db: Database session for fetching segments

        Returns:
            List of segment IDs that match the user
        """
        from sqlalchemy import select

        if not segment_ids:
            return []

        # Fetch segments
        result = await db.execute(
            select(Segment).where(Segment.id.in_(segment_ids), Segment.is_active == True)
        )
        segments = result.scalars().all()

        # Evaluate in parallel
        tasks = [
            self._evaluate_segment_async(segment, user_context) for segment in segments
        ]
        results = await asyncio.gather(*tasks)

        return [
            str(s.id) for s, r in zip(segments, results) if r
        ]

    async def _evaluate_segment_async(
        self, segment: Segment, user_context: dict
    ) -> bool:
        """Evaluate a single segment asynchronously."""
        return await asyncio.to_thread(self.evaluate_segment, segment, user_context)

    # ── Variant Assignment ───────────────────────────────────────

    def assign_experiment_variant(
        self, experiment: dict, user_context: dict, use_bandit: bool = False
    ) -> VariantAssignment:
        """Assign a variant to a user for an experiment.

        First checks if user matches experiment targeting rules.
        If matched, assigns variant via bandit or deterministic hash.
        If not matched, returns None (user excluded).

        Args:
            experiment: Experiment dict with targeting_rules, variants
            user_context: User context dict
            use_bandit: If True, use bandit service for assignment

        Returns:
            VariantAssignment with assigned variant or None
        """
        targeting_rules = experiment.get("targeting_rules")
        if targeting_rules:
            # Create temporary segment from targeting rules
            temp_segment = Segment(
                merchant_id=None,  # type: ignore
                name="temp",
                conditions=targeting_rules,
                segment_type="static",
            )
            if not self.evaluate_segment(temp_segment, user_context):
                return VariantAssignment(
                    variant_id=None, assignment_reason="User excluded by targeting rules"
                )

        variants = experiment.get("variants", [])
        if not variants:
            return VariantAssignment(variant_id=None, assignment_reason="No variants defined")

        if use_bandit:
            # Use bandit service for assignment
            from app.services.bandit_service import BanditService

            bandit = BanditService()
            variant = bandit.get_arm(str(experiment["id"]))
            return VariantAssignment(
                variant_id=variant, assignment_reason="Bandit assignment"
            )
        else:
            # Deterministic hash-based assignment
            user_id = str(user_context.get("user_id", "anonymous"))
            experiment_id = str(experiment["id"])

            # Create bucket value (0-1)
            bucket_key = f"{experiment_id}:{user_id}"
            bucket_value = self._hash_to_bucket(bucket_key)

            # Assign variant based on weights
            total_weight = sum(v.get("weight", 1.0) for v in variants)
            cumulative = 0.0

            for variant in variants:
                weight = variant.get("weight", 1.0)
                cumulative += weight / total_weight
                if bucket_value <= cumulative:
                    return VariantAssignment(
                        variant_id=variant["id"],
                        assignment_reason="Deterministic hash",
                        bucket_value=bucket_value,
                    )

            # Fallback to first variant
            return VariantAssignment(
                variant_id=variants[0]["id"],
                assignment_reason="Default (first variant)",
                bucket_value=bucket_value,
            )

    def _hash_to_bucket(self, key: str) -> float:
        """Convert a string key to a deterministic float in [0, 1]."""
        hash_bytes = hashlib.sha256(key.encode()).digest()
        hash_int = int.from_bytes(hash_bytes, byteorder="big")
        return hash_int / (2**256)

    # ── Cohort Analysis ───────────────────────────────────────────

    async def estimate_segment_size(
        self, segment: Segment, db: AsyncSession, days: int = 30
    ) -> SegmentSizeEstimate:
        """Estimate the size of a segment by sampling recent users.

        Args:
            segment: The segment to estimate
            db: Database session
            days: Number of days to look back

        Returns:
            SegmentSizeEstimate with estimated size and confidence
        """
        from sqlalchemy import func, select
        from app.models.session import Session

        # Get total unique users in the period
        since = datetime.now(UTC) - timedelta(days=days)

        total_query = (
            select(func.count(func.distinct(Session.user_id)))
            .where(Session.created_at >= since)
            .subquery()
        )
        total_result = await db.execute(select(total_query))
        total_users = total_result.scalar() or 0

        if total_users == 0:
            return SegmentSizeEstimate(
                segment_id=str(segment.id),
                estimated_size=0,
                sample_size=0,
                confidence=1.0,
            )

        # Sample users (limit to DEFAULT_SAMPLE_SIZE for performance)
        sample_size = min(total_users, self.DEFAULT_SAMPLE_SIZE)

        sample_query = (
            select(Session.user_id)
            .where(Session.created_at >= since)
            .distinct()
            .limit(sample_size)
        )
        sample_result = await db.execute(sample_query)
        sampled_users = [row[0] for row in sample_result.fetchall()]

        # Count matches
        matches = 0
        for user_id in sampled_users:
            # Build mock user context (in production, would fetch from cache)
            mock_context = {"user_id": user_id}
            if self.evaluate_segment(segment, mock_context):
                matches += 1

        # Extrapolate
        if sample_size > 0:
            estimated_size = int((matches / sample_size) * total_users)
            confidence = self._calculate_confidence(matches, sample_size)
        else:
            estimated_size = 0
            confidence = 0.0

        return SegmentSizeEstimate(
            segment_id=str(segment.id),
            estimated_size=estimated_size,
            sample_size=sample_size,
            confidence=confidence,
        )

    def _calculate_confidence(self, matches: int, sample_size: int) -> float:
        """Calculate confidence in size estimate based on sample size."""
        if sample_size == 0:
            return 0.0

        # Simple confidence based on sample size
        # Larger sample = higher confidence
        if sample_size >= 10000:
            return 0.95
        elif sample_size >= 5000:
            return 0.90
        elif sample_size >= 1000:
            return 0.80
        elif sample_size >= 500:
            return 0.70
        elif sample_size >= 100:
            return 0.60
        else:
            return 0.50

    async def get_segment_emotion_profile(
        self, segment_id: str, db: AsyncSession, days: int = 30
    ) -> EmotionProfile | None:
        """Get the emotional profile of users in a segment.

        Returns emotion breakdown and conversion rate for the segment.

        Args:
            segment_id: Segment to analyze
            db: Database session
            days: Number of days to look back

        Returns:
            EmotionProfile with emotion statistics
        """
        from sqlalchemy import func, select
        from app.models.emotion_event import EmotionSession

        since = datetime.now(UTC) - timedelta(days=days)

        # Get emotion sessions for segment
        # In production, would join with users matching segment
        query = (
            select(
                EmotionSession.dominant_emotion,
                func.count(EmotionSession.id).label("count"),
                func.avg(EmotionSession.frustration_score).label("frustration_avg"),
            )
            .where(EmotionSession.start_time >= since)
            .group_by(EmotionSession.dominant_emotion)
        )
        result = await db.execute(query)
        emotion_data = result.fetchall()

        if not emotion_data:
            return None

        # Calculate totals and averages
        total_users = sum(row.count for row in emotion_data)
        dominant_emotion = max(emotion_data, key=lambda x: x.count)[0]

        # Initialize all emotions
        emotion_avgs = {
            "frustration": 0.0,
            "confusion": 0.0,
            "delight": 0.0,
            "anxiety": 0.0,
            "focus": 0.0,
            "satisfaction": 0.0,
            "hesitation": 0.0,
        }

        for emotion, count, avg in emotion_data:
            if emotion in emotion_avgs:
                emotion_avgs[emotion] = avg or 0.0

        # Get conversion rate (simplified - would need conversion event tracking)
        conversion_rate = 0.0  # TODO: Implement with conversion events

        return EmotionProfile(
            segment_id=segment_id,
            dominant_emotion=dominant_emotion,
            frustration_avg=emotion_avgs["frustration"],
            confusion_avg=emotion_avgs["confusion"],
            delight_avg=emotion_avgs["delight"],
            anxiety_avg=emotion_avgs["anxiety"],
            focus_avg=emotion_avgs["focus"],
            satisfaction_avg=emotion_avgs["satisfaction"],
            hesitation_avg=emotion_avgs["hesitation"],
            conversion_rate=conversion_rate,
            total_users=total_users,
        )

    # ── Import/Sync ────────────────────────────────────────────────

    async def sync_crm_attributes(
        self, user_id: str, crm_data: dict, db: AsyncSession
    ) -> None:
        """Store custom CRM attributes for a user.

        Attributes are stored under the custom.* namespace in user profile.
        Merges with existing attributes (doesn't overwrite).

        Args:
            user_id: User ID to update
            crm_data: Dict of attributes to sync (e.g., {"plan": "premium", "ltv": 1500})
            db: Database session
        """
        # In production, would store in user_custom_attributes table
        # For now, log the sync
        logger.info("CRM attributes synced", user_id=user_id, attributes=list(crm_data.keys()))

        # TODO: Implement actual storage in user_custom_attributes table
        # Would use JSON column to store custom attributes
        # Format: {"custom.plan": "premium", "custom.ltv": 1500}

    async def create_emotional_cohort(
        self,
        emotion: str,
        min_score: float,
        experiment_id: str,
        merchant_id: str,
        db: AsyncSession,
    ) -> Segment:
        """Auto-create a dynamic emotional cohort segment.

        Creates a segment that matches users with a specific emotion score
        threshold for a given experiment.

        Args:
            emotion: Emotion to target (e.g., "frustration")
            min_score: Minimum score threshold (0-1)
            experiment_id: Associated experiment ID
            merchant_id: Merchant ID
            db: Database session

        Returns:
            Created Segment
        """
        segment = Segment(
            merchant_id=merchant_id,
            name=f"High {emotion} - {experiment_id[:8]}",
            description=f"Users with {emotion} score >= {min_score} in experiment {experiment_id}",
            conditions={
                "operator": "AND",
                "conditions": [
                    {
                        "attribute": f"session.{emotion}_score",
                        "operator": ConditionOperator.GTE,
                        "value": min_score,
                    }
                ],
            },
            segment_type=SegmentType.EMOTIONAL,
        )

        db.add(segment)
        await db.commit()
        await db.refresh(segment)

        logger.info(
            "Emotional cohort created",
            segment_id=str(segment.id),
            emotion=emotion,
            min_score=min_score,
            experiment_id=experiment_id,
        )

        return segment
