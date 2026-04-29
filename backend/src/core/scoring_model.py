"""
Task 1.3 — Behavioral Metrics to Sub-Facet Mapping and Scoring Model

Implements the comprehensive scoring pipeline:
  1. Raw signal normalization (min-max with polarity)
  2. Indicator → sub-facet weighted aggregation
  3. Sub-facet → construct weighted aggregation
  4. Confidence interval estimation via bootstrap
  5. Final 1-10 scale mapping
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Final

from .constructs import (
    CONSTRUCTS,
    Construct,
    ConstructID,
    SubFacet,
    BehavioralIndicator,
)


# ---------------------------------------------------------------------------
# Score Data Structures
# ---------------------------------------------------------------------------

@dataclass
class IndicatorScore:
    """Score for a single behavioral indicator."""
    indicator_id: str
    raw_value: float
    normalized_value: float   # [0, 1] after polarity and min-max
    weighted_value: float     # normalized × weight


@dataclass
class SubFacetScore:
    """Aggregated score for a sub-facet."""
    sub_facet_id: str
    sub_facet_name: str
    indicator_scores: list[IndicatorScore] = field(default_factory=list)
    raw_score: float = 0.0        # Weighted sum of indicators [0, 1]
    weighted_score: float = 0.0   # raw_score × sub-facet weight


@dataclass
class ConstructScore:
    """Final score for a construct on the 1-10 scale."""
    construct_id: str
    construct_name: str
    sub_facet_scores: list[SubFacetScore] = field(default_factory=list)
    raw_score: float = 0.0         # Weighted sum of sub-facets [0, 1]
    scaled_score: float = 0.0      # Mapped to [1, 10]
    confidence_lower: float = 0.0  # 95% CI lower bound
    confidence_upper: float = 0.0  # 95% CI upper bound
    evidence_count: int = 0        # Number of signals used


@dataclass
class AssessmentResult:
    """Complete assessment result across all constructs."""
    session_id: str
    construct_scores: dict[str, ConstructScore] = field(default_factory=dict)
    overall_profile: str = ""
    completion_pct: float = 0.0
    total_signals: int = 0


# ---------------------------------------------------------------------------
# Normalization Functions
# ---------------------------------------------------------------------------

def normalize_min_max(value: float, min_val: float, max_val: float) -> float:
    """Min-max normalize a value to [0, 1]. Clamps out-of-range values."""
    if max_val == min_val:
        return 0.5
    clamped = max(min_val, min(max_val, value))
    return (clamped - min_val) / (max_val - min_val)


def apply_polarity(normalized: float, polarity: float) -> float:
    """Apply polarity transformation. polarity=-1 inverts the scale."""
    if polarity < 0:
        return 1.0 - normalized
    return normalized


def scale_to_1_10(value_0_1: float) -> float:
    """Map a [0, 1] value to [1, 10] scale with rounding to 1 decimal."""
    return round(1.0 + value_0_1 * 9.0, 1)


# ---------------------------------------------------------------------------
# Scoring Pipeline
# ---------------------------------------------------------------------------

def score_indicator(
    indicator: BehavioralIndicator,
    raw_value: float,
) -> IndicatorScore:
    """Score a single behavioral indicator from its raw captured value."""
    normalized = normalize_min_max(raw_value, indicator.min_value, indicator.max_value)
    polarity_adjusted = apply_polarity(normalized, indicator.polarity)
    weighted = polarity_adjusted * indicator.weight
    return IndicatorScore(
        indicator_id=indicator.id,
        raw_value=raw_value,
        normalized_value=polarity_adjusted,
        weighted_value=weighted,
    )


def score_sub_facet(
    sub_facet: SubFacet,
    raw_signals: dict[str, float],
) -> SubFacetScore:
    """Score a sub-facet by aggregating its indicators."""
    indicator_scores: list[IndicatorScore] = []
    total_weight = 0.0
    weighted_sum = 0.0

    for indicator in sub_facet.indicators:
        if indicator.id in raw_signals:
            iscore = score_indicator(indicator, raw_signals[indicator.id])
            indicator_scores.append(iscore)
            weighted_sum += iscore.weighted_value
            total_weight += indicator.weight

    # Normalize by actual weight used (handles missing signals gracefully)
    raw_score = weighted_sum / total_weight if total_weight > 0 else 0.5

    return SubFacetScore(
        sub_facet_id=sub_facet.id,
        sub_facet_name=sub_facet.name,
        indicator_scores=indicator_scores,
        raw_score=raw_score,
        weighted_score=raw_score * sub_facet.weight,
    )


def score_construct(
    construct: Construct,
    raw_signals: dict[str, float],
) -> ConstructScore:
    """Score a full construct by aggregating sub-facets."""
    sf_scores: list[SubFacetScore] = []
    total_weight = 0.0
    weighted_sum = 0.0
    evidence_count = 0

    for sf in construct.sub_facets:
        sf_score = score_sub_facet(sf, raw_signals)
        sf_scores.append(sf_score)
        weighted_sum += sf_score.weighted_score
        total_weight += sf.weight
        evidence_count += len(sf_score.indicator_scores)

    raw_score = weighted_sum / total_weight if total_weight > 0 else 0.5
    scaled = scale_to_1_10(raw_score)

    # Bootstrap confidence interval
    ci_lower, ci_upper = bootstrap_confidence_interval(
        sf_scores, n_bootstrap=200
    )

    return ConstructScore(
        construct_id=construct.id.value,
        construct_name=construct.name,
        sub_facet_scores=sf_scores,
        raw_score=raw_score,
        scaled_score=scaled,
        confidence_lower=scale_to_1_10(ci_lower),
        confidence_upper=scale_to_1_10(ci_upper),
        evidence_count=evidence_count,
    )


def score_full_assessment(
    session_id: str,
    raw_signals: dict[str, float],
) -> AssessmentResult:
    """Score all four constructs and produce a complete assessment result."""
    construct_scores: dict[str, ConstructScore] = {}
    total_signals = 0

    for cid, construct in CONSTRUCTS.items():
        cs = score_construct(construct, raw_signals)
        construct_scores[cid.value] = cs
        total_signals += cs.evidence_count

    # Determine completion percentage
    total_possible = sum(c.indicator_count for c in CONSTRUCTS.values())
    completion = total_signals / total_possible if total_possible > 0 else 0.0

    return AssessmentResult(
        session_id=session_id,
        construct_scores=construct_scores,
        overall_profile=generate_profile_label(construct_scores),
        completion_pct=round(completion * 100, 1),
        total_signals=total_signals,
    )


# ---------------------------------------------------------------------------
# Confidence Interval (Bootstrap)
# ---------------------------------------------------------------------------

def bootstrap_confidence_interval(
    sf_scores: list[SubFacetScore],
    n_bootstrap: int = 200,
    ci_level: float = 0.95,
) -> tuple[float, float]:
    """
    Non-parametric bootstrap CI for a construct score.
    Resamples indicator scores within sub-facets to estimate variability.
    """
    if not sf_scores or all(len(sf.indicator_scores) == 0 for sf in sf_scores):
        return (0.3, 0.7)  # Uninformative wide interval

    bootstrap_scores: list[float] = []

    for _ in range(n_bootstrap):
        resampled_sum = 0.0
        resampled_weight = 0.0
        for sf in sf_scores:
            if not sf.indicator_scores:
                continue
            # Resample indicators with replacement
            n = len(sf.indicator_scores)
            resampled = random.choices(sf.indicator_scores, k=n)
            sf_sum = sum(s.weighted_value for s in resampled)
            sf_total_w = sum(
                1.0 for _ in resampled  # Each resampled gets equal weight
            )
            sf_raw = sf_sum / (sf_total_w * (1.0 / n)) if sf_total_w > 0 else 0.5
            resampled_sum += sf_raw * sf.weighted_score / (sf.raw_score if sf.raw_score > 0 else 1)
            resampled_weight += sf.weighted_score / (sf.raw_score if sf.raw_score > 0 else 1) * 1.0

        score = resampled_sum / resampled_weight if resampled_weight > 0 else 0.5
        bootstrap_scores.append(max(0.0, min(1.0, score)))

    bootstrap_scores.sort()
    alpha = 1.0 - ci_level
    lower_idx = int(math.floor(alpha / 2 * n_bootstrap))
    upper_idx = int(math.ceil((1 - alpha / 2) * n_bootstrap)) - 1
    lower_idx = max(0, min(lower_idx, len(bootstrap_scores) - 1))
    upper_idx = max(0, min(upper_idx, len(bootstrap_scores) - 1))

    return (bootstrap_scores[lower_idx], bootstrap_scores[upper_idx])


# ---------------------------------------------------------------------------
# Profile Label Generation
# ---------------------------------------------------------------------------

PROFILE_THRESHOLDS: Final[dict[str, tuple[float, float, float]]] = {
    # (low_threshold, mid_threshold, high_threshold)
    "confidence": (3.5, 6.0, 8.0),
    "curiosity": (3.5, 6.0, 8.0),
    "emotional_safety": (3.5, 6.0, 8.0),
    "exploratory_power": (3.5, 6.0, 8.0),
}


def generate_profile_label(scores: dict[str, ConstructScore]) -> str:
    """Generate a human-readable profile archetype from construct scores."""
    labels: list[str] = []
    for cid, cs in scores.items():
        thresholds = PROFILE_THRESHOLDS.get(cid, (3.5, 6.0, 8.0))
        if cs.scaled_score >= thresholds[2]:
            labels.append(f"High {cs.construct_name}")
        elif cs.scaled_score >= thresholds[1]:
            labels.append(f"Moderate {cs.construct_name}")
        elif cs.scaled_score >= thresholds[0]:
            labels.append(f"Developing {cs.construct_name}")
        else:
            labels.append(f"Emerging {cs.construct_name}")

    return " | ".join(labels)
