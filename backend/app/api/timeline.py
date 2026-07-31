"""Timeline APIs."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.auth.deps import CurrentUser
from app.core.dependencies import get_db, get_timeline_service
from app.schemas.timeline import TimelineEventPublic, TimelineListResponse
from app.services.project_service import ProjectService
from app.services.timeline import TimelineService

router = APIRouter(tags=["Timeline"])


async def _timeline_response(
    *,
    project_id: str,
    user_id: str,
    db: AsyncIOMotorDatabase,
    timeline: TimelineService,
    limit: int,
) -> TimelineListResponse:
    await ProjectService(db).get_project(user_id=user_id, project_id=project_id)
    events = await timeline.list_events(project_id, limit=limit)
    return TimelineListResponse(
        data=[
            TimelineEventPublic(
                id=event.id,
                project_id=event.project_id,
                event_type=event.event_type,
                title=event.title,
                description=event.description,
                metadata=event.metadata,
                created_at=event.created_at,
            )
            for event in events
        ]
    )


@router.get(
    "/projects/{project_id}/timeline",
    response_model=TimelineListResponse,
    summary="Get project activity timeline",
)
async def project_timeline(
    project_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
    timeline: Annotated[TimelineService, Depends(get_timeline_service)],
    limit: int = Query(default=50, ge=1, le=200),
) -> TimelineListResponse:
    return await _timeline_response(
        project_id=project_id,
        user_id=current_user["id"],
        db=db,
        timeline=timeline,
        limit=limit,
    )


@router.get(
    "/timeline/{project_id}",
    response_model=TimelineListResponse,
    summary="Get project timeline (spec alias)",
)
async def timeline_alias(
    project_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
    timeline: Annotated[TimelineService, Depends(get_timeline_service)],
    limit: int = Query(default=50, ge=1, le=200),
) -> TimelineListResponse:
    return await _timeline_response(
        project_id=project_id,
        user_id=current_user["id"],
        db=db,
        timeline=timeline,
        limit=limit,
    )
