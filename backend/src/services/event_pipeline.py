"""
Task 3.3 — Behavioral Event Capture and Feature Extraction Pipeline

Captures raw user interaction events, buffers them, extracts
behavioral features, and maps them to scoring model indicators.

Pipeline: RawEvent → Buffer → Extract → Normalize → Signal
"""

from __future__ import annotations

import time
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from ..core.constructs import SignalType, get_indicator_by_id

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Raw Event Schema
# ---------------------------------------------------------------------------

@dataclass
class RawEvent:
    """A single raw interaction event from the frontend."""
    event_type: str           # click, keypress, scroll, choice, text_submit, etc.
    timestamp_ms: int
    chamber_id: str
    interaction_id: str
    payload: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Feature Extractors
# ---------------------------------------------------------------------------

class FeatureExtractor:
    """Extracts behavioral features from buffered raw events."""

    @staticmethod
    def extract_latency(events: list[RawEvent]) -> float | None:
        """Extract response latency from first stimulus to first response."""
        stimulus = next((e for e in events if e.event_type == "stimulus_shown"), None)
        response = next((e for e in events if e.event_type in ("choice_made", "text_submit")), None)
        if stimulus and response:
            return float(response.timestamp_ms - stimulus.timestamp_ms)
        return None

    @staticmethod
    def extract_revision_count(events: list[RawEvent]) -> float:
        """Count how many times the user changed their answer."""
        return float(sum(1 for e in events if e.event_type == "choice_changed"))

    @staticmethod
    def extract_dwell_time(events: list[RawEvent], target: str = "") -> float | None:
        """Extract total dwell time on a specific element or area."""
        enters = [e for e in events if e.event_type == "area_enter" and (not target or e.payload.get("area") == target)]
        exits = [e for e in events if e.event_type == "area_exit" and (not target or e.payload.get("area") == target)]
        if not enters:
            return None
        total = 0.0
        for enter in enters:
            exit_event = next(
                (ex for ex in exits if ex.timestamp_ms > enter.timestamp_ms),
                None,
            )
            if exit_event:
                total += exit_event.timestamp_ms - enter.timestamp_ms
        return total

    @staticmethod
    def extract_exploration_coverage(events: list[RawEvent]) -> float:
        """Calculate percentage of available areas explored."""
        explored = set()
        total_areas = 0
        for e in events:
            if e.event_type == "area_enter":
                explored.add(e.payload.get("area", ""))
            if e.event_type == "stimulus_shown":
                total_areas = e.payload.get("total_areas", total_areas)
        if total_areas <= 0:
            return 0.5
        return len(explored) / total_areas

    @staticmethod
    def extract_text_features(events: list[RawEvent]) -> dict[str, float]:
        """Extract features from text submission events."""
        text_events = [e for e in events if e.event_type == "text_submit"]
        if not text_events:
            return {}
        text = text_events[-1].payload.get("text", "")
        return {
            "text_length": float(len(text)),
            "word_count": float(len(text.split())),
        }

    @staticmethod
    def extract_click_pattern(events: list[RawEvent]) -> float:
        """Analyze click pattern for hesitation vs. rapid-fire clicking.
        Returns [0,1] where 0 = very hesitant, 1 = rapid/confident.
        """
        clicks = [e for e in events if e.event_type in ("click", "choice_made")]
        if len(clicks) < 2:
            return 0.5
        intervals = [
            clicks[i + 1].timestamp_ms - clicks[i].timestamp_ms
            for i in range(len(clicks) - 1)
        ]
        avg_interval = sum(intervals) / len(intervals)
        # Normalize: < 500ms = rapid (1.0), > 5000ms = hesitant (0.0)
        return max(0.0, min(1.0, 1.0 - (avg_interval - 500) / 4500))

    @staticmethod
    def extract_scroll_depth(events: list[RawEvent]) -> float:
        """Extract maximum scroll depth [0, 1]."""
        scroll_events = [e for e in events if e.event_type == "scroll"]
        if not scroll_events:
            return 0.0
        return max(e.payload.get("depth", 0.0) for e in scroll_events)

    @staticmethod
    def extract_help_seek_count(events: list[RawEvent]) -> float:
        """Count help requests."""
        return float(sum(1 for e in events if e.event_type == "help_request"))


# ---------------------------------------------------------------------------
# Event Pipeline
# ---------------------------------------------------------------------------

class EventPipeline:
    """Manages the full event capture → feature extraction → signal mapping pipeline."""

    def __init__(self):
        self._buffers: dict[str, list[RawEvent]] = defaultdict(list)
        self._extractor = FeatureExtractor()
        self._extracted_signals: dict[str, float] = {}

    def ingest(self, event: RawEvent) -> None:
        """Ingest a raw event into the buffer."""
        key = f"{event.chamber_id}:{event.interaction_id}"
        self._buffers[key].append(event)

    def ingest_batch(self, events: list[RawEvent]) -> None:
        """Ingest multiple events."""
        for event in events:
            self.ingest(event)

    def extract_features(self, chamber_id: str, interaction_id: str) -> dict[str, float]:
        """Extract all features for an interaction and map to indicator IDs."""
        key = f"{chamber_id}:{interaction_id}"
        events = self._buffers.get(key, [])
        if not events:
            return {}

        signals: dict[str, float] = {}

        # Extract all possible features
        latency = self._extractor.extract_latency(events)
        if latency is not None:
            signals["response_latency"] = latency

        revision_count = self._extractor.extract_revision_count(events)
        signals["revision_count"] = revision_count

        dwell = self._extractor.extract_dwell_time(events)
        if dwell is not None:
            signals["dwell_time"] = dwell

        coverage = self._extractor.extract_exploration_coverage(events)
        signals["exploration_coverage"] = coverage

        text_features = self._extractor.extract_text_features(events)
        signals.update(text_features)

        click_pattern = self._extractor.extract_click_pattern(events)
        signals["click_pattern"] = click_pattern

        scroll = self._extractor.extract_scroll_depth(events)
        signals["scroll_depth"] = scroll

        help_count = self._extractor.extract_help_seek_count(events)
        signals["help_seek_count"] = help_count

        # Store extracted signals
        self._extracted_signals.update(signals)
        return signals

    def get_all_signals(self) -> dict[str, float]:
        """Return all extracted signals for scoring."""
        return dict(self._extracted_signals)

    def map_to_indicators(
        self, chamber_id: str, interaction_id: str, indicator_ids: list[str]
    ) -> dict[str, float]:
        """Map extracted features to specific behavioral indicator IDs."""
        features = self.extract_features(chamber_id, interaction_id)
        mapped: dict[str, float] = {}

        # Signal type to feature name mapping
        type_to_feature = {
            SignalType.LATENCY: "response_latency",
            SignalType.REVISION: "revision_count",
            SignalType.DWELL: "dwell_time",
            SignalType.EXPLORATION: "exploration_coverage",
            SignalType.TEXT_LENGTH: "text_length",
            SignalType.CLICK_PATTERN: "click_pattern",
            SignalType.SCROLL_DEPTH: "scroll_depth",
            SignalType.HELP_SEEK: "help_seek_count",
        }

        for ind_id in indicator_ids:
            indicator = get_indicator_by_id(ind_id)
            if indicator and indicator.signal_type in type_to_feature:
                feature_name = type_to_feature[indicator.signal_type]
                if feature_name in features:
                    mapped[ind_id] = features[feature_name]

        return mapped

    def clear_buffer(self, chamber_id: str, interaction_id: str) -> None:
        """Clear the event buffer for a completed interaction."""
        key = f"{chamber_id}:{interaction_id}"
        self._buffers.pop(key, None)

    def get_buffer_stats(self) -> dict[str, int]:
        """Get buffer statistics for monitoring."""
        return {key: len(events) for key, events in self._buffers.items()}
