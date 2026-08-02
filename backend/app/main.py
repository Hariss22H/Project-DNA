"""FastAPI application entrypoint."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.router import api_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.database.indexes import ensure_indexes
from app.database.mongodb import mongodb

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    setup_logging(settings.debug)
    await mongodb.connect(settings)
    try:
        await ensure_indexes(mongodb.get_db())
    except Exception as exc:  # noqa: BLE001 — app should still boot for health checks
        logger.warning("Skipping index bootstrap: %s", exc)
    logger.info("Starting %s v%s (%s)", settings.app_name, __version__, settings.app_env)
    try:
        yield
    finally:
        await mongodb.disconnect()
        logger.info("Shutdown complete")


def create_app() -> FastAPI:
    """Application factory used by uvicorn and tests."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description=(
            "Project DNA — AI Knowledge Twin backend (Hackathon MVP).\n\n"
            "Phase 0: scaffold, MongoDB, Swagger, pluggable service interfaces.\n"
            "Phase 1: JWT authentication and project workspace CRUD.\n"
            "Phase 2: GitHub connect + document upload/extraction orchestration.\n"
            "Phase 3: Chunking, OpenAI embeddings, Qdrant indexing.\n"
            "Phase 4: RAG chat with OpenAI primary and Gemini fallback.\n"
            "Phase 5: Risks, timeline persistence, and dashboard APIs.\n"
            "Phase 6: Knowledge graph JSON for React Flow + demo polish."
        ),
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    @app.get("/", tags=["Health"], summary="API root")
    async def root() -> dict:
        return {
            "success": True,
            "data": {
                "name": settings.app_name,
                "version": __version__,
                "docs": "/docs",
                "health": f"{settings.api_v1_prefix}/health",
            },
        }

    app.include_router(api_router, prefix=settings.api_v1_prefix)
    return app


app = create_app()
