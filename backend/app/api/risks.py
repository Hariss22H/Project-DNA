"""Risk analysis APIs."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.auth.deps import CurrentUser
from app.core.dependencies import get_db
from app.schemas.risk import RiskListResponse, RiskPublic
from app.services.risk_engine import RiskEngine

router = APIRouter(tags=["Risks"])


@router.post(
    "/projects/{project_id}/risks/analyze",
    response_model=RiskListResponse,
    summary="Generate rule-based project risks",
)
async def analyze_risks(
    project_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> RiskListResponse:
    risks = await RiskEngine(db).analyze_project(
        user_id=current_user["id"],
        project_id=project_id,
    )
    return RiskListResponse(
        data=[RiskPublic(**risk) for risk in risks],
        message=f"Generated {len(risks)} risk(s)",
    )


@router.get(
    "/projects/{project_id}/risks",
    response_model=RiskListResponse,
    summary="List generated project risks",
)
async def list_risks(
    project_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> RiskListResponse:
    risks = await RiskEngine(db, use_llm_summary=False).list_risks(
        user_id=current_user["id"],
        project_id=project_id,
    )
    return RiskListResponse(data=[RiskPublic(**risk) for risk in risks])


@router.get(
    "/risks/{project_id}",
    response_model=RiskListResponse,
    summary="List project risks (spec alias)",
)
async def risks_alias(
    project_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> RiskListResponse:
    return await list_risks(project_id=project_id, current_user=current_user, db=db)
