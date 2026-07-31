"""Dashboard API schemas."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field

from app.schemas.project import ProjectStatus
from app.schemas.risk import RiskPublic


class DashboardData(BaseModel):
    project_id: str
    project_name: str
    project_status: ProjectStatus
    health_score: float
    health_label: str
    knowledge_coverage: float
    ai_confidence: float
    connected_sources: list[dict[str, Any]] = Field(default_factory=list)
    connected_sources_count: int = 0
    indexed_documents_count: int = 0
    chunks_indexed: int = 0
    github_connected: bool = False
    has_readme: bool = False
    risks: list[RiskPublic] = Field(default_factory=list)
    risk_count: int = 0
    high_risk_count: int = 0
    timeline: list[dict[str, Any]] = Field(default_factory=list)
    recent_documents: list[dict[str, Any]] = Field(default_factory=list)
    recent_conversations: list[dict[str, Any]] = Field(default_factory=list)
    ai_insights: list[dict[str, str]] = Field(default_factory=list)
    knowledge_graph_preview: dict[str, Any] = Field(
        default_factory=lambda: {"nodes": [], "edges": [], "entity_count": 0}
    )


class DashboardResponse(BaseModel):
    success: bool = True
    data: DashboardData
    message: Optional[str] = None
