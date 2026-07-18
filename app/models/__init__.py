"""SQLAlchemy ORM models."""
from __future__ import annotations

from app.models.base import Base
from app.models.user import User
from app.models.session import PloggingSession, SessionStatus
from app.models.route_point import RoutePoint
from app.models.trash import TrashRecord, TrashStatus, TrashType
from app.models.detection_log import DetectionLog

__all__ = [
    "Base",
    "User",
    "PloggingSession",
    "SessionStatus",
    "RoutePoint",
    "TrashRecord",
    "TrashStatus",
    "TrashType",
    "DetectionLog",
]