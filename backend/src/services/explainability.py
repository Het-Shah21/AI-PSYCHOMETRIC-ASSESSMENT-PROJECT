"""
Task 2.4 — Explainable AI Module for Score Justification

Produces human-readable explanations for each construct score by:
  1. Identifying top contributing indicators (feature importance)
  2. Generating evidence chains linking behaviors to scores
  3. Creating natural language narratives via LLM (with fallback)
  4. Providing confidence-calibrated uncertainty descriptions

Inspired by SHAP-like feature attribution adapted for
behavioral assessment context.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..core.scoring_model import ConstructScore, SubFacetScore, IndicatorScore
from ..core.constructs import CONSTRUCTS, ConstructID


# ---------------------------------------------------------------------------
# Explanation Data Structures
# ---------------------------------------------------------------------------

@dataclass
class EvidenceItem:
    """A single piece of behavioral evidence supporting a score."""
    indicator_id: str
    indicator_name: str
    observed_value: float
    normalized_value: float
    contribution: float       # How much this indicator contributed to the score
    direction: str            # "positive" or "negative" effect
    description: str          # Human-readable behavior description


@dataclass
class SubFacetExplanation:
    """Explanation for a single sub-facet score."""
    sub_facet_id: str
    sub_facet_name: str
    score: float
    weight: float
    evidence: list[EvidenceItem] = field(default_factory=list)
    narrative: str = ""


@dataclass
class ConstructExplanation:
    """Complete explanation for a construct score."""
    construct_id: str
    construct_name: str
    scaled_score: float
    confidence_interval: tuple[float, float] = (0.0, 0.0)
    sub_facet_explanations: list[SubFacetExplanation] = field(default_factory=list)
    top_contributors: list[EvidenceItem] = field(default_factory=list)
    overall_narrative: str = ""
    confidence_description: str = ""
    strengths: list[str] = field(default_factory=list)
    growth_areas: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Feature Attribution (SHAP-inspired)
# ---------------------------------------------------------------------------

def compute_indicator_contribution(
    indicator_score: IndicatorScore,
    sub_facet_weight: float,
) -> float:
    """Compute the contribution of an indicator to the final construct score.

    Contribution = indicator_weighted_value × sub_facet_weight
    This is a simplified Shapley-like attribution where each indicator's
    marginal contribution is its weighted score times the sub-facet weight.
    """
    return indicator_score.weighted_value * sub_facet_weight


def extract_evidence(
    construct_score: ConstructScore,
) -> list[EvidenceItem]:
    """Extract all evidence items from a construct score, sorted by |contribution|."""
    evidence: list[EvidenceItem] = []

    construct = CONSTRUCTS.get(ConstructID(construct_score.construct_id))
    if not construct:
        return evidence

    for sf_score, sf_def in zip(construct_score.sub_facet_scores, construct.sub_facets):
        for ind_score in sf_score.indicator_scores:
            # Find the indicator definition for metadata
            ind_def = next(
                (i for i in sf_def.indicators if i.id == ind_score.indicator_id),
                None,
            )
            if not ind_def:
                continue

            contribution = compute_indicator_contribution(ind_score, sf_def.weight)
            direction = "positive" if ind_score.normalized_value >= 0.5 else "negative"

            evidence.append(EvidenceItem(
                indicator_id=ind_score.indicator_id,
                indicator_name=ind_def.name,
                observed_value=ind_score.raw_value,
                normalized_value=ind_score.normalized_value,
                contribution=contribution,
                direction=direction,
                description=ind_def.description,
            ))

    evidence.sort(key=lambda e: abs(e.contribution), reverse=True)
    return evidence


# ---------------------------------------------------------------------------
# Explanation Generation
# ---------------------------------------------------------------------------

def describe_confidence_interval(
    score: float,
    ci_lower: float,
    ci_upper: float,
) -> str:
    """Generate human-readable confidence interval description."""
    width = ci_upper - ci_lower
    if width < 1.5:
        precision = "high confidence"
    elif width < 3.0:
        precision = "moderate confidence"
    else:
        precision = "preliminary estimate (more data would increase precision)"

    return (
        f"Score: {score}/10 ({precision}). "
        f"Based on observed behaviors, your true score likely falls "
        f"between {ci_lower} and {ci_upper}."
    )


def identify_strengths_and_growth(
    sub_facet_scores: list[SubFacetScore],
    construct_name: str,
) -> tuple[list[str], list[str]]:
    """Identify top strengths and growth areas from sub-facet scores."""
    strengths: list[str] = []
    growth: list[str] = []

    for sf in sub_facet_scores:
        if sf.raw_score >= 0.7:
            strengths.append(f"Strong {sf.sub_facet_name.lower()}")
        elif sf.raw_score <= 0.35:
            growth.append(f"{sf.sub_facet_name} could be further developed")

    return strengths, growth


def generate_explanation(
    construct_score: ConstructScore,
    llm_narrative: str | None = None,
) -> ConstructExplanation:
    """Generate a complete explanation for a construct score."""
    evidence = extract_evidence(construct_score)
    top_contributors = evidence[:5]  # Top 5 most impactful indicators

    # Sub-facet level explanations
    sf_explanations: list[SubFacetExplanation] = []
    for sf in construct_score.sub_facet_scores:
        sf_evidence = [e for e in evidence if any(
            i.indicator_id == e.indicator_id for i in sf.indicator_scores
        )]
        sf_explanations.append(SubFacetExplanation(
            sub_facet_id=sf.sub_facet_id,
            sub_facet_name=sf.sub_facet_name,
            score=round(sf.raw_score * 10, 1),
            weight=sf.weighted_score,
            evidence=sf_evidence,
        ))

    # Confidence description
    ci_desc = describe_confidence_interval(
        construct_score.scaled_score,
        construct_score.confidence_lower,
        construct_score.confidence_upper,
    )

    # Strengths and growth areas
    strengths, growth = identify_strengths_and_growth(
        construct_score.sub_facet_scores,
        construct_score.construct_name,
    )

    # Overall narrative (LLM or fallback)
    narrative = llm_narrative or _fallback_narrative(construct_score, top_contributors)

    return ConstructExplanation(
        construct_id=construct_score.construct_id,
        construct_name=construct_score.construct_name,
        scaled_score=construct_score.scaled_score,
        confidence_interval=(
            construct_score.confidence_lower,
            construct_score.confidence_upper,
        ),
        sub_facet_explanations=sf_explanations,
        top_contributors=top_contributors,
        overall_narrative=narrative,
        confidence_description=ci_desc,
        strengths=strengths,
        growth_areas=growth,
    )


def _fallback_narrative(
    score: ConstructScore,
    top_evidence: list[EvidenceItem],
) -> str:
    """Generate explanation without LLM."""
    level = "high" if score.scaled_score >= 7 else "moderate" if score.scaled_score >= 4 else "developing"

    evidence_text = ""
    if top_evidence:
        top = top_evidence[0]
        evidence_text = f" This was most strongly influenced by your {top.indicator_name.lower()}."

    return (
        f"Your {score.construct_name} score of {score.scaled_score}/10 "
        f"indicates a {level} level based on {score.evidence_count} behavioral "
        f"observations.{evidence_text}"
    )


def generate_full_report(
    construct_scores: dict[str, ConstructScore],
) -> dict[str, ConstructExplanation]:
    """Generate explanations for all constructs."""
    return {
        cid: generate_explanation(cs)
        for cid, cs in construct_scores.items()
    }
