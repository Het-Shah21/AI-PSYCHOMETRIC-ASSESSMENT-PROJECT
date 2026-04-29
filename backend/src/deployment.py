"""
Task 6.1 — Deployment Configuration

Docker Compose stack for production:
  - FastAPI backend (uvicorn)
  - Next.js frontend (standalone build)
  - PostgreSQL database
  - Redis cache (session + rate limiting)
  - Nginx reverse proxy + CDN headers
"""

# This module provides deployment configuration generators.
# Actual Docker/Nginx files are in project root.

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


REQUIRED_ENV_VARS: Final[list[str]] = [
    "GOOGLE_API_KEY",
    "DATABASE_URL",
    "REDIS_URL",
    "SECRET_KEY",
    "CORS_ORIGINS",
]


@dataclass(frozen=True)
class DeploymentConfig:
    """Production deployment configuration."""
    backend_workers: int = 4
    backend_port: int = 8000
    frontend_port: int = 3000
    db_pool_size: int = 20
    db_max_overflow: int = 10
    redis_max_connections: int = 50
    session_ttl_seconds: int = 600       # 10-min session TTL
    rate_limit_rpm: int = 60             # Requests per minute per IP
    cdn_cache_max_age: int = 86400       # Static assets: 24h
    enable_gzip: bool = True
    enable_brotli: bool = True
    log_level: str = "info"


def generate_health_check_config() -> dict:
    """Generate health check endpoints for orchestrator."""
    return {
        "backend": {
            "endpoint": "/api/v1/external/health",
            "interval_seconds": 30,
            "timeout_seconds": 5,
            "unhealthy_threshold": 3,
        },
        "frontend": {
            "endpoint": "/",
            "interval_seconds": 30,
            "timeout_seconds": 5,
            "unhealthy_threshold": 3,
        },
        "database": {
            "type": "tcp",
            "port": 5432,
            "interval_seconds": 10,
        },
    }
