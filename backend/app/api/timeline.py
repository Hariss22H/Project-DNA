"""Timeline APIs — project memory and evolution story."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.auth.deps import CurrentUser
from app.core.dependencies import get_db, get_timeline_service
from app.schemas.timeline import TimelineEventPublic, TimelineListResponse
from app.services.project_service import ProjectService
from app.services.timeline import TimelineService
from app.services.timeline.story import enrich_timeline

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
    events = await timeline.list_events(project_id, limit=max(limit, 50))
    repository = await db["repositories"].find_one({"project_id": project_id})
    cards = enrich_timeline(
        project_id=project_id,
        events=events,
        repository=repository,
        limit=limit,
    )
    return TimelineListResponse(
        data=[
            TimelineEventPublic(
                id=str(card.get("id") or ""),
                project_id=project_id,
                event_type=str(card.get("event_type") or "event"),
                title=str(card.get("title") or "Event"),
                description=card.get("description"),
                source=str(card.get("source") or (card.get("metadata") or {}).get("source") or "System"),
                metadata=card.get("metadata") or {},
                created_at=card["created_at"],
            )
            for card in cards
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
