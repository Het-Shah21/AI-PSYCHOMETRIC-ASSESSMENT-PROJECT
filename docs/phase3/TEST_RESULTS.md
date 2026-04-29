# Phase 3 — Test Results Report

**Run date:** 2026-04-29 | **Status:** ✅ 30/30 Passed | **Duration:** 0.32s

---

## Summary

| Task | Unit Tests | Performance Tests | Pass Rate |
|------|-----------|------------------|-----------|
| 3.1 State Machine & Event Bus | 13 | 1 | 14/14 ✅ |
| 3.2 Database Models | 6 | 0 | 6/6 ✅ |
| 3.3 Event Pipeline | 9 | 1 | 10/10 ✅ |
| **Total** | **28** | **2** | **30/30 ✅** |

---

## Task 3.1 — State Machine, Event Bus, Latin Square, Branching

### Event Bus Tests

| # | Test | Result | Reason |
|---|------|--------|--------|
| 1 | `test_subscribe_and_publish` | ✅ | Async pub/sub correctly delivers data to subscriber |
| 2 | `test_multiple_subscribers` | ✅ | Both subscribers receive the same event (fan-out) |
| 3 | `test_unrelated_event_not_received` | ✅ | Subscribers only get events they registered for |

### Latin Square Counterbalancing Tests

| # | Test | Result | Reason |
|---|------|--------|--------|
| 4 | `test_order_returns_4_chambers` | ✅ | Always 4 chambers in the order |
| 5 | `test_order_contains_all_chambers` | ✅ | All 4 construct IDs present (no duplicates, no omissions) |
| 6 | `test_different_sessions_different_orders` | ✅ | Sessions 0-3 produce 4 unique orderings — eliminates first-order carryover effects |
| 7 | `test_order_cycles_after_4` | ✅ | Session 4 = Session 0 order — deterministic cycling via modulo |

### Narrative Controller Tests

| # | Test | Result | Reason |
|---|------|--------|--------|
| 8 | `test_evaluate_fast_responder` | ✅ | avg_latency < 3000ms → FAST_RESPONDER branch condition |
| 9 | `test_evaluate_slow_deliberate` | ✅ | avg_latency > 8000ms → SLOW_DELIBERATE branch condition |
| 10 | `test_evaluate_high_curiosity` | ✅ | exploration_pct > 0.7 → HIGH_CURIOSITY branch condition |
| 11 | `test_evaluate_no_conditions` | ✅ | Normal latency (5000ms) triggers no branch conditions |

### Session Engine Tests

| # | Test | Result | Reason |
|---|------|--------|--------|
| 12 | `test_create_session` | ✅ | Snapshot contains session_id, phase=consent, 4 chamber_order |
| 13 | `test_handle_consent_event` | ✅ | FSM transitions on CONSENT_GIVEN event |

### Performance

| # | Test | Metric | Result | Reason |
|---|------|--------|--------|--------|
| 14 | `test_latin_square_speed` | 10k order generations | **< 10ms** | Modular arithmetic; called once per session creation |

---

## Task 3.2 — Database Models (Schema Validation)

| # | Test | Result | Reason |
|---|------|--------|--------|
| 1 | `test_session_model_columns` | ✅ | Required columns: id, anonymous_id, mode, chamber_order, status, consent_given |
| 2 | `test_signal_model_columns` | ✅ | Required columns: id, session_id, chamber_id, signal_type, signal_id, value |
| 3 | `test_score_model_columns` | ✅ | Required columns: id, session_id, construct_id, scaled_score |
| 4 | `test_consent_model_columns` | ✅ | Required columns: id, session_id, data_collection_consent |
| 5 | `test_signal_foreign_key` | ✅ | FK → sessions.id ensures referential integrity + cascade delete |
| 6 | `test_score_foreign_key` | ✅ | FK → sessions.id ensures scores linked to sessions |

**Note:** No live DB tests — schema-only validation against SQLAlchemy models. Live DB tests require Alembic migrations + test database setup (deferred to pilot phase).

---

## Task 3.3 — Event Pipeline & Feature Extraction

### Pipeline Tests

| # | Test | Result | Reason |
|---|------|--------|--------|
| 1 | `test_ingest_single_event` | ✅ | Single event buffered correctly |
| 2 | `test_ingest_batch` | ✅ | 10 events ingested in batch mode |
| 3 | `test_pipeline_extract_features` | ✅ | End-to-end: ingest → extract → features dict |
| 4 | `test_clear_buffer` | ✅ | Buffer cleared after extraction |

### Feature Extractor Tests

| # | Test | Result | Reason |
|---|------|--------|--------|
| 5 | `test_feature_extractor_latency` | ✅ | stimulus_shown → choice_made = 3500ms latency |
| 6 | `test_feature_extractor_text` | ✅ | "This is a test response with several words" → word_count = 8 |
| 7 | `test_feature_extractor_exploration` | ✅ | 4 area_explore events → coverage ≥ 0 |
| 8 | `test_feature_extractor_revision` | ✅ | 2 choice_changed events → revision_count = 2 |
| 9 | `test_feature_extractor_help` | ✅ | 2 help_request events → help_seek_count = 2 |

### Performance

| # | Test | Metric | Result | Reason |
|---|------|--------|--------|--------|
| 10 | `test_feature_extraction_speed` | 1k latency extractions (100 events each) | **< 100ms** | Feature extraction must be faster than user interaction speed (~1s) |
