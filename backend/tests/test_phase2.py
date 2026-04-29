"""
Phase 2 Tests — AI Integration Design & Content Adaptation

Task 2.1: LLM service, prompt architecture, fallbacks
Task 2.2: Adaptive difficulty, uncertainty injection
Task 2.3: Emotion detection, valence-arousal mapping
Task 2.4: Explainability, feature attribution
"""

import time
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.services.llm_service import (
    LLMConfig, LLMGateway, PromptContext,
    build_companion_prompt, build_analysis_prompt, build_explanation_prompt,
    SYSTEM_PROMPTS,
)
from src.services.adaptive_engine import AdaptiveEngine, PerformanceState
from src.services.emotion_detector import (
    EmotionLabel, EmotionReading, EmotionAggregator,
    emotion_to_valence_arousal, EMOTION_VA_MAP,
)
from src.services.explainability import (
    extract_evidence, generate_explanation, generate_full_report,
    describe_confidence_interval, identify_strengths_and_growth,
)
from src.core.constructs import CONSTRUCTS, ConstructID
from src.core.scoring_model import score_construct


# ═══════════════════════════════════════════════════════════════════
# TASK 2.1 — LLM Service & Prompt Architecture
# ═══════════════════════════════════════════════════════════════════

class TestTask21LLMService:

    def test_system_prompts_defined(self):
        required = ["companion_base", "companion_confidence", "companion_curiosity",
                     "companion_emotional_safety", "companion_exploratory_power",
                     "text_analysis", "explanation_generation"]
        for key in required:
            assert key in SYSTEM_PROMPTS, f"Missing prompt: {key}"

    def test_prompt_max_length(self):
        for key, prompt in SYSTEM_PROMPTS.items():
            assert len(prompt) < 2000, f"{key} prompt too long: {len(prompt)} chars"

    def test_build_companion_prompt_returns_tuple(self):
        ctx = PromptContext(chamber_id="confidence", user_message="hello")
        system, user = build_companion_prompt(ctx)
        assert isinstance(system, str)
        assert isinstance(user, str)
        assert "hello" in user

    def test_build_companion_prompt_with_history(self):
        ctx = PromptContext(
            chamber_id="curiosity",
            user_message="what is this?",
            conversation_history=[
                {"role": "user", "content": "hi"},
                {"role": "assistant", "content": "welcome"},
            ],
        )
        system, user = build_companion_prompt(ctx)
        assert "hi" in user
        assert "what is this?" in user

    def test_build_analysis_prompt(self):
        system, user = build_analysis_prompt("I feel very confident about this")
        assert "JSON" in system
        assert "confident" in user

    def test_build_explanation_prompt(self):
        system, user = build_explanation_prompt("Confidence", 7.5, [{"signal": "fast"}])
        assert "Confidence" in system
        assert "7.5" in user

    def test_gateway_init_without_key(self):
        config = LLMConfig(api_key="")
        gw = LLMGateway(config)
        assert not gw.is_available

    def test_fallback_companion_returns_string(self):
        ctx = PromptContext(chamber_id="confidence", user_message="test message")
        result = LLMGateway._fallback_companion(ctx)
        assert isinstance(result, str)
        assert len(result) > 10

    def test_fallback_text_analysis_returns_dict(self):
        result = LLMGateway._fallback_text_analysis("I feel happy and confident about my choices")
        assert isinstance(result, dict)
        assert "assertiveness" in result
        assert "emotional_depth" in result
        assert all(0 <= v <= 1 for v in result.values())

    def test_fallback_text_analysis_short_text(self):
        result = LLMGateway._fallback_text_analysis("ok")
        assert all(0 <= v <= 1 for v in result.values())

    def test_fallback_explanation_returns_string(self):
        result = LLMGateway._fallback_explanation("Curiosity", 8.0)
        assert isinstance(result, str)
        assert "8.0" in result

    def test_fallback_companion_different_chambers(self):
        chambers = ["confidence", "curiosity", "emotional_safety", "exploratory_power"]
        for ch in chambers:
            ctx = PromptContext(chamber_id=ch, user_message="test")
            result = LLMGateway._fallback_companion(ctx)
            assert len(result) > 0


class TestTask21Performance:

    def test_prompt_building_speed(self):
        ctx = PromptContext(chamber_id="confidence", user_message="test")
        start = time.perf_counter()
        for _ in range(10000):
            build_companion_prompt(ctx)
        elapsed = time.perf_counter() - start
        assert elapsed < 0.5, f"10k prompt builds took {elapsed:.3f}s"

    def test_fallback_analysis_speed(self):
        text = "I feel very confident and happy about this decision that I made"
        start = time.perf_counter()
        for _ in range(1000):
            LLMGateway._fallback_text_analysis(text)
        elapsed = time.perf_counter() - start
        assert elapsed < 0.5, f"1k analyses took {elapsed:.3f}s"


# ═══════════════════════════════════════════════════════════════════
# TASK 2.2 — Adaptive Difficulty
# ═══════════════════════════════════════════════════════════════════

class TestTask22AdaptiveEngine:

    def test_initial_state(self):
        engine = AdaptiveEngine()
        state = engine.get_state("confidence")
        assert state.ability_estimate == 0.5
        assert state.responses_count == 0

    def test_difficulty_selection_range(self):
        engine = AdaptiveEngine()
        for _ in range(100):
            d = engine.select_difficulty("confidence")
            assert 0.1 <= d <= 0.95

    def test_update_correct_increases_ability(self):
        engine = AdaptiveEngine()
        engine.update_performance("confidence", True, 0.5, 2000)
        state = engine.get_state("confidence")
        assert state.ability_estimate > 0.5

    def test_update_incorrect_decreases_ability(self):
        engine = AdaptiveEngine()
        engine.update_performance("confidence", False, 0.5, 5000)
        state = engine.get_state("confidence")
        assert state.ability_estimate < 0.5

    def test_confidence_increases_with_data(self):
        engine = AdaptiveEngine()
        for _ in range(5):
            engine.update_performance("confidence", True, 0.5, 2000)
        state = engine.get_state("confidence")
        assert state.confidence > 0.5

    def test_no_uncertainty_injection_early(self):
        engine = AdaptiveEngine()
        assert not engine.should_inject_uncertainty("confidence")

    def test_uncertainty_type_valid(self):
        engine = AdaptiveEngine()
        valid_types = {"ambiguous_information", "contradictory_feedback",
                       "time_pressure_increase", "missing_context", "social_pressure"}
        for _ in range(50):
            t = engine.get_uncertainty_type()
            assert t in valid_types

    def test_record_uncertainty_reaction(self):
        engine = AdaptiveEngine()
        engine.update_performance("confidence", True, 0.5, 2000)
        engine.update_performance("confidence", True, 0.5, 2000)
        engine.record_uncertainty_reaction("confidence", 0.8)
        state = engine.get_state("confidence")
        assert len(state.uncertainty_reactions) == 1

    def test_adaptation_summary(self):
        engine = AdaptiveEngine()
        engine.update_performance("confidence", True, 0.5, 2000)
        summary = engine.get_adaptation_summary("confidence")
        assert "ability_estimate" in summary
        assert "accuracy" in summary

    def test_accuracy_tracking(self):
        engine = AdaptiveEngine()
        engine.update_performance("confidence", True, 0.5, 2000)
        engine.update_performance("confidence", False, 0.5, 3000)
        state = engine.get_state("confidence")
        assert state.accuracy == 0.5

    def test_avg_latency(self):
        engine = AdaptiveEngine()
        engine.update_performance("confidence", True, 0.5, 2000)
        engine.update_performance("confidence", True, 0.5, 4000)
        state = engine.get_state("confidence")
        assert state.avg_latency_ms == 3000.0


class TestTask22Performance:

    def test_difficulty_selection_speed(self):
        engine = AdaptiveEngine()
        start = time.perf_counter()
        for _ in range(10000):
            engine.select_difficulty("confidence")
        elapsed = time.perf_counter() - start
        assert elapsed < 0.5, f"10k selections took {elapsed:.3f}s"


# ═══════════════════════════════════════════════════════════════════
# TASK 2.3 — Emotion Detection
# ═══════════════════════════════════════════════════════════════════

class TestTask23EmotionDetector:

    def test_all_emotions_mapped(self):
        for emotion in EmotionLabel:
            v, a = emotion_to_valence_arousal(emotion)
            assert -1.0 <= v <= 1.0
            assert 0.0 <= a <= 1.0

    def test_happy_positive_valence(self):
        v, a = emotion_to_valence_arousal(EmotionLabel.HAPPY)
        assert v > 0

    def test_sad_negative_valence(self):
        v, a = emotion_to_valence_arousal(EmotionLabel.SAD)
        assert v < 0

    def test_aggregator_empty(self):
        agg = EmotionAggregator(readings=[])
        assert agg.dominant_emotion == EmotionLabel.NEUTRAL
        assert agg.avg_valence == 0.0

    def test_aggregator_single_reading(self):
        readings = [EmotionReading(timestamp_ms=0, dominant_emotion=EmotionLabel.HAPPY,
                                   confidence=0.9, valence=0.8, arousal=0.6)]
        agg = EmotionAggregator(readings=readings)
        assert agg.dominant_emotion == EmotionLabel.HAPPY
        assert agg.avg_valence == 0.8

    def test_aggregator_stability_stable(self):
        readings = [
            EmotionReading(timestamp_ms=i * 500, dominant_emotion=EmotionLabel.NEUTRAL,
                           confidence=0.9, valence=0.0, arousal=0.2)
            for i in range(10)
        ]
        agg = EmotionAggregator(readings=readings)
        assert agg.emotional_stability > 0.8

    def test_aggregator_stability_unstable(self):
        readings = [
            EmotionReading(timestamp_ms=i * 500, dominant_emotion=EmotionLabel.HAPPY,
                           confidence=0.9, valence=(-1.0) ** i, arousal=0.5)
            for i in range(10)
        ]
        agg = EmotionAggregator(readings=readings)
        assert agg.emotional_stability < 0.3

    def test_aggregator_diversity(self):
        readings = [
            EmotionReading(timestamp_ms=0, dominant_emotion=EmotionLabel.HAPPY,
                           confidence=0.9, valence=0.8, arousal=0.6),
            EmotionReading(timestamp_ms=500, dominant_emotion=EmotionLabel.SAD,
                           confidence=0.9, valence=-0.7, arousal=0.2),
            EmotionReading(timestamp_ms=1000, dominant_emotion=EmotionLabel.SURPRISED,
                           confidence=0.9, valence=0.2, arousal=0.9),
        ]
        agg = EmotionAggregator(readings=readings)
        assert agg.emotion_diversity > 0.3

    def test_behavioral_signals_output(self):
        readings = [EmotionReading(timestamp_ms=0, dominant_emotion=EmotionLabel.HAPPY,
                                   confidence=0.9, valence=0.8, arousal=0.6)]
        agg = EmotionAggregator(readings=readings)
        signals = agg.to_behavioral_signals()
        assert "emotion_stability" in signals
        assert "emotion_valence" in signals


# ═══════════════════════════════════════════════════════════════════
# TASK 2.4 — Explainability
# ═══════════════════════════════════════════════════════════════════

class TestTask24Explainability:

    def _get_scored_construct(self):
        construct = CONSTRUCTS[ConstructID.CONFIDENCE]
        signals = {}
        for sf in construct.sub_facets:
            for ind in sf.indicators:
                signals[ind.id] = (ind.min_value + ind.max_value) * 0.7
        return score_construct(construct, signals)

    def test_extract_evidence_returns_list(self):
        cs = self._get_scored_construct()
        evidence = extract_evidence(cs)
        assert isinstance(evidence, list)
        assert len(evidence) > 0

    def test_evidence_sorted_by_contribution(self):
        cs = self._get_scored_construct()
        evidence = extract_evidence(cs)
        for i in range(len(evidence) - 1):
            assert abs(evidence[i].contribution) >= abs(evidence[i + 1].contribution)

    def test_generate_explanation_structure(self):
        cs = self._get_scored_construct()
        exp = generate_explanation(cs)
        assert exp.construct_id == "confidence"
        assert 1.0 <= exp.scaled_score <= 10.0
        assert len(exp.overall_narrative) > 0

    def test_confidence_interval_description(self):
        desc = describe_confidence_interval(7.0, 5.5, 8.5)
        assert "7.0" in desc or "7" in desc
        assert "5.5" in desc
        assert "8.5" in desc

    def test_strengths_and_growth_identification(self):
        cs = self._get_scored_construct()
        strengths, growth = identify_strengths_and_growth(
            cs.sub_facet_scores, "Confidence"
        )
        assert isinstance(strengths, list)
        assert isinstance(growth, list)

    def test_full_report_all_constructs(self):
        signals = {}
        for c in CONSTRUCTS.values():
            for sf in c.sub_facets:
                for ind in sf.indicators:
                    signals[ind.id] = (ind.min_value + ind.max_value) / 2
        from src.core.scoring_model import score_full_assessment
        result = score_full_assessment("test", signals)
        report = generate_full_report(result.construct_scores)
        assert len(report) == 4


class TestTask24Performance:

    def test_explanation_generation_speed(self):
        construct = CONSTRUCTS[ConstructID.CONFIDENCE]
        signals = {ind.id: (ind.min_value + ind.max_value) / 2
                   for sf in construct.sub_facets for ind in sf.indicators}
        cs = score_construct(construct, signals)
        start = time.perf_counter()
        for _ in range(500):
            generate_explanation(cs)
        elapsed = time.perf_counter() - start
        assert elapsed < 1.0, f"500 explanations took {elapsed:.3f}s"
