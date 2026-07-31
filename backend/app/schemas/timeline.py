"""Timeline API schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class TimelineEventPublic(BaseModel):
    id: Optional[str] = None
    project_id: str
    event_type: str
    title: str
    description: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class TimelineListResponse(BaseModel):
    success: bool = True
    data: list[TimelineEventPublic]
