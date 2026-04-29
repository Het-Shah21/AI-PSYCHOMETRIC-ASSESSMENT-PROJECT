"""
FastAPI routers for session management, signals, scoring, and external API.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from ..core.interaction_loop import get_session_flow
from ..core.constructs import get_construct_summary
from ..engine.state_machine import SessionEngine
from ..services.llm_service import get_llm_gateway, PromptContext
from ..services.scoring_engine import BayesianScoringEngine
from ..services.explainability import generate_full_report
from ..services.event_pipeline import EventPipeline, RawEvent


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class CreateSessionRequest(BaseModel):
    mode: str = Field(..., pattern="^(self-awareness|hiring|educational|therapeutic)$")

class CreateSessionResponse(BaseModel):
    session_id: str
    chamber_order: list[str]
    session_flow: list[dict]

class ConsentRequest(BaseModel):
    session_id: str
    data_collection: bool
    webcam: bool = False
    analytics: bool = False

class SignalPayload(BaseModel):
    session_id: str
    chamber_id: str
    interaction_id: str
    events: list[dict[str, Any]]

class CompanionChatRequest(BaseModel):
    session_id: str
    chamber_id: str
    message: str
    history: list[dict[str, str]] = []

class ScoreRequest(BaseModel):
    session_id: str
    signals: dict[str, float]

class TransitionRequest(BaseModel):
    session_id: str
    event: str
    data: dict[str, Any] = {}


# ---------------------------------------------------------------------------
# In-Memory Session Store (replaced by DB in production)
# ---------------------------------------------------------------------------

_sessions: dict[str, SessionEngine] = {}
_pipelines: dict[str, EventPipeline] = {}
_session_counter: int = 0


def get_engine(session_id: str) -> SessionEngine:
    if session_id not in _sessions:
        raise HTTPException(404, "Session not found")
    return _sessions[session_id]


# ---------------------------------------------------------------------------
# Session Router
# ---------------------------------------------------------------------------

session_router = APIRouter(prefix="/sessions", tags=["sessions"])


@session_router.post("", response_model=CreateSessionResponse)
async def create_session(req: CreateSessionRequest):
    global _session_counter
    session_id = str(uuid.uuid4())
    _session_counter += 1
    engine = SessionEngine(session_id, session_index=_session_counter)
    engine.state.mode = req.mode
    _sessions[session_id] = engine
    _pipelines[session_id] = EventPipeline()

    return CreateSessionResponse(
        session_id=session_id,
        chamber_order=engine.state.chamber_order,
        session_flow=get_session_flow(),
    )


@session_router.post("/consent")
async def record_consent(req: ConsentRequest):
    engine = get_engine(req.session_id)
    engine.state.is_consent_given = req.data_collection
    return {"status": "consent_recorded"}


@session_router.post("/transition")
async def transition(req: TransitionRequest):
    from ..core.interaction_loop import TransitionEvent
    engine = get_engine(req.session_id)
    try:
        event = TransitionEvent(req.event)
    except ValueError:
        raise HTTPException(400, f"Invalid event: {req.event}")
    result = await engine.handle_event(event, req.data)
    return result


@session_router.get("/{session_id}/state")
async def get_state(session_id: str):
    engine = get_engine(session_id)
    return engine.get_state_snapshot()


# ---------------------------------------------------------------------------
# Signals Router
# ---------------------------------------------------------------------------

signals_router = APIRouter(prefix="/signals", tags=["signals"])


@signals_router.post("")
async def record_signals(req: SignalPayload):
    engine = get_engine(req.session_id)
    pipeline = _pipelines.get(req.session_id)
    if not pipeline:
        raise HTTPException(404, "Pipeline not found")

    events = [
        RawEvent(
            event_type=e.get("event_type", "unknown"),
            timestamp_ms=e.get("timestamp_ms", 0),
            chamber_id=req.chamber_id,
            interaction_id=req.interaction_id,
            payload=e.get("payload", {}),
        )
        for e in req.events
    ]
    pipeline.ingest_batch(events)
    features = pipeline.extract_features(req.chamber_id, req.interaction_id)

    # Record in engine
    for signal_id, value in features.items():
        engine.record_signal(req.chamber_id, signal_id, value)

    return {"features_extracted": len(features), "features": features}


# ---------------------------------------------------------------------------
# Companion Chat Router
# ---------------------------------------------------------------------------

companion_router = APIRouter(prefix="/companion", tags=["companion"])


@companion_router.post("/chat")
async def companion_chat(req: CompanionChatRequest):
    get_engine(req.session_id)  # Validate session exists
    gateway = get_llm_gateway()
    context = PromptContext(
        chamber_id=req.chamber_id,
        user_message=req.message,
        conversation_history=req.history,
    )
    response = await gateway.generate_companion_response(context)
    return {"response": response, "chamber_id": req.chamber_id}


# ---------------------------------------------------------------------------
# Scoring Router
# ---------------------------------------------------------------------------

scoring_router = APIRouter(prefix="/scoring", tags=["scoring"])


@scoring_router.post("/compute")
async def compute_scores(req: ScoreRequest):
    engine = get_engine(req.session_id)
    scoring = BayesianScoringEngine()

    # Merge pipeline signals with explicitly provided signals
    all_signals = engine.get_all_signals()
    all_signals.update(req.signals)

    result = scoring.score_full_assessment(req.session_id, all_signals)
    explanations = generate_full_report(result.construct_scores)

    # Check mode-based visibility
    mode = engine.state.mode
    scores_visible = mode in ("self-awareness", "educational")

    response: dict[str, Any] = {
        "session_id": req.session_id,
        "mode": mode,
        "scores_visible": scores_visible,
        "completion_pct": result.completion_pct,
        "total_signals": result.total_signals,
    }

    if scores_visible:
        response["scores"] = {
            cid: {
                "scaled_score": cs.scaled_score,
                "confidence_interval": [cs.confidence_lower, cs.confidence_upper],
                "evidence_count": cs.evidence_count,
                "sub_facets": [
                    {"id": sf.sub_facet_id, "name": sf.sub_facet_name, "score": round(sf.raw_score * 10, 1)}
                    for sf in cs.sub_facet_scores
                ],
            }
            for cid, cs in result.construct_scores.items()
        }
        response["explanations"] = {
            cid: {
                "narrative": exp.overall_narrative,
                "strengths": exp.strengths,
                "growth_areas": exp.growth_areas,
                "confidence_description": exp.confidence_description,
            }
            for cid, exp in explanations.items()
        }
    else:
        response["message"] = "Scores recorded. Visible to administrator only."

    return response


# ---------------------------------------------------------------------------
# External API Router (Task 5.3)
# ---------------------------------------------------------------------------

external_router = APIRouter(prefix="/external", tags=["external"])


@external_router.get("/constructs")
async def list_constructs():
    return get_construct_summary()


@external_router.get("/health")
async def health():
    gateway = get_llm_gateway()
    return {
        "status": "healthy",
        "llm_available": gateway.is_available,
        "active_sessions": len(_sessions),
    }
