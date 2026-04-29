"""
Task 3.1 — Reactive State Machine and Branching Narrative Controller

Extends the core FSM (Task 1.2) into a full reactive engine with:
  - Event-driven architecture (publish/subscribe)
  - Branching narrative paths based on behavioral signals
  - Chamber counterbalancing (Latin Square)
  - Real-time state broadcasting for frontend sync
"""

from __future__ import annotations

import asyncio
import random
import time
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Awaitable

from ..core.interaction_loop import (
    SessionState, SessionPhase, TransitionEvent,
    apply_transition, CHAMBERS, ChamberConfig,
)
from ..core.narrative import CHAMBER_NARRATIVES, PROLOGUE, EPILOGUE, NarrativeBeat

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Event Bus
# ---------------------------------------------------------------------------

EventHandler = Callable[[dict[str, Any]], Awaitable[None]]


class EventBus:
    """Simple async publish/subscribe event bus."""

    def __init__(self):
        self._handlers: dict[str, list[EventHandler]] = {}

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    async def publish(self, event_type: str, data: dict[str, Any]) -> None:
        for handler in self._handlers.get(event_type, []):
            try:
                await handler(data)
            except Exception as e:
                logger.error(f"Event handler error for {event_type}: {e}")


# ---------------------------------------------------------------------------
# Latin Square Counterbalancing
# ---------------------------------------------------------------------------

LATIN_SQUARES: list[list[str]] = [
    ["confidence", "curiosity", "emotional_safety", "exploratory_power"],
    ["curiosity", "emotional_safety", "exploratory_power", "confidence"],
    ["emotional_safety", "exploratory_power", "confidence", "curiosity"],
    ["exploratory_power", "confidence", "curiosity", "emotional_safety"],
]


def get_counterbalanced_order(session_index: int) -> list[str]:
    """Return a chamber order using Latin Square counterbalancing."""
    return LATIN_SQUARES[session_index % len(LATIN_SQUARES)]


# ---------------------------------------------------------------------------
# Branching Narrative Controller
# ---------------------------------------------------------------------------

class BranchCondition(str, Enum):
    """Conditions that determine narrative branching."""
    HIGH_CONFIDENCE = "high_confidence"
    LOW_CONFIDENCE = "low_confidence"
    HIGH_CURIOSITY = "high_curiosity"
    HIGH_VULNERABILITY = "high_vulnerability"
    FAST_RESPONDER = "fast_responder"
    SLOW_DELIBERATE = "slow_deliberate"
    HELP_SEEKER = "help_seeker"


@dataclass
class NarrativeBranch:
    """A conditional narrative branch."""
    condition: BranchCondition
    beats: tuple[NarrativeBeat, ...]
    priority: int = 0  # Higher = evaluated first


class NarrativeController:
    """Controls narrative flow with branching based on behavioral signals."""

    def __init__(self):
        self._branches: dict[str, list[NarrativeBranch]] = {}
        self._register_default_branches()

    def _register_default_branches(self) -> None:
        """Register conditional narrative branches."""
        self._branches["confidence"] = [
            NarrativeBranch(
                condition=BranchCondition.FAST_RESPONDER,
                priority=1,
                beats=(
                    NarrativeBeat(
                        id="conf_branch_fast",
                        text="The forge burns brighter — it recognizes one who decides without hesitation.",
                        speaker="narrator", duration_ms=2500,
                    ),
                ),
            ),
            NarrativeBranch(
                condition=BranchCondition.SLOW_DELIBERATE,
                priority=1,
                beats=(
                    NarrativeBeat(
                        id="conf_branch_slow",
                        text="The forge cools patiently. Deliberation has its own strength.",
                        speaker="narrator", duration_ms=2500,
                    ),
                ),
            ),
        ]
        self._branches["curiosity"] = [
            NarrativeBranch(
                condition=BranchCondition.HIGH_CURIOSITY,
                priority=1,
                beats=(
                    NarrativeBeat(
                        id="cur_branch_explorer",
                        text="The shelves rearrange in delight — a true seeker walks among them.",
                        speaker="narrator", duration_ms=2500,
                    ),
                ),
            ),
        ]
        self._branches["emotional_safety"] = [
            NarrativeBranch(
                condition=BranchCondition.HIGH_VULNERABILITY,
                priority=1,
                beats=(
                    NarrativeBeat(
                        id="es_branch_open",
                        text="The mirrors glow warmly. Your openness illuminates the garden.",
                        speaker="narrator", duration_ms=2500,
                    ),
                ),
            ),
        ]

    def evaluate_conditions(
        self, chamber_id: str, signals: dict[str, Any]
    ) -> list[BranchCondition]:
        """Evaluate which branch conditions are met based on signals."""
        conditions: list[BranchCondition] = []

        avg_latency = signals.get("avg_latency_ms", 5000)
        if avg_latency < 3000:
            conditions.append(BranchCondition.FAST_RESPONDER)
        elif avg_latency > 8000:
            conditions.append(BranchCondition.SLOW_DELIBERATE)

        exploration_pct = signals.get("exploration_pct", 0.5)
        if exploration_pct > 0.7:
            conditions.append(BranchCondition.HIGH_CURIOSITY)

        vulnerability = signals.get("vulnerability_score", 0.5)
        if vulnerability > 0.6:
            conditions.append(BranchCondition.HIGH_VULNERABILITY)

        help_count = signals.get("help_count", 0)
        if help_count >= 2:
            conditions.append(BranchCondition.HELP_SEEKER)

        return conditions

    def get_branch_beats(
        self, chamber_id: str, signals: dict[str, Any]
    ) -> list[NarrativeBeat]:
        """Get additional narrative beats based on branching conditions."""
        conditions = self.evaluate_conditions(chamber_id, signals)
        branches = self._branches.get(chamber_id, [])
        result: list[NarrativeBeat] = []

        for branch in sorted(branches, key=lambda b: -b.priority):
            if branch.condition in conditions:
                result.extend(branch.beats)

        return result


# ---------------------------------------------------------------------------
# Reactive Session Engine
# ---------------------------------------------------------------------------

class SessionEngine:
    """Main session engine coordinating state, narrative, and events."""

    def __init__(self, session_id: str, session_index: int = 0):
        self.state = SessionState(
            session_id=session_id,
            chamber_order=get_counterbalanced_order(session_index),
        )
        self.event_bus = EventBus()
        self.narrative = NarrativeController()
        self._start_time = time.time()
        self._interaction_signals: dict[str, dict[str, Any]] = {}

    @property
    def elapsed_ms(self) -> int:
        return int((time.time() - self._start_time) * 1000)

    async def handle_event(self, event: TransitionEvent, data: dict[str, Any] | None = None) -> dict[str, Any]:
        """Process a transition event and return the new state."""
        data = data or {}
        old_phase = self.state.phase

        try:
            new_phase = apply_transition(self.state, event)
        except ValueError as e:
            logger.warning(f"Invalid transition: {e}")
            return {"error": str(e), "phase": self.state.phase.value}

        self.state.elapsed_ms = self.elapsed_ms

        # Publish event
        await self.event_bus.publish(event.value, {
            "session_id": self.state.session_id,
            "old_phase": old_phase.value,
            "new_phase": new_phase.value,
            "elapsed_ms": self.state.elapsed_ms,
            **data,
        })

        result: dict[str, Any] = {
            "phase": new_phase.value,
            "chamber_index": self.state.current_chamber_index,
            "elapsed_ms": self.state.elapsed_ms,
            "progress_pct": self.state.progress_pct,
        }

        # Add narrative beats for chamber transitions
        if new_phase == SessionPhase.CHAMBER_ACTIVE:
            chamber_id = self.state.current_chamber_id
            narrative = CHAMBER_NARRATIVES.get(chamber_id)
            if narrative:
                branch_beats = self.narrative.get_branch_beats(
                    chamber_id,
                    self._get_chamber_signals(chamber_id),
                )
                result["narrative_beats"] = [
                    {"text": b.text, "speaker": b.speaker, "duration_ms": b.duration_ms}
                    for b in (*narrative.entry_beats, *branch_beats)
                ]

        return result

    def record_signal(self, chamber_id: str, signal_id: str, value: Any) -> None:
        """Record a behavioral signal for the current session."""
        if chamber_id not in self._interaction_signals:
            self._interaction_signals[chamber_id] = {}
        self._interaction_signals[chamber_id][signal_id] = value
        self.state.signals_collected.append({
            "chamber_id": chamber_id,
            "signal_id": signal_id,
            "value": value,
            "timestamp_ms": self.elapsed_ms,
        })

    def _get_chamber_signals(self, chamber_id: str) -> dict[str, Any]:
        return self._interaction_signals.get(chamber_id, {})

    def get_all_signals(self) -> dict[str, Any]:
        """Get all collected signals for scoring."""
        flat: dict[str, float] = {}
        for chamber_signals in self._interaction_signals.values():
            for sid, val in chamber_signals.items():
                if isinstance(val, (int, float)):
                    flat[sid] = float(val)
        return flat

    def get_state_snapshot(self) -> dict[str, Any]:
        """Get a serializable snapshot of current state."""
        return {
            "session_id": self.state.session_id,
            "phase": self.state.phase.value,
            "chamber_index": self.state.current_chamber_index,
            "current_chamber": self.state.current_chamber_id,
            "chamber_order": self.state.chamber_order,
            "elapsed_ms": self.elapsed_ms,
            "progress_pct": self.state.progress_pct,
            "signals_count": len(self.state.signals_collected),
            "mode": self.state.mode,
        }
