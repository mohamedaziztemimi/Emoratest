"""Experiment business logic and statistical significance (CONV-38, CONV-41).

Provides:
- CRUD helpers for experiments (merchant-scoped)
- A/B test statistical significance calculation using normal approximation
  for proportions (Z-test for two proportions)
"""

from __future__ import annotations

import math


def compute_ab_significance(
    *,
    conversion_delta: float,
    sample_size: int,
    base_rate: float = 0.04,
    confidence_target: float = 0.95,
) -> dict:
    """Compute statistical significance for an A/B experiment.

    Uses a two-proportion Z-test (normal approximation) which is standard
    for conversion rate experiments with sufficient sample sizes (n > 30).

    Args:
        conversion_delta: Observed lift (variant_b - variant_a rate).
        sample_size: Total number of sessions across both variants.
        base_rate: Baseline conversion rate (variant A). Defaults to 4%.
        confidence_target: Desired confidence level (e.g. 0.95 for 95%).

    Returns:
        Dict with p_value, confidence_level, is_significant, power, recommendation.
    """
    if sample_size < 2:
        return {
            "p_value": None,
            "confidence_level": None,
            "is_significant": False,
            "power": None,
            "recommendation": "insufficient_data",
        }

    n_per_arm = sample_size / 2
    rate_a = base_rate
    rate_b = base_rate + conversion_delta

    # Clamp rates to valid range
    rate_b = max(0.001, min(0.999, rate_b))
    rate_a = max(0.001, min(0.999, rate_a))

    # Pooled proportion
    p_pooled = (rate_a + rate_b) / 2

    # Standard error for difference of two proportions
    se = math.sqrt(2 * p_pooled * (1 - p_pooled) / n_per_arm)

    if se == 0:
        return {
            "p_value": None,
            "confidence_level": None,
            "is_significant": False,
            "power": None,
            "recommendation": "zero_variance",
        }

    # Z-statistic
    z = abs(conversion_delta) / se

    # P-value approximation (two-tailed) using complementary error function
    p_value = 2 * (1 - _normal_cdf(z))

    confidence_level = 1 - p_value
    is_significant = p_value < (1 - confidence_target)

    # Power calculation (probability of detecting this effect size)
    z_alpha = _normal_ppf(1 - (1 - confidence_target) / 2)
    noncentrality = abs(conversion_delta) / se
    power = 1 - _normal_cdf(z_alpha - noncentrality)

    # Recommendation
    if is_significant and conversion_delta > 0:
        recommendation = "adopt_variant_b"
    elif is_significant and conversion_delta < 0:
        recommendation = "keep_variant_a"
    elif sample_size < 1000:
        recommendation = "collect_more_data"
    else:
        recommendation = "no_significant_difference"

    return {
        "p_value": round(p_value, 6),
        "confidence_level": round(confidence_level, 4),
        "is_significant": is_significant,
        "power": round(power, 4),
        "recommendation": recommendation,
    }


def _normal_cdf(x: float) -> float:
    """Standard normal CDF approximation (Abramowitz & Stegun)."""
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def _normal_ppf(p: float) -> float:
    """Inverse normal CDF approximation (Rational approximation).

    Accurate to ~4.5e-4 for 0.0027 < p < 0.9973.
    """
    if p <= 0 or p >= 1:
        return 0.0

    if p < 0.5:
        return -_normal_ppf(1 - p)

    t = math.sqrt(-2 * math.log(1 - p))
    c0 = 2.515517
    c1 = 0.802853
    c2 = 0.010328
    d1 = 1.432788
    d2 = 0.189269
    d3 = 0.001308

    return t - (c0 + c1 * t + c2 * t * t) / (1 + d1 * t + d2 * t * t + d3 * t * t * t)
