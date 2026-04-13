"""Advanced Analytics API - stats, CUPED, ROPE, SRM, funnel, anomalies.

Endpoints for statistical analysis with variance reduction,
practical equivalence testing, sample ratio mismatch detection,
funnel analysis with emotion profiling, and anomaly detection.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.rate_limit import limiter
from app.services.stats_service import (
    StatsService,
    ExperimentResults,
    FunnelResult,
    CUPEDResult,
    SRMResult,
    Anomaly,
    get_stats_service,
)

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])
service = get_stats_service()


# ── Schemas ────────────────────────────────────────────────


class CUPEDRequest(BaseModel):
    covariate_metric: str = Field(..., description="Pre-experiment covariate (e.g., revenue, ltv)")


class FunnelRequest(BaseModel):
    experiment_id: str = Field(..., description="Experiment ID")
    steps: list[str] = Field(
        default_factory=lambda: ["view", "add_to_cart", "checkout", "purchase"],
        description="Funnel steps to analyze"
    )
    variant_id: str | None = Field(None, description="Optional variant for variant-level analysis")


class AnomalyRequest(BaseModel):
    experiment_id: str = Field(..., description="Experiment ID")
    metric: str = Field(default="conversion_rate", description="Metric to analyze")
    window_hours: int = Field(default=24, ge=1, le=168, description="Window size in hours")


# ── Experiment Results ───────────────────────────────────────


@router.get(
    "/experiments/{experiment_id}/results",
    summary="Get experiment results with statistical tests",
)
@limiter.limit("100/minute")
async def get_experiment_results(
    request: Request,
    experiment_id: str,
    db: Any = Depends(get_db),
):
    """Get complete experiment results with significance testing.

    Returns variant metrics with p-values, confidence intervals,
    and ROPE classification for practical significance.
    """
    results = await service.calculate_results(experiment_id, db)

    return {
        "experiment_id": results.experiment_id,
        "experiment_name": results.experiment_name,
        "variants": results.variants,
        "winner": results.winner,
        "status": results.status,
        "total_visitors": results.total_visitors,
        "total_conversions": results.total_conversions,
    }


# ── CUPED Variance Reduction ────────────────────────────────


@router.post(
    "/experiments/{experiment_id}/cuped",
    summary="Apply CUPED variance reduction",
)
@limiter.limit("50/minute")
async def apply_cuped(
    request: Request,
    experiment_id: str,
    body: CUPEDRequest,
    db: Any = Depends(get_db),
):
    """Apply CUPED variance reduction using pre-experiment covariate.

    Y_cuped = Y - θ * (X - X_mean)
    Where θ = Cov(Y,X) / Var(X)

    Returns adjusted metrics with variance reduction %.
    """
    result = await service.apply_cuped(experiment_id, body.covariate_metric, db)

    return {
        "original_variance": result.original_variance,
        "adjusted_variance": result.adjusted_variance,
        "variance_reduction": result.variance_reduction,
        "theta": result.theta,
        "metrics": result.metrics,
    }


# ── ROPE (Region of Practical Equivalence) ────────────────


@router.get(
    "/experiments/{experiment_id}/rope",
    summary="Check ROPE (Region of Practical Equivalence)",
)
@limiter.limit("100/minute")
async def check_rope(
    request: Request,
    experiment_id: str,
    rope_width: float = Query(0.01, ge=0.0, le=0.1, description="ROPE width around zero"),
    db: Any = Depends(get_db),
):
    """Check if lift is practically significant using ROPE.

    ROPE defines a region around zero lift that is
    considered practically equivalent.

    Returns classification: significant_positive, significant_negative,
    equivalent, or inconclusive.
    """
    from app.services.stats_service import get_stats_service
    stats = get_stats_service()

    # Get experiment results first
    results = await stats.calculate_results(experiment_id, db)

    # Check ROPE for each variant (except control)
    rope_results = []

    for variant in results.variants:
        if variant.variant_id == "control":
            continue

        if variant.confidence_interval and variant.relative_lift is not None:
            rope_result = stats.check_rope(
                lift=variant.relative_lift,
                ci_lower=variant.confidence_interval[0],
                ci_upper=variant.confidence_interval[1],
                rope_width=rope_width,
            )
            rope_results.append({
                "variant_id": variant.variant_id,
                "variant_name": variant.name,
                "lift": variant.relative_lift,
                "ci_lower": variant.confidence_interval[0],
                "ci_upper": variant.confidence_interval[1],
                "rope_width": rope_width,
                **rope_result.model_dump(),
            })

    return {
        "experiment_id": experiment_id,
        "rope_width": rope_width,
        "results": rope_results,
    }


# ── SRM Detection ────────────────────────────────────────────────


@router.get(
    "/experiments/{experiment_id}/srm",
    summary="Detect Sample Ratio Mismatch (SRM)",
)
@limiter.limit("100/minute")
async def detect_srm(
    request: Request,
    experiment_id: str,
    db: Any = Depends(get_db),
):
    """Detect Sample Ratio Mismatch via chi-square goodness of fit.

    Alert threshold: p < 0.001 indicates severe SRM.

    Returns chi-square statistic, p-value, severity, and affected variants.
    """
    from app.services.stats_service import get_stats_service
    stats = get_stats_service()

    # Get experiment results
    results = await stats.calculate_results(experiment_id, db)

    # Calculate expected splits (50/50 for two variants)
    expected_splits = {}
    total_visitors = results.total_visitors
    n_variants = len(results.variants)

    for variant in results.variants:
        expected_splits[variant.variant_id] = 1.0 / n_variants

    # Calculate actual counts
    actual_counts = {
        variant.variant_id: variant.visitors
        for variant in results.variants
    }

    # Detect SRM
    srm_result = stats.detect_srm(expected_splits, actual_counts)

    return {
        "experiment_id": experiment_id,
        "has_srm": srm_result.has_srm,
        "chi2_statistic": srm_result.chi2_stat,
        "p_value": srm_result.p_value,
        "severity": srm_result.severity,
        "affected_variants": srm_result.affected_variants,
        "expected_ratios": srm_result.expected_ratios,
        "actual_counts": srm_result.actual_counts,
    }


# ── Funnel Analysis ────────────────────────────────────────


@router.get(
    "/funnel",
    summary="Calculate funnel analysis with emotion profiling",
)
@limiter.limit("100/minute")
async def calculate_funnel(
    request: Request,
    experiment_id: str = Query(..., description="Experiment ID"),
    steps: list[str] = Query(default=["view", "add_to_cart", "checkout"], description="Funnel steps"),
    variant_id: str | None = Query(None, description="Optional variant ID for variant-level analysis"),
    db: Any = Depends(get_db),
):
    """Calculate funnel analysis with emotion profiling.

    Returns per-step metrics and emotion profiles from EmotionSession.
    """
    result = await service.calculate_funnel(
        db, experiment_id=experiment_id, steps=steps, variant_id=variant_id
    )

    return {
        "experiment_id": result.experiment_id,
        "steps": [
            {
                "name": s.name,
                "visitors": s.visitors,
                "conversions": s.conversions,
                "conversion_rate": s.conversionRate,
                "drop_off_rate": s.dropOffRate,
                "emotion_profile": s.emotionProfile,
                "dominant_emotion": s.dominantEmotion,
            }
            for s in result.steps
        ],
        "total_visitors": result.totalVisitors,
        "overall_conversion_rate": result.overallConversionRate,
        "variant_id": result.variantId,
    }


# ── Anomaly Detection ────────────────────────────────────────


@router.get(
    "/anomalies",
    summary="Detect anomalies in metric time series",
)
@limiter.limit("100/minute")
async def detect_anomalies(
    request: Request,
    experiment_id: str = Query(..., description="Experiment ID"),
    metric: str = Query(default="conversion_rate", description="Metric to analyze"),
    window_hours: int = Query(default=24, ge=1, le=168, description="Window size in hours"),
    db: Any = Depends(get_db),
):
    """Detect anomalies in metric time series using Z-score.

    Flags data points > 3 std devs from rolling mean.

    Returns list of detected anomalies with timestamps, values, and z-scores.
    """
    anomalies = await service.detect_anomalies(
        experiment_id, metric, window_hours, db
    )

    return {
        "experiment_id": experiment_id,
        "metric": metric,
        "anomalies": [
            {
                "timestamp": a.timestamp.isoformat() if a.timestamp else None,
                "metric": a.metric,
                "value": a.value,
                "z_score": a.z_score,
                "type": a.type,
            }
            for a in anomalies
        ],
    }
