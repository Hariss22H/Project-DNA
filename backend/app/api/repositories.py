"""GitHub repository API routes (orchestration only; connector is pluggable)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.auth.deps import CurrentUser
from app.core.dependencies import get_db, get_github_service
from app.schemas.repository import ConnectGitHubRequest, RepositoryPublic, RepositoryResponse
from app.services.github import GitHubService
from app.services.repository_service import RepositoryService

router = APIRouter(prefix="/projects/{project_id}/github", tags=["GitHub"])


@router.post(
    "",
    response_model=RepositoryResponse,
    summary="Connect a public GitHub repository",
)
async def connect_github(
    project_id: str,
    payload: ConnectGitHubRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
    github: Annotated[GitHubService, Depends(get_github_service)],
) -> RepositoryResponse:
    data = await RepositoryService(db, github_service=github).connect_repository(
        user_id=current_user["id"],
        project_id=project_id,
        repository_url=payload.repository_url,
    )
    return RepositoryResponse(
        data=RepositoryPublic(**data),
        message="GitHub repository connected",
    )


@router.get(
    "",
    response_model=RepositoryResponse,
    summary="Get connected GitHub repository metadata",
)
async def get_github(
    project_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> RepositoryResponse:
    data = await RepositoryService(db).get_repository(
        user_id=current_user["id"],
        project_id=project_id,
    )
    return RepositoryResponse(data=RepositoryPublic(**data))
