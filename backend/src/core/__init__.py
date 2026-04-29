# Core module — Construct definitions, scoring models, narrative logic
from .constructs import CONSTRUCTS, Construct, SubFacet, BehavioralIndicator, SignalType
from .interaction_loop import (
    CHAMBERS, TIMING, TRANSITIONS,
    InteractionType, SessionPhase, DifficultyLevel, TransitionEvent,
    InteractionConfig, ChamberConfig, SessionState, TimingModel,
    apply_transition, get_chamber, get_interaction, get_session_flow,
)
from .scoring_model import (
    score_full_assessment, score_construct, score_sub_facet,
    AssessmentResult, ConstructScore, SubFacetScore, IndicatorScore,
)
from .narrative import (
    CHAMBER_NARRATIVES, PROLOGUE, EPILOGUE,
    ChamberNarrative, NarrativeBeat, PuzzleComponent,
    validate_all_timings,
)
