"""Risk API schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class RiskPublic(BaseModel):
    id: str
    project_id: str
    title: str
    description: str = ""
    severity: str = "medium"
    recommendation: str = ""
    evidence: list[str] = Field(default_factory=list)
    rule_id: Optional[str] = None
    generated_at: Optional[datetime] = None


class RiskListResponse(BaseModel):
    success: bool = True
    data: list[RiskPublic]
    message: Optional[str] = None
