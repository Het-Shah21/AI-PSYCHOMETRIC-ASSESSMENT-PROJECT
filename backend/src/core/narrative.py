"""
Task 1.4 — Narrative and Puzzle Components within 5-Minute Timebox

Defines the narrative script, puzzle content, and time allocation
for each chamber. The narrative wraps around an overarching metaphor:
"The Abstract Enclave" — a liminal space between consciousness and
intuition where each chamber reveals a facet of the self.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final, Any


# ---------------------------------------------------------------------------
# Narrative Structure
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class NarrativeBeat:
    """A single narrative element (dialogue, description, or prompt)."""
    id: str
    text: str
    speaker: str = "narrator"       # narrator | guide | environment
    duration_ms: int = 3000         # Display duration
    trigger_emotion: str = ""       # Intended emotional tone
    is_skippable: bool = True


@dataclass(frozen=True)
class PuzzleComponent:
    """A puzzle element within a chamber interaction."""
    id: str
    puzzle_type: str               # pattern | logic | spatial | wordplay
    description: str
    solution: str
    difficulty: float              # [0, 1] — 0 = trivial, 1 = expert
    hints: tuple[str, ...] = ()
    time_limit_ms: int = 15000
    scoring_rubric: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class ChamberNarrative:
    """Complete narrative arc for a single chamber."""
    chamber_id: str
    title: str
    entry_beats: tuple[NarrativeBeat, ...] = ()
    interaction_transitions: tuple[NarrativeBeat, ...] = ()
    exit_beats: tuple[NarrativeBeat, ...] = ()
    puzzles: tuple[PuzzleComponent, ...] = ()
    time_budget_ms: int = 60_000


# ---------------------------------------------------------------------------
# Overarching Narrative
# ---------------------------------------------------------------------------

PROLOGUE: Final[tuple[NarrativeBeat, ...]] = (
    NarrativeBeat(
        id="prologue_1",
        text="You stand at the threshold of the Abstract Enclave — a space that exists between thought and feeling.",
        speaker="narrator", duration_ms=4000, trigger_emotion="wonder",
    ),
    NarrativeBeat(
        id="prologue_2",
        text="Within its chambers, there are no right or wrong answers. Only your authentic responses matter.",
        speaker="narrator", duration_ms=3500, trigger_emotion="safety",
    ),
    NarrativeBeat(
        id="prologue_3",
        text="A luminous guide materializes beside you. 'I'll be here throughout your journey. You can ask me anything.'",
        speaker="narrator", duration_ms=3500, trigger_emotion="trust",
    ),
    NarrativeBeat(
        id="prologue_4",
        text="Four chambers await. Each will take about a minute. Let your instincts guide you.",
        speaker="guide", duration_ms=3000, trigger_emotion="readiness",
    ),
)

EPILOGUE: Final[tuple[NarrativeBeat, ...]] = (
    NarrativeBeat(
        id="epilogue_1",
        text="The Enclave dims around you. The chambers have recorded your journey.",
        speaker="narrator", duration_ms=3000, trigger_emotion="completion",
    ),
    NarrativeBeat(
        id="epilogue_2",
        text="'Every choice, hesitation, and discovery painted a portrait of who you are today.'",
        speaker="guide", duration_ms=3500, trigger_emotion="reflection",
    ),
)


# ---------------------------------------------------------------------------
# Chamber Narratives with Puzzles
# ---------------------------------------------------------------------------

CHAMBER_NARRATIVES: Final[dict[str, ChamberNarrative]] = {
    "confidence": ChamberNarrative(
        chamber_id="confidence",
        title="The Decision Forge",
        time_budget_ms=60_000,
        entry_beats=(
            NarrativeBeat(
                id="conf_entry_1",
                text="Heat washes over you. An ancient forge pulses with molten light.",
                speaker="narrator", duration_ms=2500, trigger_emotion="intensity",
            ),
            NarrativeBeat(
                id="conf_entry_2",
                text="'Here, decisions are forged in fire. Hesitation costs heat.'",
                speaker="guide", duration_ms=2500, trigger_emotion="urgency",
            ),
        ),
        interaction_transitions=(
            NarrativeBeat(
                id="conf_trans_1",
                text="The metal shifts. Another challenge takes shape in the flames.",
                speaker="narrator", duration_ms=2000, trigger_emotion="anticipation",
            ),
            NarrativeBeat(
                id="conf_trans_2",
                text="Sparks fly as the forge tests your resolve once more.",
                speaker="narrator", duration_ms=2000, trigger_emotion="challenge",
            ),
        ),
        exit_beats=(
            NarrativeBeat(
                id="conf_exit_1",
                text="The flames subside. Your decisions are tempered into the blade of resolve.",
                speaker="narrator", duration_ms=2500, trigger_emotion="accomplishment",
            ),
        ),
        puzzles=(
            PuzzleComponent(
                id="conf_puzzle_runes",
                puzzle_type="pattern",
                description="Identify the true rune sequence from three plausible options",
                solution="Sequence A: ◆▲●◆▲●",
                difficulty=0.5,
                hints=("Look for the repeating unit of 3", "The pattern mirrors itself"),
                time_limit_ms=15000,
                scoring_rubric={
                    "correct_fast": 1.0,        # Correct + < 5s
                    "correct_moderate": 0.8,     # Correct + 5-10s
                    "correct_slow": 0.6,         # Correct + > 10s
                    "incorrect_committed": 0.3,  # Wrong but no revision
                    "incorrect_revised": 0.1,    # Wrong after changing answer
                },
            ),
        ),
    ),

    "curiosity": ChamberNarrative(
        chamber_id="curiosity",
        title="The Archive of Whispers",
        time_budget_ms=60_000,
        entry_beats=(
            NarrativeBeat(
                id="cur_entry_1",
                text="Infinite shelves stretch in every direction. Knowledge hides in unexpected places.",
                speaker="narrator", duration_ms=2500, trigger_emotion="wonder",
            ),
            NarrativeBeat(
                id="cur_entry_2",
                text="'Not everything here is meant to be found. But everything found has meaning.'",
                speaker="guide", duration_ms=2500, trigger_emotion="mystery",
            ),
        ),
        interaction_transitions=(
            NarrativeBeat(
                id="cur_trans_1",
                text="A book slides from its shelf, opening to a page that was waiting for you.",
                speaker="narrator", duration_ms=2000, trigger_emotion="curiosity",
            ),
        ),
        exit_beats=(
            NarrativeBeat(
                id="cur_exit_1",
                text="You carry more questions than answers. The Archive approves.",
                speaker="narrator", duration_ms=2500, trigger_emotion="satisfaction",
            ),
        ),
        puzzles=(
            PuzzleComponent(
                id="cur_puzzle_alcoves",
                puzzle_type="spatial",
                description="Explore 6 alcoves, each containing artifacts with clues",
                solution="alcove_3_hidden_passage leads to secret 7th alcove",
                difficulty=0.4,
                hints=("Some alcoves connect to others", "The whispers grow louder near secrets"),
                time_limit_ms=20000,
                scoring_rubric={
                    "all_explored": 1.0,       # Visited all 6+
                    "most_explored": 0.7,      # 4-5 alcoves
                    "some_explored": 0.4,      # 2-3 alcoves
                    "minimal": 0.1,            # 0-1 alcoves
                    "secret_found": 0.3,       # Bonus for hidden passage
                },
            ),
        ),
    ),

    "emotional_safety": ChamberNarrative(
        chamber_id="emotional_safety",
        title="The Mirror Garden",
        time_budget_ms=60_000,
        entry_beats=(
            NarrativeBeat(
                id="es_entry_1",
                text="Mirrors surround you, but they reflect feelings, not faces — colors pulse with your emotions.",
                speaker="narrator", duration_ms=3000, trigger_emotion="intimacy",
            ),
            NarrativeBeat(
                id="es_entry_2",
                text="'This is a safe space. Nothing you share here will be judged.'",
                speaker="guide", duration_ms=2500, trigger_emotion="safety",
            ),
        ),
        interaction_transitions=(
            NarrativeBeat(
                id="es_trans_1",
                text="The mirrors shift, revealing a new reflection.",
                speaker="narrator", duration_ms=2000, trigger_emotion="gentleness",
            ),
        ),
        exit_beats=(
            NarrativeBeat(
                id="es_exit_1",
                text="The mirrors dim softly. What you showed here was real, and that takes courage.",
                speaker="narrator", duration_ms=2500, trigger_emotion="warmth",
            ),
        ),
        puzzles=(),  # This chamber uses reflective prompts, not traditional puzzles
    ),

    "exploratory_power": ChamberNarrative(
        chamber_id="exploratory_power",
        title="The Uncharted Expanse",
        time_budget_ms=60_000,
        entry_beats=(
            NarrativeBeat(
                id="ep_entry_1",
                text="An endless landscape unfolds. Islands of knowledge float in fog.",
                speaker="narrator", duration_ms=2500, trigger_emotion="vastness",
            ),
            NarrativeBeat(
                id="ep_entry_2",
                text="'Chart what you find. Every discovery connects to something larger.'",
                speaker="guide", duration_ms=2500, trigger_emotion="purpose",
            ),
        ),
        interaction_transitions=(
            NarrativeBeat(
                id="ep_trans_1",
                text="New islands emerge from the fog as you venture deeper.",
                speaker="narrator", duration_ms=2000, trigger_emotion="discovery",
            ),
        ),
        exit_beats=(
            NarrativeBeat(
                id="ep_exit_1",
                text="Your map is drawn. Not all explorers cover the same ground — but all reveal who they are.",
                speaker="narrator", duration_ms=2500, trigger_emotion="insight",
            ),
        ),
        puzzles=(
            PuzzleComponent(
                id="ep_puzzle_islands",
                puzzle_type="spatial",
                description="Navigate 8 floating islands, discovering connections between them",
                solution="Islands 2→5→3→7 form the central mystery chain",
                difficulty=0.6,
                hints=(
                    "Some islands reference others",
                    "Revisiting with new knowledge reveals more",
                    "The connections form a story",
                ),
                time_limit_ms=25000,
                scoring_rubric={
                    "full_synthesis": 1.0,      # Found all connections + hypothesis
                    "partial_synthesis": 0.7,    # Found some connections
                    "broad_exploration": 0.5,    # High coverage, low synthesis
                    "deep_single": 0.4,          # Deep dive on few islands
                    "minimal": 0.1,              # Barely explored
                },
            ),
        ),
    ),
}


# ---------------------------------------------------------------------------
# Time Budget Validation
# ---------------------------------------------------------------------------

@dataclass
class TimeBudgetReport:
    """Validates that all narrative + puzzle content fits within time budget."""
    chamber_id: str
    narrative_ms: int = 0
    puzzle_ms: int = 0
    total_ms: int = 0
    budget_ms: int = 60_000
    is_within_budget: bool = True
    slack_ms: int = 0


def validate_chamber_timing(chamber_id: str) -> TimeBudgetReport:
    """Check if a chamber's content fits within its time budget."""
    narrative = CHAMBER_NARRATIVES.get(chamber_id)
    if not narrative:
        raise ValueError(f"Unknown chamber: {chamber_id}")

    narrative_ms = (
        sum(b.duration_ms for b in narrative.entry_beats)
        + sum(b.duration_ms for b in narrative.interaction_transitions)
        + sum(b.duration_ms for b in narrative.exit_beats)
    )
    puzzle_ms = sum(p.time_limit_ms for p in narrative.puzzles)
    total = narrative_ms + puzzle_ms
    budget = narrative.time_budget_ms

    return TimeBudgetReport(
        chamber_id=chamber_id,
        narrative_ms=narrative_ms,
        puzzle_ms=puzzle_ms,
        total_ms=total,
        budget_ms=budget,
        is_within_budget=total <= budget,
        slack_ms=budget - total,
    )


def validate_all_timings() -> list[TimeBudgetReport]:
    """Validate all chamber timings. Returns list of reports."""
    return [validate_chamber_timing(cid) for cid in CHAMBER_NARRATIVES]
