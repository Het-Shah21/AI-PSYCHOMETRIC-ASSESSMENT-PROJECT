"""
Phase 5+6 Tests — API Endpoints + Monitoring + Deployment Config

Task 5.3: API endpoints
Task 6.1: Deployment configuration
Task 6.2: Monitoring, metrics, analytics
"""

import time
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.monitoring import MetricsCollector, AnalyticsTracker, SessionAnalytics, get_metrics, get_analytics
from src.deployment import DeploymentConfig, generate_health_check_config, REQUIRED_ENV_VARS


# ═══════════════════════════════════════════════════════════════════
# TASK 5.3 — API (structural verification)
# ═══════════════════════════════════════════════════════════════════

class TestTask53API:

    def test_routers_importable(self):
        from src.routers.api import (
            session_router, signals_router, companion_router,
            scoring_router, external_router,
        )
        assert session_router is not None
        assert signals_router is not None

    def test_main_app_importable(self):
        from src.main import app
        assert app.title == "Abstract Enclave Assessment API"

    def test_routes_registered(self):
        from src.main import app
        routes = [r.path for r in app.routes]
        assert any("/api/v1" in r for r in routes)


# ═══════════════════════════════════════════════════════════════════
# TASK 6.1 — Deployment Config
# ═══════════════════════════════════════════════════════════════════

class TestTask61Deployment:

    def test_default_config_values(self):
        config = DeploymentConfig()
        assert config.backend_workers == 4
        assert config.backend_port == 8000
        assert config.frontend_port == 3000

    def test_session_ttl_reasonable(self):
        config = DeploymentConfig()
        assert 300 <= config.session_ttl_seconds <= 1800  # 5-30 min

    def test_required_env_vars_defined(self):
        assert "GOOGLE_API_KEY" in REQUIRED_ENV_VARS
        assert "DATABASE_URL" in REQUIRED_ENV_VARS
        assert len(REQUIRED_ENV_VARS) >= 4

    def test_health_check_config_structure(self):
        hc = generate_health_check_config()
        assert "backend" in hc
        assert "frontend" in hc
        assert "database" in hc
        assert "endpoint" in hc["backend"]
        assert hc["backend"]["interval_seconds"] > 0


# ═══════════════════════════════════════════════════════════════════
# TASK 6.2 — Monitoring
# ═══════════════════════════════════════════════════════════════════

class TestTask62Monitoring:

    def test_counter_increment(self):
        mc = MetricsCollector()
        mc.increment("requests", 1)
        mc.increment("requests", 1)
        summary = mc.get_summary()
        assert summary["counters"]["requests"] == 2.0

    def test_counter_with_tags(self):
        mc = MetricsCollector()
        mc.increment("errors", 1, {"code": "500"})
        mc.increment("errors", 1, {"code": "404"})
        summary = mc.get_summary()
        assert "errors|code=500" in summary["counters"]
        assert "errors|code=404" in summary["counters"]

    def test_gauge_set(self):
        mc = MetricsCollector()
        mc.gauge("sessions.active", 42)
        summary = mc.get_summary()
        assert summary["gauges"]["sessions.active"] == 42

    def test_gauge_overwrite(self):
        mc = MetricsCollector()
        mc.gauge("sessions.active", 10)
        mc.gauge("sessions.active", 20)
        summary = mc.get_summary()
        assert summary["gauges"]["sessions.active"] == 20

    def test_histogram_stats(self):
        mc = MetricsCollector()
        for v in [10, 20, 30, 40, 50, 60, 70, 80, 90, 100,
                  15, 25, 35, 45, 55, 65, 75, 85, 95, 105]:
            mc.observe("latency", v)
        summary = mc.get_summary()
        hist = summary["histograms"]["latency"]
        assert hist["count"] == 20
        assert hist["min"] == 10
        assert hist["max"] == 105
        assert 50 <= hist["mean"] <= 60

    def test_event_recording(self):
        mc = MetricsCollector()
        mc.record_event("session_started", {"session_id": "abc"})
        mc.record_event("session_completed", {"session_id": "abc"})
        summary = mc.get_summary()
        assert summary["total_events"] == 2

    def test_reset(self):
        mc = MetricsCollector()
        mc.increment("x", 5)
        mc.gauge("y", 10)
        mc.reset()
        summary = mc.get_summary()
        assert len(summary["counters"]) == 0
        assert len(summary["gauges"]) == 0

    def test_analytics_session_lifecycle(self):
        at = AnalyticsTracker()
        at.session_started("s1", "self-awareness")
        at.signal_recorded("s1")
        at.signal_recorded("s1")
        at.session_completed("s1")
        analytics = at.get_analytics()
        assert analytics.completed_sessions == 1
        assert analytics.abandoned_sessions == 0
        assert analytics.avg_signals_per_session == 2.0

    def test_analytics_abandoned(self):
        at = AnalyticsTracker()
        at.session_started("s1", "hiring")
        at.session_abandoned("s1")
        analytics = at.get_analytics()
        assert analytics.abandoned_sessions == 1

    def test_analytics_completion_rate(self):
        at = AnalyticsTracker()
        for i in range(10):
            at.session_started(f"s{i}", "educational")
        for i in range(7):
            at.session_completed(f"s{i}")
        for i in range(7, 10):
            at.session_abandoned(f"s{i}")
        analytics = at.get_analytics()
        assert analytics.completion_rate == 70.0

    def test_analytics_mode_distribution(self):
        at = AnalyticsTracker()
        at.session_started("s1", "hiring")
        at.session_started("s2", "hiring")
        at.session_started("s3", "self-awareness")
        at.session_completed("s1")
        at.session_completed("s2")
        at.session_completed("s3")
        analytics = at.get_analytics()
        assert analytics.mode_distribution["hiring"] == 2
        assert analytics.mode_distribution["self-awareness"] == 1

    def test_singleton_accessors(self):
        m1 = get_metrics()
        m2 = get_metrics()
        assert m1 is m2
        a1 = get_analytics()
        a2 = get_analytics()
        assert a1 is a2


class TestTask62Performance:

    def test_counter_speed(self):
        mc = MetricsCollector()
        start = time.perf_counter()
        for _ in range(100000):
            mc.increment("requests")
        elapsed = time.perf_counter() - start
        assert elapsed < 0.5, f"100k increments took {elapsed:.3f}s"

    def test_histogram_observe_speed(self):
        mc = MetricsCollector()
        start = time.perf_counter()
        for i in range(10000):
            mc.observe("latency", float(i))
        elapsed = time.perf_counter() - start
        assert elapsed < 0.2, f"10k observations took {elapsed:.3f}s"
