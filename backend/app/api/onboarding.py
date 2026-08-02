"""AI Project Onboarding Assistant APIs."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.auth.deps import CurrentUser
from app.core.dependencies import get_db
from app.schemas.onboarding import (
    OnboardingBriefingData,
    OnboardingBriefingResponse,
    OnboardingSection,
)
from app.schemas.chat import ChatSource
from app.services.onboarding_service import OnboardingService

router = APIRouter(tags=["Onboarding"])


@router.post(
    "/projects/{project_id}/onboarding/briefing",
    response_model=OnboardingBriefingResponse,
    summary="Generate an AI onboarding briefing for a new developer",
)
async def generate_onboarding_briefing(
    project_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> OnboardingBriefingResponse:
    data = await OnboardingService(db).generate_briefing(
        user_id=current_user["id"],
        project_id=project_id,
    )
    return OnboardingBriefingResponse(
        data=OnboardingBriefingData(
            project_id=data["project_id"],
            project_name=data["project_name"],
            title=data["title"],
            markdown=data["markdown"],
            sections=[OnboardingSection(**section) for section in data.get("sections") or []],
            sources=[ChatSource(**source) for source in data.get("sources") or []],
            confidence=data.get("confidence", 0.0),
            model_used=data["model_used"],
            fallback_used=data.get("fallback_used", False),
            retrieved_count=data.get("retrieved_count", 0),
            response_time_ms=data.get("response_time_ms", 0),
            generated_at=data.get("generated_at"),
        ),
        message="Onboarding briefing generated",
    )
