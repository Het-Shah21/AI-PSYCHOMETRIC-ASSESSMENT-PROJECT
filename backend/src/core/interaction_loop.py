"""
Task 1.2 — Core Interaction Loop and Task Paradigm

Defines the interaction types, chamber progression logic, timing model,
and state transitions for the 5-minute assessment experience.

Each user session flows through 4 chambers (one per construct), with
each chamber containing 3-4 interactions of varied types. A reactive
state machine drives transitions based on user actions and time budgets.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Final, Any


# ---------------------------------------------------------------------------
# Interaction Types
# ---------------------------------------------------------------------------

class InteractionType(str, Enum):
    """Types of behavioral measurement interactions."""
    BINARY_CHOICE = "binary_choice"       # Two options, measures decisiveness
    MULTI_CHOICE = "multi_choice"         # 3-5 options, measures exploration
    TIMED_DECISION = "timed_decision"     # Choice under time pressure
    FREE_TEXT = "free_text"               # Open-ended text response
    SLIDER_RATING = "slider_rating"       # Continuous scale input
    SPATIAL_EXPLORATION = "spatial_exploration"  # Click/navigate a 2D space
    PUZZLE_SOLVE = "puzzle_solve"          # Logic/pattern puzzle
    DIALOGUE_EXCHANGE = "dialogue_exchange"  # AI companion conversation


class SessionPhase(str, Enum):
    """Phases of a complete assessment session."""
    CONSENT = "consent"
    MODE_SELECT = "mode_select"
    ONBOARDING = "onboarding"
    CHAMBER_ACTIVE = "chamber_active"
    CHAMBER_TRANSITION = "chamber_transition"
    SCORING = "scoring"
    RESULTS = "results"
    COMPLETED = "completed"


class DifficultyLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ADAPTIVE = "adaptive"


# ---------------------------------------------------------------------------
# Interaction Definition
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class InteractionConfig:
    """Configuration for a single interaction within a chamber."""
    id: str
    interaction_type: InteractionType
    prompt: str
    ai_context_prompt: str       # Prompt sent to LLM for adaptive content
    time_budget_ms: int          # Max time allowed (0 = unlimited)
    difficulty: DifficultyLevel
    options: tuple[str, ...] = ()          # For choice-based interactions
    hidden_elements: tuple[str, ...] = ()  # Optional discoverable content
    min_response_length: int = 0           # For free_text
    construct_target: str = ""             # Primary construct being measured
    signals_captured: tuple[str, ...] = () # IDs of BehavioralIndicators measured

    @property
    def is_timed(self) -> bool:
        return self.time_budget_ms > 0


@dataclass(frozen=True)
class ChamberConfig:
    """Configuration for a single assessment chamber."""
    id: str
    construct_id: str
    name: str
    theme: str
    description: str
    time_budget_ms: int          # Total time for this chamber
    interactions: tuple[InteractionConfig, ...] = ()
    entry_narrative: str = ""
    exit_narrative: str = ""
    ambient_color: str = "#1a1a2e"

    @property
    def interaction_count(self) -> int:
        return len(self.interactions)


# ---------------------------------------------------------------------------
# Timing Model
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TimingModel:
    """Global timing constraints for the 5-minute assessment."""
    total_session_ms: int = 300_000        # 5 minutes
    consent_budget_ms: int = 15_000        # 15s for consent
    onboarding_budget_ms: int = 20_000     # 20s intro
    per_chamber_budget_ms: int = 60_000    # 60s per chamber (4 × 60 = 240s)
    transition_budget_ms: int = 5_000      # 5s between chambers
    scoring_budget_ms: int = 10_000        # 10s for scoring animation
    buffer_ms: int = 10_000               # Slack time

    @property
    def active_assessment_ms(self) -> int:
        return self.per_chamber_budget_ms * 4

    def validate(self) -> bool:
        total = (
            self.consent_budget_ms
            + self.onboarding_budget_ms
            + self.active_assessment_ms
            + self.transition_budget_ms * 3  # 3 transitions between 4 chambers
            + self.scoring_budget_ms
            + self.buffer_ms
        )
        return total <= self.total_session_ms


TIMING: Final[TimingModel] = TimingModel()


# ---------------------------------------------------------------------------
# State Transition Model
# ---------------------------------------------------------------------------

@dataclass
class SessionState:
    """Mutable session state tracking current progress."""
    session_id: str = ""
    phase: SessionPhase = SessionPhase.CONSENT
    current_chamber_index: int = 0
    current_interaction_index: int = 0
    chamber_order: list[str] = field(default_factory=lambda: [
        "confidence", "curiosity", "emotional_safety", "exploratory_power"
    ])
    elapsed_ms: int = 0
    signals_collected: list[dict[str, Any]] = field(default_factory=list)
    is_consent_given: bool = False
    mode: str = ""

    @property
    def current_chamber_id(self) -> str:
        if self.current_chamber_index < len(self.chamber_order):
            return self.chamber_order[self.current_chamber_index]
        return ""

    @property
    def is_final_chamber(self) -> bool:
        return self.current_chamber_index >= len(self.chamber_order) - 1

    @property
    def progress_pct(self) -> float:
        total = len(self.chamber_order)
        if total == 0:
            return 0.0
        return (self.current_chamber_index / total) * 100


class TransitionEvent(str, Enum):
    """Events that trigger state transitions."""
    CONSENT_GIVEN = "consent_given"
    MODE_SELECTED = "mode_selected"
    ONBOARDING_COMPLETE = "onboarding_complete"
    INTERACTION_COMPLETE = "interaction_complete"
    CHAMBER_COMPLETE = "chamber_complete"
    TIME_EXPIRED = "time_expired"
    SCORING_COMPLETE = "scoring_complete"
    SESSION_ABORT = "session_abort"


# Transition table: (current_phase, event) → next_phase
TRANSITIONS: Final[dict[tuple[SessionPhase, TransitionEvent], SessionPhase]] = {
    (SessionPhase.CONSENT, TransitionEvent.CONSENT_GIVEN): SessionPhase.MODE_SELECT,
    (SessionPhase.MODE_SELECT, TransitionEvent.MODE_SELECTED): SessionPhase.ONBOARDING,
    (SessionPhase.ONBOARDING, TransitionEvent.ONBOARDING_COMPLETE): SessionPhase.CHAMBER_ACTIVE,
    (SessionPhase.CHAMBER_ACTIVE, TransitionEvent.INTERACTION_COMPLETE): SessionPhase.CHAMBER_ACTIVE,
    (SessionPhase.CHAMBER_ACTIVE, TransitionEvent.CHAMBER_COMPLETE): SessionPhase.CHAMBER_TRANSITION,
    (SessionPhase.CHAMBER_ACTIVE, TransitionEvent.TIME_EXPIRED): SessionPhase.CHAMBER_TRANSITION,
    (SessionPhase.CHAMBER_TRANSITION, TransitionEvent.CHAMBER_COMPLETE): SessionPhase.CHAMBER_ACTIVE,
    (SessionPhase.CHAMBER_TRANSITION, TransitionEvent.SCORING_COMPLETE): SessionPhase.SCORING,
    (SessionPhase.SCORING, TransitionEvent.SCORING_COMPLETE): SessionPhase.RESULTS,
    (SessionPhase.RESULTS, TransitionEvent.SESSION_ABORT): SessionPhase.COMPLETED,
}


def apply_transition(state: SessionState, event: TransitionEvent) -> SessionPhase:
    """Apply a transition event, returning the new phase. Raises ValueError on invalid transition."""
    key = (state.phase, event)
    if key not in TRANSITIONS:
        raise ValueError(f"Invalid transition: {state.phase.value} + {event.value}")
    new_phase = TRANSITIONS[key]
    state.phase = new_phase

    # Side effects
    if event == TransitionEvent.CHAMBER_COMPLETE and not state.is_final_chamber:
        state.current_chamber_index += 1
        state.current_interaction_index = 0

    return new_phase


# ---------------------------------------------------------------------------
# Chamber Definitions
# ---------------------------------------------------------------------------

CHAMBERS: Final[dict[str, ChamberConfig]] = {
    "confidence": ChamberConfig(
        id="confidence",
        construct_id="confidence",
        name="The Decision Forge",
        theme="Ancient forge where choices are tempered in fire",
        description="Test your conviction through decisive action under uncertainty.",
        time_budget_ms=60_000,
        ambient_color="#ff6b35",
        entry_narrative="You enter a dimly lit forge. Embers pulse with each heartbeat. The Artificer awaits your decisions...",
        exit_narrative="The metal has cooled. Your choices are forged into the blade of resolve.",
        interactions=(
            InteractionConfig(
                id="conf-1", interaction_type=InteractionType.TIMED_DECISION,
                prompt="Two paths diverge before you. One is well-lit and familiar. The other descends into shadow, but a faint melody echoes from its depths. You have 8 seconds.",
                ai_context_prompt="Generate a choice scenario testing decisiveness under time pressure",
                time_budget_ms=8000, difficulty=DifficultyLevel.MEDIUM,
                options=("Take the well-lit path", "Descend into the shadow"),
                construct_target="confidence",
                signals_captured=("conf_d_latency", "conf_d_choice"),
            ),
            InteractionConfig(
                id="conf-2", interaction_type=InteractionType.FREE_TEXT,
                prompt="The Artificer challenges you: 'Defend a belief you hold that others might disagree with. Speak with conviction.'",
                ai_context_prompt="Analyze the user's response for assertiveness, hedging language, and conviction markers",
                time_budget_ms=25000, difficulty=DifficultyLevel.HIGH,
                min_response_length=20,
                construct_target="confidence",
                signals_captured=("conf_sa_length", "conf_sa_sentiment"),
            ),
            InteractionConfig(
                id="conf-3", interaction_type=InteractionType.PUZZLE_SOLVE,
                prompt="A pattern of runes appears on the forge wall. Some are deliberately misleading. Identify the true sequence and commit — you cannot change your answer.",
                ai_context_prompt="Generate a pattern recognition puzzle with one clearly correct and two plausible-but-wrong answers",
                time_budget_ms=15000, difficulty=DifficultyLevel.ADAPTIVE,
                options=("Sequence A: ◆▲●◆▲●", "Sequence B: ◆●▲◆●▲", "Sequence C: ▲◆●▲◆●"),
                construct_target="confidence",
                signals_captured=("conf_d_latency", "conf_d_revision", "conf_mc_accuracy"),
            ),
        ),
    ),
    "curiosity": ChamberConfig(
        id="curiosity",
        construct_id="curiosity",
        name="The Archive of Whispers",
        theme="Infinite library where knowledge hides in unexpected places",
        description="Explore the unknown. What you discover reveals your nature.",
        time_budget_ms=60_000,
        ambient_color="#7b2ff7",
        entry_narrative="Shelves stretch infinitely. Books rearrange themselves. Some glow faintly, others seem to whisper...",
        exit_narrative="You leave the Archive carrying more questions than answers — and that is the point.",
        interactions=(
            InteractionConfig(
                id="cur-1", interaction_type=InteractionType.SPATIAL_EXPLORATION,
                prompt="You stand in a vast chamber with 6 alcoves. Each contains a different artifact. You have 20 seconds. Explore as many or as few as you wish.",
                ai_context_prompt="Track which alcoves the user explores, in what order, and for how long",
                time_budget_ms=20000, difficulty=DifficultyLevel.LOW,
                hidden_elements=("alcove_1_secret", "alcove_3_hidden_passage", "alcove_6_ancient_text"),
                construct_target="curiosity",
                signals_captured=("cur_je_explore", "cur_je_dwell", "cur_je_clicks"),
            ),
            InteractionConfig(
                id="cur-2", interaction_type=InteractionType.DIALOGUE_EXCHANGE,
                prompt="A spectral librarian appears: 'I have the answer to a question you haven't asked yet.' What would you like to know?",
                ai_context_prompt="Respond as a cryptic but helpful librarian. Evaluate the depth and creativity of the user's questions",
                time_budget_ms=20000, difficulty=DifficultyLevel.MEDIUM,
                construct_target="curiosity",
                signals_captured=("cur_ds_questions", "cur_ds_incomplete"),
            ),
            InteractionConfig(
                id="cur-3", interaction_type=InteractionType.MULTI_CHOICE,
                prompt="A half-torn page reveals partial information about a hidden treasure. Do you: search for the other half, proceed with partial info, ask the librarian, or ignore it entirely?",
                ai_context_prompt="Present deliberately incomplete information to measure deprivation sensitivity",
                time_budget_ms=12000, difficulty=DifficultyLevel.MEDIUM,
                options=("Search for the missing half", "Proceed with partial info", "Ask the spectral librarian", "Ignore and move on"),
                construct_target="curiosity",
                signals_captured=("cur_ds_incomplete", "cur_st_ambiguity"),
            ),
        ),
    ),
    "emotional_safety": ChamberConfig(
        id="emotional_safety",
        construct_id="emotional_safety",
        name="The Mirror Garden",
        theme="Reflective space where emotions become visible as light",
        description="A sanctuary of reflection where authenticity is valued above all.",
        time_budget_ms=60_000,
        ambient_color="#06d6a0",
        entry_narrative="Mirrors surround you, but they don't reflect your appearance — they reflect your feelings as colors and shapes...",
        exit_narrative="The mirrors dim. What you showed here was real, and that takes courage.",
        interactions=(
            InteractionConfig(
                id="es-1", interaction_type=InteractionType.FREE_TEXT,
                prompt="The mirror shows a moment from your past where you felt truly understood. Describe it — or describe what it would look like if it hasn't happened yet.",
                ai_context_prompt="Analyze self-disclosure depth, emotional vocabulary richness, and vulnerability markers",
                time_budget_ms=25000, difficulty=DifficultyLevel.LOW,
                min_response_length=15,
                construct_target="emotional_safety",
                signals_captured=("es_v_disclosure", "es_v_emotion_display"),
            ),
            InteractionConfig(
                id="es-2", interaction_type=InteractionType.BINARY_CHOICE,
                prompt="You solved the last puzzle incorrectly. The guide says: 'That wasn't right, but it showed creative thinking.' How do you feel?",
                ai_context_prompt="Inject mild failure feedback and observe post-error recovery behavior",
                time_budget_ms=10000, difficulty=DifficultyLevel.MEDIUM,
                options=("I'd like to try again differently", "I'd rather move forward to something new"),
                construct_target="emotional_safety",
                signals_captured=("es_ec_post_error", "es_ec_abandon"),
            ),
            InteractionConfig(
                id="es-3", interaction_type=InteractionType.SLIDER_RATING,
                prompt="On a scale, how comfortable are you asking for help when you're stuck? (Not at all → Completely comfortable)",
                ai_context_prompt="Compare stated comfort with actual help-seeking behavior observed in previous chambers",
                time_budget_ms=8000, difficulty=DifficultyLevel.LOW,
                construct_target="emotional_safety",
                signals_captured=("es_ha_help_freq", "es_ae_consistency"),
            ),
        ),
    ),
    "exploratory_power": ChamberConfig(
        id="exploratory_power",
        construct_id="exploratory_power",
        name="The Uncharted Expanse",
        theme="Vast terrain with hidden connections between discoveries",
        description="Map the unknown. Every discovery connects to something larger.",
        time_budget_ms=60_000,
        ambient_color="#118ab2",
        entry_narrative="An endless landscape unfolds before you. Islands of knowledge float in a sea of fog. Your task: chart what you find...",
        exit_narrative="Your map is drawn. Not all explorers cover the same ground — but all reveal who they are by what they seek.",
        interactions=(
            InteractionConfig(
                id="ep-1", interaction_type=InteractionType.SPATIAL_EXPLORATION,
                prompt="You see 8 floating islands. Each reveals a clue about a central mystery. Explore strategically — you can revisit, but time is limited.",
                ai_context_prompt="Track exploration breadth (coverage), depth (time per island), and revisitation patterns",
                time_budget_ms=25000, difficulty=DifficultyLevel.MEDIUM,
                hidden_elements=("island_2_connection", "island_5_link_to_3", "island_7_synthesis_clue"),
                construct_target="exploratory_power",
                signals_captured=("ep_b_coverage", "ep_b_diversity", "ep_d_time_per_area", "ep_d_revisit"),
            ),
            InteractionConfig(
                id="ep-2", interaction_type=InteractionType.FREE_TEXT,
                prompt="Based on your exploration, what do you think the central mystery is? Form a hypothesis.",
                ai_context_prompt="Evaluate hypothesis quality: specificity, evidence citation, logical structure",
                time_budget_ms=20000, difficulty=DifficultyLevel.HIGH,
                min_response_length=20,
                construct_target="exploratory_power",
                signals_captured=("ep_h_text_quality", "ep_h_testing"),
            ),
            InteractionConfig(
                id="ep-3", interaction_type=InteractionType.MULTI_CHOICE,
                prompt="New information contradicts your earlier discovery on Island 3. How do you proceed?",
                ai_context_prompt="Present contradictory evidence to measure synthesis ability and cognitive flexibility",
                time_budget_ms=12000, difficulty=DifficultyLevel.HIGH,
                options=(
                    "Revisit Island 3 with new perspective",
                    "Integrate both pieces of info into revised hypothesis",
                    "Discard the contradictory info",
                    "Ask for help resolving the contradiction",
                ),
                construct_target="exploratory_power",
                signals_captured=("ep_s_connection", "ep_s_summary"),
            ),
        ),
    ),
}


def get_chamber(chamber_id: str) -> ChamberConfig:
    """Retrieve a chamber configuration by ID."""
    if chamber_id not in CHAMBERS:
        raise ValueError(f"Unknown chamber: {chamber_id}")
    return CHAMBERS[chamber_id]


def get_interaction(chamber_id: str, interaction_id: str) -> InteractionConfig:
    """Retrieve a specific interaction within a chamber."""
    chamber = get_chamber(chamber_id)
    for interaction in chamber.interactions:
        if interaction.id == interaction_id:
            return interaction
    raise ValueError(f"Unknown interaction {interaction_id} in chamber {chamber_id}")


def get_session_flow() -> list[dict[str, Any]]:
    """Return the full session flow for API consumption."""
    return [
        {
            "chamber_id": cid,
            "chamber_name": c.name,
            "interaction_count": c.interaction_count,
            "time_budget_ms": c.time_budget_ms,
        }
        for cid, c in CHAMBERS.items()
    ]
