"""Stats service for advanced statistical analysis.

Provides:
- Two-proportion z-test and Welch's t-test for significance
- CUPED variance reduction using pre-experiment covariates
- ROPE (Region of Practical Equivalence) for practical significance
- SRM detection via chi-square goodness of fit
- Anomaly detection via Z-score on rolling windows
- Funnel analysis with emotion profiling
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    pass

logger = structlog.get_logger(__name__)


# ── Result Classes ────────────────────────────────────────────────


@dataclass
class VariantResult:
    """Results for a single variant."""

    variant_id: str
    name: str
    visitors: int
    conversions: int
    conversion_rate: float
    relative_lift: float | None = None
    p_value: float | None = None
    confidence_interval: tuple[float, float] | None = None
    is_significant: bool = False
    practical_significance: str | None = None  # ROPE result


@dataclass
class ExperimentResults:
    """Complete results for an experiment."""

    experiment_id: str
    experiment_name: str
    variants: list[VariantResult]
    winner: str | None
    status: str  # running, completed, inconclusive
    total_visitors: int
    total_conversions: int


@dataclass
class CUPEDResult:
    """Result of applying CUPED variance reduction."""

    original_variance: float
    adjusted_variance: float
    variance_reduction: float
    theta: float  # Regression coefficient
    metrics: dict[str, float]


@dataclass
class ROPEResult:
    """Result of ROPE (Region of Practical Equivalence) test."""

    classification: str  # significant_positive | significant_negative | equivalent | inconclusive
    lift: float
    ci_lower: float
    ci_upper: float
    rope_width: float
    explanation: str


@dataclass
class SRMResult:
    """Result of Sample Ratio Mismatch detection."""

    has_srm: bool
    chi2_stat: float
    p_value: float
    severity: str  # minor | moderate | severe
    affected_variants: list[str]
    expected_ratios: dict[str, float]
    actual_counts: dict[str, int]


@dataclass
class Anomaly:
    """Detected anomaly in metric time series."""

    timestamp: datetime
    metric: str
    value: float
    z_score: float
    type: str  # spike | drop


@dataclass
class FunnelStep:
    """A single step in the funnel."""

    name: str
    visitors: int
    conversions: int
    conversion_rate: float
    drop_off_rate: float
    emotion_profile: dict[str, float] | None = None
    dominant_emotion: str | None = None


@dataclass
class FunnelResult:
    """Complete funnel analysis results."""

    experiment_id: str
    steps: list[FunnelStep]
    total_visitors: int
    overall_conversion_rate: float
    variant_id: str | None = None


# ── Stats Service ────────────────────────────────────────────────


class StatsService:
    """Service for statistical analysis of experiment results."""

    # SRM detection threshold
    SRM_P_THRESHOLD = 0.001

    # Anomaly detection parameters
    ANOMALY_Z_THRESHOLD = 3.0
    DEFAULT_ANOMALY_WINDOW = 24  # hours

    # Funnel behavioral state categories
    FUNNEL_EMOTIONS = ["confused", "frustrated", "engaged", "disengaged"]

    # ── Core Stats ────────────────────────────────────────

    async def calculate_results(
        self, experiment_id: str, db: AsyncSession
    ) -> ExperimentResults:
        """Calculate complete experiment results with statistical tests.

        Returns variant-level metrics with conversion rates, relative lift,
        p-values, confidence intervals, and significance status.
        """
        from sqlalchemy import select

        from app.models.experiment import Experiment

        # Fetch experiment
        result = await db.execute(
            select(Experiment).where(Experiment.id == experiment_id)
        )
        experiment = result.scalar_one_or_none()

        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")

        # Fetch events grouped by variant

        # Placeholder: In production, would query actual event data
        # For now, return mock results
        variants = [
            VariantResult(
                variant_id="control",
                name="Control",
                visitors=10000,
                conversions=500,
                conversion_rate=0.05,
                relative_lift=None,
                p_value=None,
                confidence_interval=None,
                is_significant=False,
            ),
            VariantResult(
                variant_id="variant_a",
                name="Variant A",
                visitors=10000,
                conversions=550,
                conversion_rate=0.055,
                relative_lift=0.10,
                p_value=0.03,
                confidence_interval=(0.048, 0.062),
                is_significant=True,
                practical_significance="significant_positive",
            ),
        ]

        # Calculate significance
        self._calculate_variant_significance(variants)

        # Determine winner
        winner = None
        if variants[0].conversion_rate > 0:
            best = max(variants, key=lambda v: v.conversion_rate)
            if best.is_significant:
                winner = best.variant_id

        return ExperimentResults(
            experiment_id=experiment_id,
            experiment_name=experiment.title,
            variants=variants,
            winner=winner,
            status="completed" if winner else "inconclusive",
            total_visitors=sum(v.visitors for v in variants),
            total_conversions=sum(v.conversions for v in variants),
        )

    def _calculate_variant_significance(
        self, variants: list[VariantResult]
    ) -> None:
        """Calculate p-values and confidence intervals for variants."""
        n_variants = len(variants)

        if n_variants < 2:
            return

        control = variants[0]

        for i in range(1, n_variants):
            variant = variants[i]

            # Two-proportion z-test for conversion rates
            p1 = control.conversion_rate
            p2 = variant.conversion_rate
            n1 = control.visitors
            n2 = variant.visitors

            if n1 == 0 or n2 == 0:
                continue

            # Pooled proportion
            p_pooled = (control.conversions + variant.conversions) / (n1 + n2)

            if p_pooled == 0 or p_pooled == 1:
                continue

            # Z-score
            se = math.sqrt(p_pooled * (1 - p_pooled) * (1/n1 + 1/n2))
            if se == 0:
                continue

            z = (p2 - p1) / se

            # P-value (two-tailed)
            # Use standard normal CDF approximation
            p_value = 2 * (1 - self._normal_cdf(abs(z)))

            variant.p_value = p_value
            variant.is_significant = p_value < 0.05

            # Confidence interval (95%)
            z_critical = 1.96
            se_variant = math.sqrt(p2 * (1 - p2) / n2)
            margin = z_critical * se_variant
            variant.confidence_interval = (
                max(0.0, p2 - margin),
                min(1.0, p2 + margin),
            )

            # Relative lift
            if p1 > 0:
                variant.relative_lift = ((p2 - p1) / p1) * 100

    def _normal_cdf(self, x: float) -> float:
        """Approximate standard normal CDF using error function."""
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))

    # ── CUPED Variance Reduction ─────────────────────────────

    async def apply_cuped(
        self,
        experiment_id: str,
        covariate_metric: str,
        db: AsyncSession,
    ) -> CUPEDResult:
        """Apply CUPED variance reduction using pre-experiment covariate.

        Formula: Y_cuped = Y - θ * (X - X_mean)
        Where θ = Cov(Y,X) / Var(X)

        Args:
            experiment_id: Experiment ID
            covariate_metric: Pre-experiment covariate (e.g., past revenue)
            db: Database session

        Returns:
            CUPEDResult with adjusted metrics and variance reduction %
        """
        from app.models.experiment import Experiment

        result = await db.execute(
            select(Experiment).where(Experiment.id == experiment_id)
        )
        experiment = result.scalar_one_or_none()

        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")

        # Placeholder: In production, would fetch actual covariate data
        # For now, return mock result
        original_variance = 0.01  # Placeholder
        theta = 0.85  # Regression coefficient
        adjusted_variance = original_variance * (1 - theta)

        variance_reduction = ((original_variance - adjusted_variance) / original_variance) * 100

        return CUPEDResult(
            original_variance=original_variance,
            adjusted_variance=adjusted_variance,
            variance_reduction=variance_reduction,
            theta=theta,
            metrics={},
        )

    # ── ROPE (Region of Practical Equivalence) ─────────────

    def check_rope(
        self,
        lift: float,
        ci_lower: float,
        ci_upper: float,
        rope_width: float = 0.01,
    ) -> ROPEResult:
        """Check if lift is practically significant using ROPE.

        ROPE defines a region around zero lift that is considered
        practically equivalent.

        Args:
            lift: Observed relative lift (as decimal, e.g., 0.05 for 5%)
            ci_lower: Lower bound of confidence interval
            ci_upper: Upper bound of confidence interval
            rope_width: ROPE width around zero (default 1%)

        Returns:
            ROPEResult with classification and explanation
        """
        rope_lower = -rope_width
        rope_upper = rope_width

        # Check if CI is entirely outside ROPE
        if ci_lower > rope_upper:
            classification = "significant_positive"
            explanation = f"Confidence interval [{ci_lower:.2%}, {ci_upper:.2%}] is entirely above ROPE [{rope_lower:.2%}, {rope_upper:.2%}]"
        elif ci_upper < rope_lower:
            classification = "significant_negative"
            explanation = f"Confidence interval [{ci_lower:.2%}, {ci_upper:.2%}] is entirely below ROPE [{rope_lower:.2%}, {rope_upper:.2%}]"
        elif ci_lower >= rope_lower and ci_upper <= rope_upper:
            classification = "equivalent"
            explanation = f"Confidence interval [{ci_lower:.2%}, {ci_upper:.2%}] falls within ROPE [{rope_lower:.2%}, {rope_upper:.2%}]"
        else:
            classification = "inconclusive"
            explanation = f"Confidence interval [{ci_lower:.2%}, {ci_upper:.2%}] partially overlaps ROPE [{rope_lower:.2%}, {rope_upper:.2%}]"

        return ROPEResult(
            classification=classification,
            lift=lift,
            ci_lower=ci_lower,
            ci_upper=ci_upper,
            rope_width=rope_width,
            explanation=explanation,
        )

    # ── SRM Detection ─────────────────────────────────────────────

    def detect_srm(
        self,
        expected_splits: dict[str, float],
        actual_counts: dict[str, int],
    ) -> SRMResult:
        """Detect Sample Ratio Mismatch via chi-square goodness of fit.

        Alert threshold: p < 0.001 indicates severe SRM.

        Args:
            expected_splits: Expected traffic split ratios (e.g., {"control": 0.5, "variant_a": 0.5})
            actual_counts: Actual observed counts

        Returns:
            SRMResult with chi-square statistic, p-value, and affected variants
        """
        total_actual = sum(actual_counts.values())

        if total_actual == 0:
            return SRMResult(
                has_srm=False,
                chi2_stat=0.0,
                p_value=1.0,
                severity="none",
                affected_variants=[],
                expected_ratios=expected_splits,
                actual_counts=actual_counts,
            )

        # Calculate expected counts
        expected_counts = {
            variant: total_actual * ratio
            for variant, ratio in expected_splits.items()
        }

        # Calculate chi-square statistic
        chi2 = 0.0
        affected_variants: list[str] = []

        for variant in expected_splits:
            actual = actual_counts.get(variant, 0)
            expected = expected_counts.get(variant, 0)

            if expected > 0:
                contribution = ((actual - expected) ** 2) / expected
                chi2 += contribution

                # Check if contribution is significant (> 4 for single df)
                if contribution > 4.0:
                    if variant not in affected_variants:
                        affected_variants.append(variant)

        # Calculate p-value (chi-square with k-1 degrees of freedom)
        degrees_of_freedom = len(expected_splits) - 1

        if degrees_of_freedom > 0:
            # Simplified p-value calculation
            # In production, would use chi-square CDF
            p_value = math.exp(-0.5 * chi2)  # Rough approximation
        else:
            p_value = 1.0

        # Determine severity
        has_srm = p_value < self.SRM_P_THRESHOLD
        if has_srm:
            severity = "severe"
        elif chi2 > 4.0:
            severity = "moderate"
        else:
            severity = "minor"

        return SRMResult(
            has_srm=has_srm,
            chi2_stat=chi2,
            p_value=p_value,
            severity=severity,
            affected_variants=affected_variants,
            expected_ratios=expected_splits,
            actual_counts=actual_counts,
        )

    # ── Anomaly Detection ─────────────────────────────────────

    async def detect_anomalies(
        self,
        experiment_id: str,
        metric: str,
        window_hours: int = 24,
        db: AsyncSession | None = None,
    ) -> list[Anomaly]:
        """Detect anomalies in metric time series using Z-score.

        Flags data points > 3 std devs from rolling mean.

        Args:
            experiment_id: Experiment ID
            metric: Metric to analyze (e.g., conversion_rate, revenue)
            window_hours: Size of rolling window for mean/std calculation
            db: Database session (optional)

        Returns:
            List of detected anomalies with timestamps, values, and z-scores
        """
        # Placeholder: In production, would fetch actual time series data
        # For now, generate mock data points
        import random

        now = datetime.now(UTC)
        data_points: list[dict] = []

        for i in range(100):
            timestamp = now - timedelta(hours=i)
            value = 0.05 + random.gauss(0, 0.01)  # Mean 5%, std 1%
            data_points.append({"timestamp": timestamp, "value": value})

        # Detect anomalies
        anomalies: list[Anomaly] = []

        for i in range(window_hours, len(data_points)):
            # Calculate rolling mean and std
            window = data_points[i - window_hours : i]
            values = [p["value"] for p in window]
            mean = statistics.mean(values)
            std = statistics.stdev(values) if len(values) > 1 else 0

            current = data_points[i]
            z_score = 0.0

            if std > 0:
                z_score = (current["value"] - mean) / std

            # Flag if Z-score exceeds threshold
            if abs(z_score) > self.ANOMALY_Z_THRESHOLD:
                anomalies.append(
                    Anomaly(
                        timestamp=current["timestamp"],
                        metric=metric,
                        value=current["value"],
                        z_score=z_score,
                        type="spike" if z_score > 0 else "drop",
                    )
                )

        return anomalies

    # ── Funnel Analysis ────────────────────────────────────────

    async def calculate_funnel(
        self,
        experiment_id: str,
        steps: list[str],
        variant_id: str | None = None,
        db: AsyncSession | None = None,
    ) -> FunnelResult:
        """Calculate funnel analysis with emotion profiling.

        Joins with EmotionSession to add emotion_profile per step.

        Args:
            experiment_id: Experiment ID
            steps: List of funnel step names (e.g., ["view", "add_to_cart", "checkout"])
            variant_id: Optional variant ID for variant-level analysis
            db: Database session

        Returns:
            FunnelResult with per-step metrics and emotion profiles
        """
        # Placeholder: In production, would fetch actual funnel data
        # For now, generate mock funnel data

        funnels_steps: list[FunnelStep] = []
        visitors = 10000

        # Behavioral state colors for visualization
        emotion_colors = {
            "frustrated": "#EF4444",
            "confused": "#F59E0B",
            "hesitating": "#EAB308",
            "engaged": "#22C55E",
            "disengaged": "#6B7280",
        }

        # Generate mock funnel steps
        drop_rates = [0.0, 0.1, 0.15, 0.08]  # Cumulative drop-off

        for i, step_name in enumerate(steps):
            step_visitors = int(visitors * (1 - drop_rates[i - 1])) if i > 0 else visitors
            step_conversions = step_visitors - int(visitors * drop_rates[i])
            conversion_rate = step_conversions / step_visitors if step_visitors > 0 else 0.0
            drop_off_rate = drop_rates[i]

            # Generate mock emotion profile
            emotion_profile = {
                emotion: random.uniform(0.1, 0.4)
                for emotion in self.FUNNEL_EMOTIONS
            }

            # Find dominant emotion
            dominant_emotion = max(
                emotion_profile.items(), key=lambda x: x[1]
            )[0]

            funnels_steps.append(
                FunnelStep(
                    name=step_name,
                    visitors=step_visitors,
                    conversions=step_conversions,
                    conversion_rate=conversion_rate,
                    drop_off_rate=drop_off_rate,
                    emotion_profile=emotion_profile,
                    dominant_emotion=dominant_emotion,
                )
            )

        overall_rate = sum(s.conversions for s in funnels_steps) / sum(
            s.visitors for s in funnels_steps
        ) if funnels_steps else 0.0

        return FunnelResult(
            experiment_id=experiment_id,
            steps=funnels_steps,
            total_visitors=visitors,
            overall_conversion_rate=overall_rate,
            variant_id=variant_id,
        )


# ── Singleton instance ──────────────────────────────────────────

_service_instance: StatsService | None = None


def get_stats_service() -> StatsService:
    """Get singleton instance of StatsService."""
    global _service_instance
    if _service_instance is None:
        _service_instance = StatsService()
    return _service_instance
