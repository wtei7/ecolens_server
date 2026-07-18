"""Route point ORM model with PostGIS location."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class RoutePoint(Base):
    __tablename__ = "route_points"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("plogging_sessions.id"), nullable=False, index=True)

    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    accuracy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    # PostGIS POINT(lng lat), SRID 4326. Nullable so SQLite tests can skip.
    location: Mapped[Optional[object]] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=True,
    )