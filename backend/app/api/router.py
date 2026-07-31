"""Aggregate API router. Phase routers are mounted here as they land."""

from fastapi import APIRouter

from app.api import (
    auth,
    chat,
    dashboard,
    documents,
    graph,
    health,
    indexing,
    projects,
    repositories,
    risks,
    status,
    timeline,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(projects.router)
api_router.include_router(repositories.router)
api_router.include_router(documents.router)
api_router.include_router(indexing.router)
api_router.include_router(chat.router)
api_router.include_router(timeline.router)
api_router.include_router(risks.router)
api_router.include_router(dashboard.router)
api_router.include_router(graph.router)
api_router.include_router(status.router)
