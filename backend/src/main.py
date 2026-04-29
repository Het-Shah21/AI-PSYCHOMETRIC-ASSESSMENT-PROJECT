"""
Abstract Enclave Assessment — FastAPI Application Entry Point
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers.api import (
    session_router,
    signals_router,
    companion_router,
    scoring_router,
    external_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle: startup and shutdown."""
    # Startup: initialize services
    from .services.llm_service import get_llm_gateway
    get_llm_gateway()  # Warm up LLM connection
    yield
    # Shutdown: cleanup


app = FastAPI(
    title="Abstract Enclave Assessment API",
    description="AI-powered psychometric assessment backend",
    version="1.0.0",
    lifespan=lifespan,
)

import os

# CORS
cors_origins = os.environ.get(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:5173"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(session_router, prefix="/api/v1")
app.include_router(signals_router, prefix="/api/v1")
app.include_router(companion_router, prefix="/api/v1")
app.include_router(scoring_router, prefix="/api/v1")
app.include_router(external_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"name": "Abstract Enclave Assessment", "version": "1.0.0"}
