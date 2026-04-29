"""
Task 4.2 — Convergent Validity Study Framework

Provides tools to assess whether the behavioral assessment
correlates with established psychometric instruments:
  - BFI-2 (Big Five Inventory) → Confidence, Curiosity
  - CEI-II (Curiosity and Exploration Inventory) → Curiosity
  - PANAS (Positive/Negative Affect Schedule) → Emotional Safety
  - NEO-PI-R Openness → Exploratory Power

This module provides the statistical framework; actual validation
requires pilot data collection.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Final


@dataclass
class ValidityMetric:
    """A single convergent validity measurement."""
    our_construct: str
    reference_instrument: str
    reference_subscale: str
    expected_correlation: float   # Theoretical r value
    observed_correlation: float | None = None  # Filled after pilot
    sample_size: int = 0
    p_value: float | None = None
    is_significant: bool = False


@dataclass
class ValidityReport:
    """Complete validity report for all constructs."""
    metrics: list[ValidityMetric] = field(default_factory=list)
    overall_convergent_validity: float | None = None  # Average |r|
    minimum_sample_size: int = 200
    recommended_sample_size: int = 500


# Construct → Reference instrument mapping
VALIDITY_MATRIX: Final[list[ValidityMetric]] = [
    ValidityMetric("confidence", "BFI-2", "Extraversion-Assertiveness", expected_correlation=0.55),
    ValidityMetric("confidence", "GSE", "General Self-Efficacy", expected_correlation=0.65),
    ValidityMetric("curiosity", "CEI-II", "Exploration", expected_correlation=0.70),
    ValidityMetric("curiosity", "BFI-2", "Openness-Intellect", expected_correlation=0.50),
    ValidityMetric("emotional_safety", "PANAS", "Positive Affect (inv. Negative)", expected_correlation=0.45),
    ValidityMetric("emotional_safety", "PSI", "Psychological Safety Index", expected_correlation=0.60),
    ValidityMetric("exploratory_power", "NEO-PI-R", "Openness to Experience", expected_correlation=0.55),
    ValidityMetric("exploratory_power", "CEI-II", "Stretching", expected_correlation=0.50),
]


def pearson_r(x: list[float], y: list[float]) -> float:
    """Compute Pearson correlation coefficient."""
    n = len(x)
    if n != len(y) or n < 3:
        return 0.0
    mx, my = sum(x) / n, sum(y) / n
    sx = math.sqrt(sum((xi - mx) ** 2 for xi in x) / (n - 1))
    sy = math.sqrt(sum((yi - my) ** 2 for yi in y) / (n - 1))
    if sx == 0 or sy == 0:
        return 0.0
    cov = sum((x[i] - mx) * (y[i] - my) for i in range(n)) / (n - 1)
    return cov / (sx * sy)


def required_sample_size(
    expected_r: float, alpha: float = 0.05, power: float = 0.80
) -> int:
    """Compute required sample size for detecting a correlation.
    Uses Cohen's (1988) formula: n = ((zα + zβ) / arctanh(r))² + 3
    """
    z_alpha = 1.96 if alpha == 0.05 else 2.576
    z_beta = 0.84 if power == 0.80 else 1.28
    if abs(expected_r) < 0.01:
        return 1000
    fisher_z = math.atanh(expected_r)
    n = ((z_alpha + z_beta) / fisher_z) ** 2 + 3
    return int(math.ceil(n))


def generate_validity_report() -> ValidityReport:
    """Generate a validity study plan with sample size requirements."""
    metrics = [ValidityMetric(
        our_construct=m.our_construct,
        reference_instrument=m.reference_instrument,
        reference_subscale=m.reference_subscale,
        expected_correlation=m.expected_correlation,
    ) for m in VALIDITY_MATRIX]

    min_n = max(
        required_sample_size(m.expected_correlation) for m in metrics
    )

    return ValidityReport(
        metrics=metrics,
        minimum_sample_size=min_n,
        recommended_sample_size=max(min_n * 2, 500),
    )
