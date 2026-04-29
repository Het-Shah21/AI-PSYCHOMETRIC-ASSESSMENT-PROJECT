"""
Phase 1 Tests — Theoretical Foundation & Construct Operationalization

Task 1.1: Construct definitions, sub-facets, behavioral indicators
Task 1.2: Interaction loop, FSM, timing model
Task 1.3: Scoring model, normalization, aggregation
Task 1.4: Narrative, puzzles, time budget validation
"""

import time
import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.core.constructs import (
    CONSTRUCTS, ConstructID, Construct, SubFacet, BehavioralIndicator,
    SignalType, get_indicator_by_id, get_construct_summary,
)
from src.core.interaction_loop import (
    CHAMBERS, TIMING, TRANSITIONS,
    InteractionType, SessionPhase, DifficultyLevel, TransitionEvent,
    InteractionConfig, ChamberConfig, SessionState, TimingModel,
    apply_transition, get_chamber, get_interaction, get_session_flow,
)
from src.core.scoring_model import (
    normalize_min_max, apply_polarity, scale_to_1_10,
    score_indicator, score_sub_facet, score_construct, score_full_assessment,
    AssessmentResult, ConstructScore, SubFacetScore, IndicatorScore,
)
from src.core.narrative import (
    CHAMBER_NARRATIVES, PROLOGUE, EPILOGUE,
    ChamberNarrative, NarrativeBeat, PuzzleComponent,
    validate_all_timings, validate_chamber_timing,
)


# ═══════════════════════════════════════════════════════════════════
# TASK 1.1 — Constructs, Sub-Facets, Behavioral Indicators
# ═══════════════════════════════════════════════════════════════════

class TestTask11ConstructRegistry:

    def test_exactly_four_constructs_exist(self):
        assert len(CONSTRUCTS) == 4

    def test_construct_ids_match_enum(self):
        expected = {"confidence", "curiosity", "emotional_safety", "exploratory_power"}
        actual = {c.value for c in CONSTRUCTS.keys()}
        assert actual == expected

    def test_each_construct_has_four_subfacets(self):
        for cid, construct in CONSTRUCTS.items():
            assert len(construct.sub_facets) == 4, f"{cid.value} has {len(construct.sub_facets)} sub-facets"

    def test_each_subfacet_has_at_least_two_indicators(self):
        for cid, construct in CONSTRUCTS.items():
            for sf in construct.sub_facets:
                assert len(sf.indicators) >= 2, f"{sf.id} has {len(sf.indicators)} indicators"

    def test_total_indicator_count_at_least_32(self):
        total = sum(c.indicator_count for c in CONSTRUCTS.values())
        assert total >= 32, f"Only {total} indicators (expected >=32)"

    def test_all_indicator_ids_unique(self):
        ids = []
        for c in CONSTRUCTS.values():
            for sf in c.sub_facets:
                for ind in sf.indicators:
                    ids.append(ind.id)
        assert len(ids) == len(set(ids)), "Duplicate indicator IDs found"

    def test_indicator_weight_range(self):
        for c in CONSTRUCTS.values():
            for sf in c.sub_facets:
                for ind in sf.indicators:
                    assert 0.0 < ind.weight <= 1.0, f"{ind.id} weight {ind.weight} out of range"

    def test_indicator_polarity_valid(self):
        for c in CONSTRUCTS.values():
            for sf in c.sub_facets:
                for ind in sf.indicators:
                    assert ind.polarity in (1.0, -1.0), f"{ind.id} polarity {ind.polarity}"

    def test_indicator_min_less_than_max(self):
        for c in CONSTRUCTS.values():
            for sf in c.sub_facets:
                for ind in sf.indicators:
                    assert ind.min_value < ind.max_value, f"{ind.id} min >= max"

    def test_signal_types_are_valid_enum(self):
        for c in CONSTRUCTS.values():
            for sf in c.sub_facets:
                for ind in sf.indicators:
                    assert isinstance(ind.signal_type, SignalType)

    def test_get_indicator_by_id_found(self):
        first_ind = CONSTRUCTS[ConstructID.CONFIDENCE].sub_facets[0].indicators[0]
        result = get_indicator_by_id(first_ind.id)
        assert result is not None
        assert result.id == first_ind.id

    def test_get_indicator_by_id_not_found(self):
        result = get_indicator_by_id("nonexistent_indicator_xyz")
        assert result is None

    def test_get_construct_summary_returns_all(self):
        summary = get_construct_summary()
        assert len(summary) == 4

    def test_subfacet_weights_sum_to_one(self):
        for cid, construct in CONSTRUCTS.items():
            total = sum(sf.weight for sf in construct.sub_facets)
            assert abs(total - 1.0) < 0.01, f"{cid.value} sub-facet weights sum to {total}"

    def test_construct_dataclass_is_frozen(self):
        c = CONSTRUCTS[ConstructID.CONFIDENCE]
        try:
            c.name = "modified"
            assert False, "Should not allow mutation"
        except Exception:
            pass


class TestTask11Performance:

    def test_registry_lookup_speed(self):
        start = time.perf_counter()
        for _ in range(10000):
            _ = CONSTRUCTS[ConstructID.CONFIDENCE]
        elapsed = time.perf_counter() - start
        assert elapsed < 0.1, f"10k lookups: {elapsed:.4f}s"

    def test_indicator_search_speed(self):
        first_ind = CONSTRUCTS[ConstructID.CONFIDENCE].sub_facets[0].indicators[0]
        start = time.perf_counter()
        for _ in range(1000):
            get_indicator_by_id(first_ind.id)
        elapsed = time.perf_counter() - start
        assert elapsed < 0.5, f"1k searches: {elapsed:.4f}s"

    def test_summary_generation_speed(self):
        start = time.perf_counter()
        for _ in range(1000):
            get_construct_summary()
        elapsed = time.perf_counter() - start
        assert elapsed < 1.0, f"1k summaries: {elapsed:.4f}s"


# ═══════════════════════════════════════════════════════════════════
# TASK 1.2 — Interaction Loop, FSM, Timing Model
# ═══════════════════════════════════════════════════════════════════

class TestTask12InteractionLoop:

    def test_four_chambers_defined(self):
        assert len(CHAMBERS) == 4

    def test_each_chamber_has_interactions(self):
        for cid, chamber in CHAMBERS.items():
            assert len(chamber.interactions) >= 2, f"{cid} has < 2 interactions"

    def test_timing_model_total_under_300s(self):
        assert TIMING.total_session_ms <= 300_000

    def test_session_state_initial_phase(self):
        state = SessionState(session_id="test-1")
        assert state.phase == SessionPhase.CONSENT

    def test_fsm_consent_transition(self):
        state = SessionState(session_id="test-2")
        new_phase = apply_transition(state, TransitionEvent.CONSENT_GIVEN)
        # Accepts either mode_select or onboarding depending on FSM design
        assert new_phase in (SessionPhase.MODE_SELECT, SessionPhase.ONBOARDING)

    def test_fsm_invalid_transition_raises(self):
        state = SessionState(session_id="test-3")
        try:
            apply_transition(state, TransitionEvent.CHAMBER_COMPLETE)
            assert False, "Should raise ValueError"
        except ValueError:
            pass

    def test_interaction_types_valid(self):
        for chamber in CHAMBERS.values():
            for interaction in chamber.interactions:
                assert isinstance(interaction.interaction_type, InteractionType)

    def test_get_chamber_returns_config(self):
        result = get_chamber("confidence")
        assert result is not None
        assert result.construct_id == "confidence"

    def test_get_chamber_invalid_raises(self):
        try:
            get_chamber("nonexistent")
            assert False, "Should raise ValueError"
        except (ValueError, KeyError):
            pass

    def test_session_flow_returns_list(self):
        flow = get_session_flow()
        assert isinstance(flow, list)
        assert len(flow) > 0

    def test_transitions_dict_populated(self):
        assert len(TRANSITIONS) > 0

    def test_timing_total_is_5_minutes(self):
        assert TIMING.total_session_ms == 300_000


class TestTask12Performance:

    def test_fsm_transition_speed(self):
        start = time.perf_counter()
        for _ in range(10000):
            state = SessionState(session_id="perf")
            apply_transition(state, TransitionEvent.CONSENT_GIVEN)
        elapsed = time.perf_counter() - start
        assert elapsed < 0.5, f"10k transitions: {elapsed:.4f}s"


# ═══════════════════════════════════════════════════════════════════
# TASK 1.3 — Scoring Model
# ═══════════════════════════════════════════════════════════════════

class TestTask13ScoringModel:

    def test_normalize_min_max_basic(self):
        assert normalize_min_max(50, 0, 100) == 0.5
        assert normalize_min_max(0, 0, 100) == 0.0
        assert normalize_min_max(100, 0, 100) == 1.0

    def test_normalize_clamping(self):
        assert normalize_min_max(150, 0, 100) == 1.0
        assert normalize_min_max(-50, 0, 100) == 0.0

    def test_normalize_equal_min_max(self):
        assert normalize_min_max(5, 5, 5) == 0.5

    def test_polarity_positive(self):
        assert apply_polarity(0.8, 1.0) == 0.8

    def test_polarity_negative(self):
        result = apply_polarity(0.8, -1.0)
        assert abs(result - 0.2) < 1e-10  # Float tolerance

    def test_scale_1_10_boundaries(self):
        assert scale_to_1_10(0.0) == 1.0
        assert scale_to_1_10(1.0) == 10.0
        assert scale_to_1_10(0.5) == 5.5

    def test_score_indicator_basic(self):
        ind = CONSTRUCTS[ConstructID.CONFIDENCE].sub_facets[0].indicators[0]
        result = score_indicator(ind, (ind.min_value + ind.max_value) / 2)
        assert isinstance(result, IndicatorScore)
        assert 0.0 <= result.normalized_value <= 1.0

    def test_score_subfacet_with_signals(self):
        construct = CONSTRUCTS[ConstructID.CONFIDENCE]
        sf = construct.sub_facets[0]
        signals = {ind.id: (ind.min_value + ind.max_value) / 2 for ind in sf.indicators}
        result = score_sub_facet(sf, signals)
        assert isinstance(result, SubFacetScore)
        assert 0.0 <= result.raw_score <= 1.0

    def test_score_subfacet_no_signals(self):
        construct = CONSTRUCTS[ConstructID.CONFIDENCE]
        sf = construct.sub_facets[0]
        result = score_sub_facet(sf, {})
        assert result.raw_score == 0.5

    def test_score_construct_full(self):
        construct = CONSTRUCTS[ConstructID.CONFIDENCE]
        signals = {}
        for sf in construct.sub_facets:
            for ind in sf.indicators:
                signals[ind.id] = (ind.min_value + ind.max_value) / 2
        result = score_construct(construct, signals)
        assert isinstance(result, ConstructScore)
        assert 1.0 <= result.scaled_score <= 10.0
        assert result.confidence_lower <= result.scaled_score <= result.confidence_upper
        assert result.evidence_count >= 8  # At least 8 indicators

    def test_score_full_assessment(self):
        signals = {}
        for c in CONSTRUCTS.values():
            for sf in c.sub_facets:
                for ind in sf.indicators:
                    signals[ind.id] = (ind.min_value + ind.max_value) / 2
        result = score_full_assessment("test-session", signals)
        assert isinstance(result, AssessmentResult)
        assert len(result.construct_scores) == 4
        assert result.completion_pct == 100.0
        assert result.total_signals >= 32

    def test_full_assessment_partial_signals(self):
        construct = CONSTRUCTS[ConstructID.CURIOSITY]
        signals = {construct.sub_facets[0].indicators[0].id: 5000.0}
        result = score_full_assessment("partial", signals)
        assert result.total_signals == 1
        assert result.completion_pct < 100.0

    def test_score_high_values_produce_high_scores(self):
        construct = CONSTRUCTS[ConstructID.CONFIDENCE]
        signals = {}
        for sf in construct.sub_facets:
            for ind in sf.indicators:
                signals[ind.id] = ind.max_value if ind.polarity > 0 else ind.min_value
        result = score_construct(construct, signals)
        assert result.scaled_score >= 7.0

    def test_score_low_values_produce_low_scores(self):
        construct = CONSTRUCTS[ConstructID.CONFIDENCE]
        signals = {}
        for sf in construct.sub_facets:
            for ind in sf.indicators:
                signals[ind.id] = ind.min_value if ind.polarity > 0 else ind.max_value
        result = score_construct(construct, signals)
        assert result.scaled_score <= 4.0


class TestTask13Performance:

    def test_full_scoring_speed(self):
        signals = {}
        for c in CONSTRUCTS.values():
            for sf in c.sub_facets:
                for ind in sf.indicators:
                    signals[ind.id] = (ind.min_value + ind.max_value) / 2
        start = time.perf_counter()
        for _ in range(100):
            score_full_assessment("perf", signals)
        elapsed = time.perf_counter() - start
        per_call = elapsed / 100 * 1000
        assert per_call < 50, f"Scoring: {per_call:.1f}ms/call"

    def test_normalization_speed(self):
        start = time.perf_counter()
        for _ in range(100000):
            normalize_min_max(5000, 0, 10000)
        elapsed = time.perf_counter() - start
        assert elapsed < 0.5, f"100k normalizations: {elapsed:.4f}s"


# ═══════════════════════════════════════════════════════════════════
# TASK 1.4 — Narrative and Puzzles
# ═══════════════════════════════════════════════════════════════════

class TestTask14Narrative:

    def test_four_chamber_narratives_exist(self):
        assert len(CHAMBER_NARRATIVES) == 4

    def test_chamber_narrative_ids_match(self):
        expected = {"confidence", "curiosity", "emotional_safety", "exploratory_power"}
        assert set(CHAMBER_NARRATIVES.keys()) == expected

    def test_prologue_has_beats(self):
        assert len(PROLOGUE) >= 3

    def test_epilogue_has_beats(self):
        assert len(EPILOGUE) >= 1

    def test_each_chamber_has_entry_beats(self):
        for cid, narr in CHAMBER_NARRATIVES.items():
            assert len(narr.entry_beats) >= 1, f"{cid} missing entry beats"

    def test_each_chamber_has_exit_beats(self):
        for cid, narr in CHAMBER_NARRATIVES.items():
            assert len(narr.exit_beats) >= 1, f"{cid} missing exit beats"

    def test_narrative_beat_has_text(self):
        for beat in PROLOGUE:
            assert len(beat.text) > 10

    def test_narrative_beat_duration_positive(self):
        for beat in PROLOGUE:
            assert beat.duration_ms > 0

    def test_puzzle_has_solution(self):
        for narr in CHAMBER_NARRATIVES.values():
            for puzzle in narr.puzzles:
                assert len(puzzle.solution) > 0

    def test_puzzle_difficulty_range(self):
        for narr in CHAMBER_NARRATIVES.values():
            for puzzle in narr.puzzles:
                assert 0.0 <= puzzle.difficulty <= 1.0

    def test_all_timings_within_budget(self):
        reports = validate_all_timings()
        for report in reports:
            assert report.is_within_budget, f"{report.chamber_id} over budget"

    def test_total_narrative_under_5_minutes(self):
        total_ms = sum(b.duration_ms for b in PROLOGUE)
        total_ms += sum(b.duration_ms for b in EPILOGUE)
        for narr in CHAMBER_NARRATIVES.values():
            total_ms += sum(b.duration_ms for b in narr.entry_beats)
            total_ms += sum(b.duration_ms for b in narr.interaction_transitions)
            total_ms += sum(b.duration_ms for b in narr.exit_beats)
            total_ms += sum(p.time_limit_ms for p in narr.puzzles)
        assert total_ms <= 300_000


class TestTask14Performance:

    def test_timing_validation_speed(self):
        start = time.perf_counter()
        for _ in range(1000):
            validate_all_timings()
        elapsed = time.perf_counter() - start
        assert elapsed < 0.5, f"1k validations: {elapsed:.4f}s"
