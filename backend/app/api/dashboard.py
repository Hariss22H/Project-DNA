"""Dashboard aggregation APIs."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.auth.deps import CurrentUser
from app.core.dependencies import get_db
from app.schemas.dashboard import DashboardData, DashboardResponse
from app.schemas.risk import RiskPublic
from app.services.dashboard_service import DashboardService

router = APIRouter(tags=["Dashboard"])


async def _dashboard(
    *,
    project_id: str,
    user_id: str,
    db: AsyncIOMotorDatabase,
) -> DashboardResponse:
    data = await DashboardService(db).get_dashboard(user_id=user_id, project_id=project_id)
    return DashboardResponse(
        data=DashboardData(
            **{
                **data,
                "risks": [RiskPublic(**risk) for risk in data.get("risks") or []],
            }
        ),
        message="Dashboard loaded",
    )


@router.get(
    "/projects/{project_id}/dashboard",
    response_model=DashboardResponse,
    summary="Get project intelligence dashboard",
)
async def project_dashboard(
    project_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> DashboardResponse:
    return await _dashboard(project_id=project_id, user_id=current_user["id"], db=db)


@router.get(
    "/dashboard/{project_id}",
    response_model=DashboardResponse,
    summary="Get project dashboard (spec alias)",
)
async def dashboard_alias(
    project_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> DashboardResponse:
    return await _dashboard(project_id=project_id, user_id=current_user["id"], db=db)
