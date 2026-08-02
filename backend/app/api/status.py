"""Project status API."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.auth.deps import CurrentUser
from app.core.dependencies import get_db
from app.schemas.status import ProjectStatusData, ProjectStatusResponse
from app.services.status_service import StatusService

router = APIRouter(prefix="/projects/{project_id}", tags=["Projects"])


@router.get(
    "/status",
    response_model=ProjectStatusResponse,
    summary="Get project ingestion / readiness status",
)
async def get_project_status(
    project_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> ProjectStatusResponse:
    data = await StatusService(db).get_status(
        user_id=current_user["id"],
        project_id=project_id,
    )
    return ProjectStatusResponse(data=ProjectStatusData(**data))
