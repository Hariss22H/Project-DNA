"""AI Project Onboarding Assistant schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.chat import ChatSource


class OnboardingSection(BaseModel):
    title: str
    content: str
    icon: str = "sparkles"


class OnboardingBriefingData(BaseModel):
    project_id: str
    project_name: str
    title: str
    markdown: str
    sections: list[OnboardingSection] = Field(default_factory=list)
    sources: list[ChatSource] = Field(default_factory=list)
    confidence: float = 0.0
    model_used: str
    fallback_used: bool = False
    retrieved_count: int = 0
    response_time_ms: int = 0
    generated_at: Optional[datetime] = None


class OnboardingBriefingResponse(BaseModel):
    success: bool = True
    data: OnboardingBriefingData
    message: Optional[str] = None
