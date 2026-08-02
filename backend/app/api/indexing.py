"""Knowledge indexing API routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.auth.deps import CurrentUser
from app.core.dependencies import get_db
from app.schemas.indexing import (
    IndexResponse,
    IndexResultData,
    IndexStatusData,
    IndexStatusResponse,
)
from app.services.indexing_service import IndexingService

router = APIRouter(prefix="/projects/{project_id}", tags=["Indexing"])


@router.post(
    "/index",
    response_model=IndexResponse,
    summary="Chunk, embed, and index project knowledge into Qdrant",
)
async def index_project(
    project_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> IndexResponse:
    data = await IndexingService(db).index_project(
        user_id=current_user["id"],
        project_id=project_id,
    )
    return IndexResponse(
        data=IndexResultData(**data),
        message=data.get("message") or "Indexing complete",
    )


@router.get(
    "/index",
    response_model=IndexStatusResponse,
    summary="Get project indexing status",
)
async def get_index_status(
    project_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> IndexStatusResponse:
    data = await IndexingService(db).get_index_status(
        user_id=current_user["id"],
        project_id=project_id,
    )
    return IndexStatusResponse(data=IndexStatusData(**data))
