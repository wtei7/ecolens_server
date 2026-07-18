"""Plogging session ORM model."""
from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SessionStatus(str, enum.Enum):
    active = "active"
    paused = "paused"
    completed = "completed"
    cancelled = "cancelled"


class PloggingSession(Base):
    __tablename__ = "plogging_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    status: Mapped[SessionStatus] = mapped_column(Enum(SessionStatus), default=SessionStatus.active, nullable=False, index=True)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    duration_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    distance_meters: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    detected_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cleaned_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    uncollected_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    start_latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    start_longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    end_latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    end_longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)