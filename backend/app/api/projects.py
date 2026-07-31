"""Project workspace API routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.auth.deps import CurrentUser
from app.core.dependencies import get_db
from app.schemas.common import MessageResponse
from app.schemas.project import (
    ProjectCreate,
    ProjectListResponse,
    ProjectPublic,
    ProjectResponse,
    ProjectUpdate,
)
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a project workspace",
)
async def create_project(
    payload: ProjectCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> ProjectResponse:
    project = await ProjectService(db).create_project(
        user_id=current_user["id"],
        project_name=payload.project_name,
        description=payload.description,
    )
    return ProjectResponse(
        data=ProjectPublic(**project),
        message="Project created",
    )


@router.get(
    "",
    response_model=ProjectListResponse,
    summary="List projects for the current user",
)
async def list_projects(
    current_user: CurrentUser,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> ProjectListResponse:
    projects = await ProjectService(db).list_projects(user_id=current_user["id"])
    return ProjectListResponse(data=[ProjectPublic(**item) for item in projects])


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Get a project by id",
)
async def get_project(
    project_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> ProjectResponse:
    project = await ProjectService(db).get_project(
        user_id=current_user["id"],
        project_id=project_id,
    )
    return ProjectResponse(data=ProjectPublic(**project))


@router.put(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Update a project",
)
async def update_project(
    project_id: str,
    payload: ProjectUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> ProjectResponse:
    project = await ProjectService(db).update_project(
        user_id=current_user["id"],
        project_id=project_id,
        updates=payload.model_dump(exclude_unset=True),
    )
    return ProjectResponse(data=ProjectPublic(**project), message="Project updated")


@router.delete(
    "/{project_id}",
    response_model=MessageResponse,
    summary="Delete a project",
)
async def delete_project(
    project_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> MessageResponse:
    await ProjectService(db).delete_project(
        user_id=current_user["id"],
        project_id=project_id,
    )
    return MessageResponse(message="Project deleted")
