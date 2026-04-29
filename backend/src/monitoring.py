"""
Task 6.2 — Real-Time Monitoring of User Behavior and System Performance

Implements structured logging, metrics collection, and alerting hooks:
  1. Session lifecycle events (start, chamber_enter, complete, abandon)
  2. API latency tracking per endpoint
  3. LLM call success/failure rates
  4. Scoring pipeline timing
  5. User engagement metrics (completion rate, avg duration)
"""

from __future__ import annotations

import time
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("enclave.monitoring")


# ---------------------------------------------------------------------------
# Metrics Collector (in-memory, replaceable with Prometheus/StatsD)
# ---------------------------------------------------------------------------

@dataclass
class MetricPoint:
    """A single metric data point."""
    name: str
    value: float
    timestamp: float = 0.0
    tags: dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


class MetricsCollector:
    """Collects and aggregates application metrics."""

    def __init__(self):
        self._counters: dict[str, float] = defaultdict(float)
        self._gauges: dict[str, float] = {}
        self._histograms: dict[str, list[float]] = defaultdict(list)
        self._events: list[MetricPoint] = []

    # --- Counters ---
    def increment(self, name: str, value: float = 1.0, tags: dict[str, str] | None = None) -> None:
        key = self._make_key(name, tags)
        self._counters[key] += value

    # --- Gauges ---
    def gauge(self, name: str, value: float, tags: dict[str, str] | None = None) -> None:
        key = self._make_key(name, tags)
        self._gauges[key] = value

    # --- Histograms (latency, durations) ---
    def observe(self, name: str, value: float, tags: dict[str, str] | None = None) -> None:
        key = self._make_key(name, tags)
        self._histograms[key].append(value)

    # --- Events ---
    def record_event(self, name: str, data: dict[str, Any] | None = None) -> None:
        self._events.append(MetricPoint(
            name=name,
            value=1.0,
            tags=data or {},
        ))
        logger.info(f"EVENT: {name} | {data}")

    # --- Aggregation ---
    def get_summary(self) -> dict[str, Any]:
        summary: dict[str, Any] = {
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
        }
        for name, values in self._histograms.items():
            if values:
                sorted_v = sorted(values)
                n = len(sorted_v)
                summary.setdefault("histograms", {})[name] = {
                    "count": n,
                    "mean": sum(sorted_v) / n,
                    "p50": sorted_v[n // 2],
                    "p95": sorted_v[int(n * 0.95)] if n >= 20 else sorted_v[-1],
                    "p99": sorted_v[int(n * 0.99)] if n >= 100 else sorted_v[-1],
                    "min": sorted_v[0],
                    "max": sorted_v[-1],
                }
        summary["total_events"] = len(self._events)
        return summary

    def reset(self) -> None:
        self._counters.clear()
        self._gauges.clear()
        self._histograms.clear()
        self._events.clear()

    @staticmethod
    def _make_key(name: str, tags: dict[str, str] | None) -> str:
        if not tags:
            return name
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}|{tag_str}"


# ---------------------------------------------------------------------------
# Session Analytics
# ---------------------------------------------------------------------------

@dataclass
class SessionAnalytics:
    """Aggregated session analytics for monitoring dashboard."""
    total_sessions: int = 0
    completed_sessions: int = 0
    abandoned_sessions: int = 0
    avg_duration_ms: float = 0.0
    completion_rate: float = 0.0
    avg_signals_per_session: float = 0.0
    mode_distribution: dict[str, int] = field(default_factory=dict)


class AnalyticsTracker:
    """Tracks session-level analytics."""

    def __init__(self):
        self._sessions: dict[str, dict[str, Any]] = {}
        self._completed: list[dict[str, Any]] = []

    def session_started(self, session_id: str, mode: str) -> None:
        self._sessions[session_id] = {
            "start_time": time.time(),
            "mode": mode,
            "signals": 0,
        }

    def signal_recorded(self, session_id: str) -> None:
        if session_id in self._sessions:
            self._sessions[session_id]["signals"] += 1

    def session_completed(self, session_id: str) -> None:
        if session_id in self._sessions:
            session = self._sessions.pop(session_id)
            session["duration_ms"] = (time.time() - session["start_time"]) * 1000
            session["status"] = "completed"
            self._completed.append(session)

    def session_abandoned(self, session_id: str) -> None:
        if session_id in self._sessions:
            session = self._sessions.pop(session_id)
            session["duration_ms"] = (time.time() - session["start_time"]) * 1000
            session["status"] = "abandoned"
            self._completed.append(session)

    def get_analytics(self) -> SessionAnalytics:
        completed = [s for s in self._completed if s.get("status") == "completed"]
        abandoned = [s for s in self._completed if s.get("status") == "abandoned"]
        all_finished = completed + abandoned

        mode_dist: dict[str, int] = {}
        for s in all_finished:
            mode_dist[s.get("mode", "unknown")] = mode_dist.get(s.get("mode", "unknown"), 0) + 1

        avg_dur = sum(s.get("duration_ms", 0) for s in completed) / max(1, len(completed))
        avg_sig = sum(s.get("signals", 0) for s in completed) / max(1, len(completed))

        return SessionAnalytics(
            total_sessions=len(all_finished) + len(self._sessions),
            completed_sessions=len(completed),
            abandoned_sessions=len(abandoned),
            avg_duration_ms=round(avg_dur),
            completion_rate=round(len(completed) / max(1, len(all_finished)) * 100, 1),
            avg_signals_per_session=round(avg_sig, 1),
            mode_distribution=mode_dist,
        )


# ---------------------------------------------------------------------------
# Singletons
# ---------------------------------------------------------------------------

_metrics: MetricsCollector | None = None
_analytics: AnalyticsTracker | None = None


def get_metrics() -> MetricsCollector:
    global _metrics
    if _metrics is None:
        _metrics = MetricsCollector()
    return _metrics


def get_analytics() -> AnalyticsTracker:
    global _analytics
    if _analytics is None:
        _analytics = AnalyticsTracker()
    return _analytics
