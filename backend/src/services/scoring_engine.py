"""
Task 4.1 — Bayesian Scoring Model with Confidence Intervals

Implements a Bayesian inference engine that:
  1. Maintains Beta distribution priors for each construct
  2. Updates posteriors with behavioral evidence (likelihood)
  3. Produces credible intervals (not just point estimates)
  4. Maps posterior means to 1–10 scale
  5. Handles missing data via prior predictive distribution

This replaces the simpler weighted aggregation from Task 1.3
for production use, while Task 1.3 remains as a fast fallback.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Final

from ..core.constructs import CONSTRUCTS, ConstructID, SubFacet, BehavioralIndicator
from ..core.scoring_model import (
    normalize_min_max, apply_polarity, scale_to_1_10,
    ConstructScore, SubFacetScore, IndicatorScore, AssessmentResult,
)


# ---------------------------------------------------------------------------
# Beta Distribution Parameters
# ---------------------------------------------------------------------------

@dataclass
class BetaParams:
    """Parameters for a Beta(α, β) distribution representing belief about a score."""
    alpha: float = 2.0   # Prior successes (default: mildly informative)
    beta: float = 2.0    # Prior failures

    @property
    def mean(self) -> float:
        return self.alpha / (self.alpha + self.beta)

    @property
    def variance(self) -> float:
        ab = self.alpha + self.beta
        return (self.alpha * self.beta) / (ab * ab * (ab + 1))

    @property
    def std(self) -> float:
        return math.sqrt(self.variance)

    def credible_interval(self, ci: float = 0.95) -> tuple[float, float]:
        """Approximate credible interval using normal approximation.
        For Beta with α,β > 5, normal approximation is reasonable.
        """
        z = 1.96 if ci == 0.95 else 2.576  # 95% or 99%
        lower = max(0.0, self.mean - z * self.std)
        upper = min(1.0, self.mean + z * self.std)
        return (lower, upper)

    def update(self, observation: float, strength: float = 1.0) -> None:
        """Bayesian update with a continuous observation in [0, 1].

        For Beta-Bernoulli: α += observation × strength, β += (1-observation) × strength
        """
        self.alpha += observation * strength
        self.beta += (1.0 - observation) * strength


# ---------------------------------------------------------------------------
# Bayesian Scoring Engine
# ---------------------------------------------------------------------------

class BayesianScoringEngine:
    """Full Bayesian scoring engine for psychometric assessment."""

    # Prior hyperparameters (weakly informative)
    DEFAULT_ALPHA: Final[float] = 2.0
    DEFAULT_BETA: Final[float] = 2.0

    def __init__(self):
        self.construct_priors: dict[str, BetaParams] = {}
        self.subfacet_priors: dict[str, BetaParams] = {}
        self._initialize_priors()

    def _initialize_priors(self) -> None:
        """Initialize Beta priors for all constructs and sub-facets."""
        for cid, construct in CONSTRUCTS.items():
            self.construct_priors[cid.value] = BetaParams(
                alpha=self.DEFAULT_ALPHA, beta=self.DEFAULT_BETA
            )
            for sf in construct.sub_facets:
                self.subfacet_priors[sf.id] = BetaParams(
                    alpha=self.DEFAULT_ALPHA, beta=self.DEFAULT_BETA
                )

    def update_with_signal(
        self,
        indicator: BehavioralIndicator,
        raw_value: float,
        sub_facet: SubFacet,
        construct_id: str,
    ) -> None:
        """Update posteriors with a single behavioral signal."""
        # Normalize and apply polarity
        normalized = normalize_min_max(raw_value, indicator.min_value, indicator.max_value)
        adjusted = apply_polarity(normalized, indicator.polarity)

        # Update sub-facet posterior
        strength = indicator.weight  # Higher weight = stronger evidence
        sf_prior = self.subfacet_priors.get(sub_facet.id)
        if sf_prior:
            sf_prior.update(adjusted, strength)

        # Update construct posterior (attenuated by sub-facet weight)
        construct_prior = self.construct_priors.get(construct_id)
        if construct_prior:
            construct_prior.update(adjusted, strength * sub_facet.weight)

    def score_construct(
        self, construct_id: str, raw_signals: dict[str, float]
    ) -> ConstructScore:
        """Score a construct using Bayesian posterior."""
        construct = CONSTRUCTS.get(ConstructID(construct_id))
        if not construct:
            raise ValueError(f"Unknown construct: {construct_id}")

        # Process all available signals
        evidence_count = 0
        sf_scores: list[SubFacetScore] = []

        for sf in construct.sub_facets:
            ind_scores: list[IndicatorScore] = []
            for ind in sf.indicators:
                if ind.id in raw_signals:
                    self.update_with_signal(ind, raw_signals[ind.id], sf, construct_id)

                    normalized = normalize_min_max(raw_signals[ind.id], ind.min_value, ind.max_value)
                    adjusted = apply_polarity(normalized, ind.polarity)
                    ind_scores.append(IndicatorScore(
                        indicator_id=ind.id,
                        raw_value=raw_signals[ind.id],
                        normalized_value=adjusted,
                        weighted_value=adjusted * ind.weight,
                    ))
                    evidence_count += 1

            sf_posterior = self.subfacet_priors.get(sf.id, BetaParams())
            sf_scores.append(SubFacetScore(
                sub_facet_id=sf.id,
                sub_facet_name=sf.name,
                indicator_scores=ind_scores,
                raw_score=sf_posterior.mean,
                weighted_score=sf_posterior.mean * sf.weight,
            ))

        # Construct posterior
        c_posterior = self.construct_priors.get(construct_id, BetaParams())
        ci = c_posterior.credible_interval(0.95)

        return ConstructScore(
            construct_id=construct_id,
            construct_name=construct.name,
            sub_facet_scores=sf_scores,
            raw_score=c_posterior.mean,
            scaled_score=scale_to_1_10(c_posterior.mean),
            confidence_lower=scale_to_1_10(ci[0]),
            confidence_upper=scale_to_1_10(ci[1]),
            evidence_count=evidence_count,
        )

    def score_full_assessment(
        self, session_id: str, raw_signals: dict[str, float]
    ) -> AssessmentResult:
        """Score all constructs and produce complete assessment."""
        construct_scores: dict[str, ConstructScore] = {}
        total_signals = 0

        for cid in CONSTRUCTS:
            cs = self.score_construct(cid.value, raw_signals)
            construct_scores[cid.value] = cs
            total_signals += cs.evidence_count

        total_possible = sum(c.indicator_count for c in CONSTRUCTS.values())
        completion = total_signals / total_possible if total_possible > 0 else 0.0

        return AssessmentResult(
            session_id=session_id,
            construct_scores=construct_scores,
            completion_pct=round(completion * 100, 1),
            total_signals=total_signals,
        )

    def get_posterior_summary(self) -> dict[str, dict]:
        """Get posterior summaries for all constructs."""
        return {
            cid: {
                "mean": round(params.mean, 3),
                "std": round(params.std, 3),
                "alpha": round(params.alpha, 2),
                "beta": round(params.beta, 2),
                "ci_95": tuple(round(v, 3) for v in params.credible_interval()),
            }
            for cid, params in self.construct_priors.items()
        }
