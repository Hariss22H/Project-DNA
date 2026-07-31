"""Aggregate API router. Phase routers are mounted here as they land."""

from fastapi import APIRouter

from app.api import (
    auth,
    chat,
    dashboard,
    documents,
    docx,
    github,
    graph,
    health,
    indexing,
    m3_graph,
    m3_timeline,
    metadata,
    pdf,
    projects,
    repositories,
    repository,
    risks,
    status,
    timeline,
    upload,
)

api_router = APIRouter()

# Member 1 — core product APIs
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

# Member 3 — integration/utility connectors (coexist without overriding core routes)
api_router.include_router(github.router)
api_router.include_router(repository.router)
api_router.include_router(upload.router)
api_router.include_router(pdf.router)
api_router.include_router(docx.router)
api_router.include_router(metadata.router)
api_router.include_router(m3_timeline.router)
api_router.include_router(m3_graph.router)
