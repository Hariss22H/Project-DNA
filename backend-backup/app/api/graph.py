"""Knowledge graph APIs (React Flow JSON, no Neo4j)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.auth.deps import CurrentUser
from app.core.dependencies import get_db
from app.schemas.graph import (
    GraphEdgePublic,
    GraphNodePublic,
    KnowledgeGraphPublic,
    KnowledgeGraphResponse,
)
from app.services.knowledge_graph_service import KnowledgeGraphService

router = APIRouter(tags=["Knowledge Graph"])


def _to_response(payload: dict) -> KnowledgeGraphResponse:
    return KnowledgeGraphResponse(
        data=KnowledgeGraphPublic(
            project_id=payload["project_id"],
            nodes=[GraphNodePublic(**node) for node in payload.get("nodes") or []],
            edges=[GraphEdgePublic(**edge) for edge in payload.get("edges") or []],
            entity_count=int(payload.get("entity_count") or 0),
            generated_at=payload.get("generated_at"),
            cached=bool(payload.get("cached")),
        ),
        message="Knowledge graph ready",
    )


@router.get(
    "/projects/{project_id}/graph",
    response_model=KnowledgeGraphResponse,
    summary="Get React Flow knowledge graph JSON",
)
async def get_project_graph(
    project_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
    refresh: bool = Query(default=False, description="Force rebuild from latest sources"),
) -> KnowledgeGraphResponse:
    payload = await KnowledgeGraphService(db).get_graph(
        user_id=current_user["id"],
        project_id=project_id,
        refresh=refresh,
    )
    return _to_response(payload)


@router.post(
    "/projects/{project_id}/graph/rebuild",
    response_model=KnowledgeGraphResponse,
    summary="Rebuild knowledge graph from current project entities",
)
async def rebuild_project_graph(
    project_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> KnowledgeGraphResponse:
    payload = await KnowledgeGraphService(db).get_graph(
        user_id=current_user["id"],
        project_id=project_id,
        refresh=True,
    )
    return _to_response(payload)


@router.get(
    "/knowledge-graph/{project_id}",
    response_model=KnowledgeGraphResponse,
    summary="Get knowledge graph (spec alias)",
)
async def knowledge_graph_alias(
    project_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
    refresh: bool = Query(default=False),
) -> KnowledgeGraphResponse:
    return await get_project_graph(
        project_id=project_id,
        current_user=current_user,
        db=db,
        refresh=refresh,
    )
