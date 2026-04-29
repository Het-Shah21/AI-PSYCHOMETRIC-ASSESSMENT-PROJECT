"""
Task 1.1 — Construct Operationalization Module

Defines the four psychological constructs (Confidence, Curiosity,
Emotional Safety, Exploratory Power), their sub-facets, and
observable behavioral indicators grounded in peer-reviewed literature.

References:
  - Bandura (1997) Self-Efficacy
  - Kashdan et al. (2018) Curiosity (5-Dimensional)
  - Edmondson (1999) Psychological Safety
  - Berlyne (1966) Exploratory Behavior
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Final


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class SignalType(str, Enum):
    """Categories of raw behavioral signals captured during assessment."""
    LATENCY = "latency"                # Response time in ms
    CHOICE = "choice"                  # Categorical selection
    REVISION = "revision"              # Changed answer count
    DWELL = "dwell"                    # Time spent on area (ms)
    TEXT_LENGTH = "text_length"        # Character count of free text
    TEXT_SENTIMENT = "text_sentiment"  # NLP sentiment polarity [-1,1]
    EXPLORATION = "exploration"        # % of optional areas visited
    CLICK_PATTERN = "click_pattern"    # Hesitation / rapid-click ratio
    SCROLL_DEPTH = "scroll_depth"     # Max scroll percentage
    HELP_SEEK = "help_seek"           # Times user requested help
    EMOTION = "emotion"               # Webcam-derived emotion label
    UNCERTAINTY_RESPONSE = "uncertainty_response"  # Reaction to injected ambiguity


class ConstructID(str, Enum):
    CONFIDENCE = "confidence"
    CURIOSITY = "curiosity"
    EMOTIONAL_SAFETY = "emotional_safety"
    EXPLORATORY_POWER = "exploratory_power"


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BehavioralIndicator:
    """A single measurable behavioral signal mapped to a sub-facet."""
    id: str
    name: str
    description: str
    signal_type: SignalType
    polarity: float          # +1 = higher value → higher construct score; -1 = inverse
    weight: float            # Relative importance within sub-facet [0, 1]
    min_value: float = 0.0
    max_value: float = 1.0


@dataclass(frozen=True)
class SubFacet:
    """A measurable dimension within a construct."""
    id: str
    name: str
    description: str
    weight: float  # Relative weight within parent construct [0, 1]
    indicators: tuple[BehavioralIndicator, ...] = field(default_factory=tuple)
    literature_ref: str = ""


@dataclass(frozen=True)
class Construct:
    """A top-level psychological construct with sub-facets."""
    id: ConstructID
    name: str
    definition: str
    theoretical_basis: str
    sub_facets: tuple[SubFacet, ...] = field(default_factory=tuple)

    @property
    def all_indicators(self) -> list[BehavioralIndicator]:
        return [ind for sf in self.sub_facets for ind in sf.indicators]

    @property
    def indicator_count(self) -> int:
        return len(self.all_indicators)


# ---------------------------------------------------------------------------
# Construct Definitions
# ---------------------------------------------------------------------------

CONFIDENCE: Final[Construct] = Construct(
    id=ConstructID.CONFIDENCE,
    name="Confidence",
    definition=(
        "The degree to which an individual trusts their own judgment, "
        "commits to decisions under uncertainty, and maintains behavioral "
        "consistency without excessive second-guessing."
    ),
    theoretical_basis=(
        "Bandura's Self-Efficacy Theory (1997): belief in one's capability "
        "to execute courses of action. Supplemented by Stankov's (2013) "
        "metacognitive confidence calibration research."
    ),
    sub_facets=(
        SubFacet(
            id="conf_decisiveness",
            name="Decisiveness",
            description="Speed and commitment in making choices under ambiguity.",
            weight=0.30,
            literature_ref="Bandura (1997); Kruger & Dunning (1999)",
            indicators=(
                BehavioralIndicator(
                    id="conf_d_latency", name="Decision Latency",
                    description="Time from stimulus onset to first committed choice",
                    signal_type=SignalType.LATENCY, polarity=-1.0, weight=0.5,
                    min_value=500, max_value=15000,
                ),
                BehavioralIndicator(
                    id="conf_d_revision", name="Answer Revisions",
                    description="Number of times user changes selected answer",
                    signal_type=SignalType.REVISION, polarity=-1.0, weight=0.3,
                    min_value=0, max_value=5,
                ),
                BehavioralIndicator(
                    id="conf_d_choice", name="Bold Choice Selection",
                    description="Selection of higher-risk/non-default options",
                    signal_type=SignalType.CHOICE, polarity=1.0, weight=0.2,
                    min_value=0, max_value=1,
                ),
            ),
        ),
        SubFacet(
            id="conf_persistence",
            name="Persistence Under Pressure",
            description="Sustained engagement when difficulty increases or feedback is negative.",
            weight=0.25,
            literature_ref="Duckworth (2007) Grit Scale; Bandura (1997)",
            indicators=(
                BehavioralIndicator(
                    id="conf_p_dwell", name="Post-Difficulty Dwell Time",
                    description="Time spent after encountering a hard challenge vs. abandoning",
                    signal_type=SignalType.DWELL, polarity=1.0, weight=0.5,
                    min_value=0, max_value=30000,
                ),
                BehavioralIndicator(
                    id="conf_p_retry", name="Retry After Failure",
                    description="Whether user re-attempts after receiving negative feedback",
                    signal_type=SignalType.CHOICE, polarity=1.0, weight=0.5,
                    min_value=0, max_value=1,
                ),
            ),
        ),
        SubFacet(
            id="conf_self_assurance",
            name="Self-Assurance in Expression",
            description="Assertiveness and conviction in free-text and verbal responses.",
            weight=0.25,
            literature_ref="Stankov (2013); Pennebaker (2001) linguistic markers",
            indicators=(
                BehavioralIndicator(
                    id="conf_sa_length", name="Response Elaboration",
                    description="Length and detail of free-text answers",
                    signal_type=SignalType.TEXT_LENGTH, polarity=1.0, weight=0.4,
                    min_value=0, max_value=500,
                ),
                BehavioralIndicator(
                    id="conf_sa_sentiment", name="Assertive Language",
                    description="Use of definitive vs. hedging language (NLP)",
                    signal_type=SignalType.TEXT_SENTIMENT, polarity=1.0, weight=0.6,
                    min_value=-1, max_value=1,
                ),
            ),
        ),
        SubFacet(
            id="conf_calibration",
            name="Metacognitive Calibration",
            description="Alignment between confidence expression and actual accuracy.",
            weight=0.20,
            literature_ref="Stankov & Lee (2014); Lichtenstein et al. (1982)",
            indicators=(
                BehavioralIndicator(
                    id="conf_mc_accuracy", name="Confidence-Accuracy Match",
                    description="Correlation between stated confidence and objective correctness",
                    signal_type=SignalType.CHOICE, polarity=1.0, weight=0.6,
                    min_value=0, max_value=1,
                ),
                BehavioralIndicator(
                    id="conf_mc_help", name="Appropriate Help-Seeking",
                    description="Requesting help when genuinely uncertain (not over/under-seeking)",
                    signal_type=SignalType.HELP_SEEK, polarity=1.0, weight=0.4,
                    min_value=0, max_value=1,
                ),
            ),
        ),
    ),
)

CURIOSITY: Final[Construct] = Construct(
    id=ConstructID.CURIOSITY,
    name="Curiosity",
    definition=(
        "The intrinsic drive to seek novel information, explore unknown "
        "territories, and engage with complexity beyond task requirements."
    ),
    theoretical_basis=(
        "Kashdan et al. (2018) Five-Dimensional Curiosity Scale: Joyous "
        "Exploration, Deprivation Sensitivity, Stress Tolerance, Social "
        "Curiosity, Thrill Seeking. Berlyne (1960) epistemic curiosity."
    ),
    sub_facets=(
        SubFacet(
            id="cur_joyous_exploration",
            name="Joyous Exploration",
            description="Pleasure derived from discovering new information and experiences.",
            weight=0.30,
            literature_ref="Kashdan et al. (2018); Litman (2008)",
            indicators=(
                BehavioralIndicator(
                    id="cur_je_explore", name="Optional Area Exploration",
                    description="Percentage of non-required interactive elements engaged with",
                    signal_type=SignalType.EXPLORATION, polarity=1.0, weight=0.5,
                    min_value=0, max_value=1,
                ),
                BehavioralIndicator(
                    id="cur_je_dwell", name="Discovery Dwell Time",
                    description="Time spent examining discovered optional content",
                    signal_type=SignalType.DWELL, polarity=1.0, weight=0.3,
                    min_value=0, max_value=20000,
                ),
                BehavioralIndicator(
                    id="cur_je_clicks", name="Exploratory Click Rate",
                    description="Rate of clicks on novel vs. familiar elements",
                    signal_type=SignalType.CLICK_PATTERN, polarity=1.0, weight=0.2,
                    min_value=0, max_value=1,
                ),
            ),
        ),
        SubFacet(
            id="cur_deprivation_sensitivity",
            name="Deprivation Sensitivity",
            description="Need to resolve gaps in knowledge; discomfort with not knowing.",
            weight=0.25,
            literature_ref="Loewenstein (1994) Information Gap Theory",
            indicators=(
                BehavioralIndicator(
                    id="cur_ds_incomplete", name="Incomplete Info Response",
                    description="Behavior when presented with deliberately incomplete information",
                    signal_type=SignalType.UNCERTAINTY_RESPONSE, polarity=1.0, weight=0.6,
                    min_value=0, max_value=1,
                ),
                BehavioralIndicator(
                    id="cur_ds_questions", name="Question Asking",
                    description="Frequency and depth of questions posed to AI companion",
                    signal_type=SignalType.TEXT_LENGTH, polarity=1.0, weight=0.4,
                    min_value=0, max_value=300,
                ),
            ),
        ),
        SubFacet(
            id="cur_stress_tolerance",
            name="Stress Tolerance in Exploration",
            description="Willingness to explore despite uncertainty or anxiety triggers.",
            weight=0.20,
            literature_ref="Kashdan et al. (2018); Silvia (2008)",
            indicators=(
                BehavioralIndicator(
                    id="cur_st_ambiguity", name="Ambiguity Engagement",
                    description="Continued exploration when facing ambiguous/uncertain content",
                    signal_type=SignalType.UNCERTAINTY_RESPONSE, polarity=1.0, weight=0.5,
                    min_value=0, max_value=1,
                ),
                BehavioralIndicator(
                    id="cur_st_emotion", name="Emotional Stability in Novel Contexts",
                    description="Webcam-derived affect stability during exploration",
                    signal_type=SignalType.EMOTION, polarity=1.0, weight=0.5,
                    min_value=0, max_value=1,
                ),
            ),
        ),
        SubFacet(
            id="cur_depth_seeking",
            name="Depth-Seeking Behavior",
            description="Preference for deep engagement over surface-level scanning.",
            weight=0.25,
            literature_ref="Berlyne (1966); Litman & Jimerson (2004)",
            indicators=(
                BehavioralIndicator(
                    id="cur_dsb_scroll", name="Content Depth Engagement",
                    description="Scroll depth and reading time on detailed content",
                    signal_type=SignalType.SCROLL_DEPTH, polarity=1.0, weight=0.5,
                    min_value=0, max_value=1,
                ),
                BehavioralIndicator(
                    id="cur_dsb_detail", name="Detail-Oriented Responses",
                    description="Specificity and depth in free-text answers",
                    signal_type=SignalType.TEXT_LENGTH, polarity=1.0, weight=0.5,
                    min_value=0, max_value=500,
                ),
            ),
        ),
    ),
)

EMOTIONAL_SAFETY: Final[Construct] = Construct(
    id=ConstructID.EMOTIONAL_SAFETY,
    name="Emotional Safety",
    definition=(
        "The degree to which an individual feels secure to express authentic "
        "emotions, take interpersonal risks, and engage vulnerably without "
        "fear of negative judgment."
    ),
    theoretical_basis=(
        "Edmondson (1999) Psychological Safety; Rogers (1961) unconditional "
        "positive regard; Bowlby (1969) Attachment Theory secure base."
    ),
    sub_facets=(
        SubFacet(
            id="es_vulnerability",
            name="Vulnerability Willingness",
            description="Readiness to share personal/emotional content openly.",
            weight=0.30,
            literature_ref="Brown (2012); Edmondson (1999)",
            indicators=(
                BehavioralIndicator(
                    id="es_v_disclosure", name="Self-Disclosure Depth",
                    description="Personal content depth in free-text (NLP analysis)",
                    signal_type=SignalType.TEXT_SENTIMENT, polarity=1.0, weight=0.5,
                    min_value=0, max_value=1,
                ),
                BehavioralIndicator(
                    id="es_v_emotion_display", name="Emotional Expression",
                    description="Range and authenticity of emotions shown via webcam",
                    signal_type=SignalType.EMOTION, polarity=1.0, weight=0.5,
                    min_value=0, max_value=1,
                ),
            ),
        ),
        SubFacet(
            id="es_error_comfort",
            name="Comfort with Errors",
            description="Equanimity when making mistakes; absence of catastrophizing.",
            weight=0.25,
            literature_ref="Edmondson (1999); Dweck (2006) Growth Mindset",
            indicators=(
                BehavioralIndicator(
                    id="es_ec_post_error", name="Post-Error Behavior",
                    description="Recovery speed and re-engagement after incorrect answers",
                    signal_type=SignalType.LATENCY, polarity=-1.0, weight=0.5,
                    min_value=500, max_value=15000,
                ),
                BehavioralIndicator(
                    id="es_ec_abandon", name="Non-Abandonment Rate",
                    description="Continued participation after errors vs. quitting/skipping",
                    signal_type=SignalType.CHOICE, polarity=1.0, weight=0.5,
                    min_value=0, max_value=1,
                ),
            ),
        ),
        SubFacet(
            id="es_help_acceptance",
            name="Help-Seeking Openness",
            description="Willingness to request and accept assistance without shame.",
            weight=0.20,
            literature_ref="Ryan & Pintrich (1997); Newman (2000)",
            indicators=(
                BehavioralIndicator(
                    id="es_ha_help_freq", name="Help Request Frequency",
                    description="Rate of voluntary help-seeking from AI companion",
                    signal_type=SignalType.HELP_SEEK, polarity=1.0, weight=0.5,
                    min_value=0, max_value=10,
                ),
                BehavioralIndicator(
                    id="es_ha_help_follow", name="Help Utilization",
                    description="Whether user applies advice given after requesting help",
                    signal_type=SignalType.CHOICE, polarity=1.0, weight=0.5,
                    min_value=0, max_value=1,
                ),
            ),
        ),
        SubFacet(
            id="es_authentic_expression",
            name="Authentic Expression",
            description="Genuine vs. socially desirable responses.",
            weight=0.25,
            literature_ref="Rogers (1961); Paulhus (1991) social desirability",
            indicators=(
                BehavioralIndicator(
                    id="es_ae_consistency", name="Response Consistency",
                    description="Coherence between behavioral signals and stated preferences",
                    signal_type=SignalType.CHOICE, polarity=1.0, weight=0.5,
                    min_value=0, max_value=1,
                ),
                BehavioralIndicator(
                    id="es_ae_unique", name="Unique Response Rate",
                    description="Proportion of non-default/non-modal answer choices",
                    signal_type=SignalType.CHOICE, polarity=1.0, weight=0.5,
                    min_value=0, max_value=1,
                ),
            ),
        ),
    ),
)

EXPLORATORY_POWER: Final[Construct] = Construct(
    id=ConstructID.EXPLORATORY_POWER,
    name="Exploratory Power",
    definition=(
        "The capacity and inclination to systematically investigate novel "
        "environments, generate creative hypotheses, and synthesize "
        "disparate information into coherent understanding."
    ),
    theoretical_basis=(
        "Berlyne (1966) specific vs. diversive exploration; Guilford (1967) "
        "divergent thinking; Kolb (1984) experiential learning cycle."
    ),
    sub_facets=(
        SubFacet(
            id="ep_breadth",
            name="Exploration Breadth",
            description="Range and diversity of areas investigated.",
            weight=0.25,
            literature_ref="Berlyne (1966); Hills et al. (2015)",
            indicators=(
                BehavioralIndicator(
                    id="ep_b_coverage", name="Area Coverage",
                    description="Percentage of available interactive zones visited",
                    signal_type=SignalType.EXPLORATION, polarity=1.0, weight=0.5,
                    min_value=0, max_value=1,
                ),
                BehavioralIndicator(
                    id="ep_b_diversity", name="Choice Diversity",
                    description="Entropy of selections across available options",
                    signal_type=SignalType.CLICK_PATTERN, polarity=1.0, weight=0.5,
                    min_value=0, max_value=1,
                ),
            ),
        ),
        SubFacet(
            id="ep_depth",
            name="Exploration Depth",
            description="Thoroughness and analytical quality of investigation.",
            weight=0.25,
            literature_ref="Chi et al. (1981); Berlyne (1966)",
            indicators=(
                BehavioralIndicator(
                    id="ep_d_time_per_area", name="Time Per Discovery",
                    description="Average dwell time on each new area discovered",
                    signal_type=SignalType.DWELL, polarity=1.0, weight=0.5,
                    min_value=0, max_value=15000,
                ),
                BehavioralIndicator(
                    id="ep_d_revisit", name="Strategic Revisitation",
                    description="Returning to previously explored areas with new information",
                    signal_type=SignalType.CLICK_PATTERN, polarity=1.0, weight=0.5,
                    min_value=0, max_value=1,
                ),
            ),
        ),
        SubFacet(
            id="ep_hypothesis",
            name="Hypothesis Generation",
            description="Formulating and testing predictions during exploration.",
            weight=0.25,
            literature_ref="Guilford (1967); Klahr & Dunbar (1988)",
            indicators=(
                BehavioralIndicator(
                    id="ep_h_text_quality", name="Hypothesis Articulation",
                    description="Quality and specificity of predictions in free-text",
                    signal_type=SignalType.TEXT_LENGTH, polarity=1.0, weight=0.5,
                    min_value=0, max_value=500,
                ),
                BehavioralIndicator(
                    id="ep_h_testing", name="Systematic Testing",
                    description="Sequential exploration patterns suggesting hypothesis testing",
                    signal_type=SignalType.CLICK_PATTERN, polarity=1.0, weight=0.5,
                    min_value=0, max_value=1,
                ),
            ),
        ),
        SubFacet(
            id="ep_synthesis",
            name="Information Synthesis",
            description="Integrating discoveries into coherent understanding.",
            weight=0.25,
            literature_ref="Kolb (1984); Bloom (1956) taxonomy — synthesis level",
            indicators=(
                BehavioralIndicator(
                    id="ep_s_connection", name="Cross-Reference Behavior",
                    description="Linking separate discoveries (revisiting after new info)",
                    signal_type=SignalType.CLICK_PATTERN, polarity=1.0, weight=0.5,
                    min_value=0, max_value=1,
                ),
                BehavioralIndicator(
                    id="ep_s_summary", name="Synthesis Quality",
                    description="Quality of summary/integration responses in free-text",
                    signal_type=SignalType.TEXT_LENGTH, polarity=1.0, weight=0.5,
                    min_value=0, max_value=500,
                ),
            ),
        ),
    ),
)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

CONSTRUCTS: Final[dict[ConstructID, Construct]] = {
    ConstructID.CONFIDENCE: CONFIDENCE,
    ConstructID.CURIOSITY: CURIOSITY,
    ConstructID.EMOTIONAL_SAFETY: EMOTIONAL_SAFETY,
    ConstructID.EXPLORATORY_POWER: EXPLORATORY_POWER,
}


def get_all_indicators() -> list[BehavioralIndicator]:
    """Return a flat list of every behavioral indicator across all constructs."""
    return [ind for c in CONSTRUCTS.values() for ind in c.all_indicators]


def get_indicator_by_id(indicator_id: str) -> BehavioralIndicator | None:
    """Look up a single indicator by its unique ID."""
    for indicator in get_all_indicators():
        if indicator.id == indicator_id:
            return indicator
    return None


def get_construct_summary() -> dict[str, dict]:
    """Return a JSON-serializable summary of all constructs for API responses."""
    return {
        c.id.value: {
            "name": c.name,
            "definition": c.definition,
            "sub_facets": [
                {
                    "id": sf.id,
                    "name": sf.name,
                    "weight": sf.weight,
                    "indicator_count": len(sf.indicators),
                }
                for sf in c.sub_facets
            ],
            "total_indicators": c.indicator_count,
        }
        for c in CONSTRUCTS.values()
    }
