"""Application configuration loaded from environment variables."""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_name: str = "EcoLens"
    env: str = "local"
    debug: bool = True
    api_prefix: str = "/api"

    # Database
    database_url: str = (
        "postgresql+psycopg2://ecolens:ecolens@db:5432/ecolens"
    )

    # JWT
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # AI
    ai_mode: Literal["mock", "yolo"] = "mock"
    ai_service_url: str = "http://ai:8001"

    # Storage
    storage_type: Literal["local", "s3"] = "local"
    storage_local_path: str = "./storage"
    s3_endpoint: str = ""
    s3_bucket: str = ""
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""

    # Deduplication
    dedup_time_seconds: int = 15
    dedup_distance_meters: float = 8.0

    # Detection
    detection_min_confidence: float = 0.7

    # Location
    location_min_accuracy_meters: float = 50.0
    location_max_speed_mps: float = 7.0
    location_min_interval_seconds: float = 5.0
    location_min_distance_meters: float = 5.0

    # Score table (type -> score)
    score_general: int = 3
    score_paper_cup: int = 4
    score_can: int = 5
    score_plastic_bottle: int = 6
    score_vinyl: int = 6
    score_glass_bottle: int = 8
    score_bulky: int = 20

    def score_for(self, trash_type: str) -> int:
        """Return base score for a trash type. Unknown → general."""
        mapping = {
            "general": self.score_general,
            "paper_cup": self.score_paper_cup,
            "can": self.score_can,
            "plastic_bottle": self.score_plastic_bottle,
            "vinyl": self.score_vinyl,
            "glass_bottle": self.score_glass_bottle,
            "bulky": self.score_bulky,
        }
        return mapping.get(trash_type, self.score_general)


@lru_cache
def get_settings() -> Settings:  # pragma: no cover - simple caching
    """Return a cached settings instance."""
    return Settings()