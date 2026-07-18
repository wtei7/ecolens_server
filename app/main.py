"""FastAPI application entry point."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        debug=settings.debug,
        lifespan=lifespan,
    )

    @app.get("/health", tags=["meta"])
    def health() -> dict:
        return {"status": "ok", "service": settings.app_name, "ai_mode": settings.ai_mode}

    @app.get("/ready", tags=["meta"])
    def ready() -> dict:
        return {"status": "ready"}

    # Routers are mounted here as they are implemented in later stages.
    # Example:
    # from app.api.v1 import api_router
    # app.include_router(api_router, prefix=settings.api_prefix)

    return app


app = create_app()