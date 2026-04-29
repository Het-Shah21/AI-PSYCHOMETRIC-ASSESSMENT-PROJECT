"""
Task 3.2 — Database Models for Session Management and Data Logging

SQLAlchemy 2.0 async models for:
  - Sessions (with consent tracking)
  - Behavioral signals (anonymized)
  - Scores and explanations
  - Consent records (GDPR compliant)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    String, Float, Integer, DateTime, Text, JSON,
    ForeignKey, Boolean, Index,
)
from sqlalchemy.orm import (
    DeclarativeBase, Mapped, mapped_column, relationship,
)


class Base(DeclarativeBase):
    pass


class Session(Base):
    """A single assessment session."""
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    anonymous_id: Mapped[str] = mapped_column(String(64), index=True, default=lambda: uuid.uuid4().hex)
    mode: Mapped[str] = mapped_column(String(20))  # self-awareness, hiring, educational, therapeutic
    chamber_order: Mapped[dict] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active, completed, abandoned
    consent_given: Mapped[bool] = mapped_column(Boolean, default=False)
    consent_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Relationships
    signals: Mapped[list["BehavioralSignal"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    scores: Mapped[list["Score"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    consent_record: Mapped["ConsentRecord | None"] = relationship(back_populates="session", uselist=False)

    __table_args__ = (
        Index("ix_sessions_status_mode", "status", "mode"),
    )


class BehavioralSignal(Base):
    """A single captured behavioral event (anonymized)."""
    __tablename__ = "behavioral_signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"))
    chamber_id: Mapped[str] = mapped_column(String(30))
    interaction_id: Mapped[str] = mapped_column(String(30))
    signal_type: Mapped[str] = mapped_column(String(30))   # Maps to SignalType enum
    signal_id: Mapped[str] = mapped_column(String(50))      # Maps to BehavioralIndicator.id
    value: Mapped[float] = mapped_column(Float)
    raw_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # Additional context
    timestamp_ms: Mapped[int] = mapped_column(Integer)       # Relative to session start
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    session: Mapped["Session"] = relationship(back_populates="signals")

    __table_args__ = (
        Index("ix_signals_session_chamber", "session_id", "chamber_id"),
    )


class Score(Base):
    """Computed score for a construct."""
    __tablename__ = "scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"))
    construct_id: Mapped[str] = mapped_column(String(30))
    scaled_score: Mapped[float] = mapped_column(Float)        # 1-10
    raw_score: Mapped[float] = mapped_column(Float)            # 0-1
    confidence_lower: Mapped[float] = mapped_column(Float)
    confidence_upper: Mapped[float] = mapped_column(Float)
    evidence_count: Mapped[int] = mapped_column(Integer)
    sub_facet_breakdown: Mapped[dict] = mapped_column(JSON, default=dict)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    session: Mapped["Session"] = relationship(back_populates="scores")


class ConsentRecord(Base):
    """GDPR-compliant consent tracking."""
    __tablename__ = "consent_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"), unique=True)
    data_collection_consent: Mapped[bool] = mapped_column(Boolean, default=False)
    webcam_consent: Mapped[bool] = mapped_column(Boolean, default=False)
    analytics_consent: Mapped[bool] = mapped_column(Boolean, default=False)
    ip_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)  # Hashed, not raw
    consent_text_version: Mapped[str] = mapped_column(String(10), default="1.0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    session: Mapped["Session"] = relationship(back_populates="consent_record")
