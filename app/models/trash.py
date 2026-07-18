"""Trash record ORM model with PostGIS location."""
from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TrashStatus(str, enum.Enum):
    detected = "detected"
    verification_pending = "verification_pending"
    cleaned = "cleaned"
    not_cleaned = "not_cleaned"
    uncertain = "uncertain"


class TrashType(str, enum.Enum):
    general = "general"
    paper_cup = "paper_cup"
    can = "can"
    plastic_bottle = "plastic_bottle"
    vinyl = "vinyl"
    glass_bottle = "glass_bottle"
    bulky = "bulky"


class TrashRecord(Base):
    __tablename__ = "trash_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("plogging_sessions.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    type: Mapped[TrashType] = mapped_column(Enum(TrashType), nullable=False, index=True)
    status: Mapped[TrashStatus] = mapped_column(Enum(TrashStatus), default=TrashStatus.detected, nullable=False, index=True)

    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    before_image_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    after_image_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    cleaned_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    detection_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # PostGIS POINT(lng lat). Nullable for SQLite tests.
    location: Mapped[Optional[object]] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=True,
    )