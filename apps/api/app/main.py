"""FastAPI application entrypoint."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.config import get_settings
from app.routers import roadmaps, users


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="AI Engineer OS API",
        version=__version__,
        description="Backend for the AI Engineering Learning OS.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/healthz", tags=["health"])
    def healthz() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    app.include_router(users.router)
    app.include_router(roadmaps.router)

    return app


app = create_app()
