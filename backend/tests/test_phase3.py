"""Phase 3 Tests — actual API signatures from inspection."""

import time
import asyncio
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.engine.state_machine import (
    EventBus, NarrativeController, SessionEngine, BranchCondition,
    get_counterbalanced_order,
)
from src.core.interaction_loop import SessionPhase, TransitionEvent
from src.models.database import (
    Session as SessionModel, BehavioralSignal as BehavioralSignalModel,
    Score as ScoreModel, ConsentRecord,
)
from src.services.event_pipeline import EventPipeline, FeatureExtractor, RawEvent


def _raw(event_type, ts, chamber="confidence", interaction="conf-1", payload=None):
    return RawEvent(event_type=event_type, timestamp_ms=ts, chamber_id=chamber,
                    interaction_id=interaction, payload=payload or {})


# ═══ TASK 3.1 ═══

class TestTask31EventBus:
    def test_subscribe_and_publish(self):
        bus = EventBus()
        received = []
        bus.subscribe("test_event", lambda data: received.append(data))
        asyncio.get_event_loop().run_until_complete(bus.publish("test_event", {"key": "value"}))
        assert len(received) == 1

    def test_multiple_subscribers(self):
        bus = EventBus()
        r1, r2 = [], []
        bus.subscribe("evt", lambda d: r1.append(d))
        bus.subscribe("evt", lambda d: r2.append(d))
        asyncio.get_event_loop().run_until_complete(bus.publish("evt", {}))
        assert len(r1) == 1 and len(r2) == 1

    def test_unrelated_event_not_received(self):
        bus = EventBus()
        received = []
        bus.subscribe("event_a", lambda d: received.append(d))
        asyncio.get_event_loop().run_until_complete(bus.publish("event_b", {}))
        assert len(received) == 0


class TestTask31LatinSquare:
    def test_order_returns_4_chambers(self):
        assert len(get_counterbalanced_order(0)) == 4

    def test_order_contains_all_chambers(self):
        expected = {"confidence", "curiosity", "emotional_safety", "exploratory_power"}
        assert set(get_counterbalanced_order(0)) == expected

    def test_different_sessions_different_orders(self):
        orders = [tuple(get_counterbalanced_order(i)) for i in range(4)]
        assert len(set(orders)) == 4

    def test_order_cycles_after_4(self):
        assert get_counterbalanced_order(0) == get_counterbalanced_order(4)


class TestTask31NarrativeController:
    def test_evaluate_fast_responder(self):
        ctrl = NarrativeController()
        conditions = ctrl.evaluate_conditions("confidence", {"avg_latency_ms": 2000})
        assert BranchCondition.FAST_RESPONDER in conditions

    def test_evaluate_slow_deliberate(self):
        ctrl = NarrativeController()
        conditions = ctrl.evaluate_conditions("confidence", {"avg_latency_ms": 9000})
        assert BranchCondition.SLOW_DELIBERATE in conditions

    def test_evaluate_high_curiosity(self):
        ctrl = NarrativeController()
        conditions = ctrl.evaluate_conditions("curiosity", {"exploration_pct": 0.85})
        assert BranchCondition.HIGH_CURIOSITY in conditions

    def test_evaluate_no_conditions(self):
        ctrl = NarrativeController()
        conditions = ctrl.evaluate_conditions("confidence", {"avg_latency_ms": 5000})
        assert len(conditions) == 0


class TestTask31SessionEngine:
    def test_create_session(self):
        engine = SessionEngine("test-session", session_index=0)
        snap = engine.get_state_snapshot()
        assert snap["session_id"] == "test-session"
        assert len(snap["chamber_order"]) == 4

    def test_handle_consent_event(self):
        engine = SessionEngine("test-consent", session_index=0)
        asyncio.get_event_loop().run_until_complete(engine.handle_event(TransitionEvent.CONSENT_GIVEN))
        snap = engine.get_state_snapshot()
        assert snap["phase"] in ("onboarding", "mode_select")


class TestTask31Performance:
    def test_latin_square_speed(self):
        start = time.perf_counter()
        for i in range(10000):
            get_counterbalanced_order(i)
        elapsed = time.perf_counter() - start
        assert elapsed < 0.1, f"10k orders: {elapsed:.4f}s"


# ═══ TASK 3.2 ═══

class TestTask32DatabaseModels:
    def test_session_model_columns(self):
        cols = {c.name for c in SessionModel.__table__.columns}
        assert {"id", "anonymous_id", "mode", "chamber_order", "status", "consent_given"}.issubset(cols)

    def test_signal_model_columns(self):
        cols = {c.name for c in BehavioralSignalModel.__table__.columns}
        assert {"id", "session_id", "chamber_id", "signal_type", "signal_id", "value"}.issubset(cols)

    def test_score_model_columns(self):
        cols = {c.name for c in ScoreModel.__table__.columns}
        assert {"id", "session_id", "construct_id", "scaled_score"}.issubset(cols)

    def test_consent_model_columns(self):
        cols = {c.name for c in ConsentRecord.__table__.columns}
        assert {"id", "session_id", "data_collection_consent"}.issubset(cols)

    def test_signal_foreign_key(self):
        fks = [str(fk) for fk in BehavioralSignalModel.__table__.foreign_keys]
        assert any("sessions.id" in fk for fk in fks)

    def test_score_foreign_key(self):
        fks = [str(fk) for fk in ScoreModel.__table__.foreign_keys]
        assert any("sessions.id" in fk for fk in fks)


# ═══ TASK 3.3 ═══  (using single-event ingest API)

class TestTask33EventPipeline:
    def test_ingest_single_event(self):
        pipeline = EventPipeline()
        pipeline.ingest(_raw("click", 1000))
        stats = pipeline.get_buffer_stats()
        assert sum(stats.values()) >= 1

    def test_ingest_batch(self):
        pipeline = EventPipeline()
        events = [_raw("click", i * 100) for i in range(10)]
        pipeline.ingest_batch(events)
        stats = pipeline.get_buffer_stats()
        assert sum(stats.values()) >= 10

    def test_feature_extractor_latency(self):
        events = [_raw("stimulus_shown", 1000), _raw("choice_made", 4500)]
        latency = FeatureExtractor.extract_latency(events)
        assert latency == 3500

    def test_feature_extractor_text(self):
        events = [_raw("text_submit", 1000, payload={"text": "This is a test response with several words"})]
        features = FeatureExtractor.extract_text_features(events)
        assert features.get("word_count", 0) == 8

    def test_feature_extractor_exploration(self):
        events = [_raw("area_explore", i * 500, payload={"area_id": i}) for i in range(4)]
        cov = FeatureExtractor.extract_exploration_coverage(events)
        assert cov >= 0

    def test_feature_extractor_revision(self):
        events = [_raw("choice_changed", 1000), _raw("choice_changed", 2000), _raw("choice_made", 3000)]
        count = FeatureExtractor.extract_revision_count(events)
        assert count == 2

    def test_feature_extractor_help(self):
        events = [_raw("help_request", 1000), _raw("help_request", 3000)]
        count = FeatureExtractor.extract_help_seek_count(events)
        assert count == 2

    def test_pipeline_extract_features(self):
        pipeline = EventPipeline()
        pipeline.ingest_batch([_raw("interaction_start", 1000), _raw("response_submit", 4000)])
        features = pipeline.extract_features("confidence", "conf-1")
        assert isinstance(features, dict)

    def test_clear_buffer(self):
        pipeline = EventPipeline()
        pipeline.ingest(_raw("click", 0))
        pipeline.clear_buffer("confidence", "conf-1")
        features = pipeline.extract_features("confidence", "conf-1")
        assert len(features) == 0


class TestTask33Performance:
    def test_feature_extraction_speed(self):
        events = [_raw("click", i * 100) for i in range(100)]
        start = time.perf_counter()
        for _ in range(1000):
            FeatureExtractor.extract_latency(events)
        elapsed = time.perf_counter() - start
        assert elapsed < 1.0, f"1k extractions: {elapsed:.3f}s"
