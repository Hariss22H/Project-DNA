"""Knowledge graph API schemas for React Flow."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class GraphNodePublic(BaseModel):
    id: str
    label: str
    type: str = "other"
    data: dict[str, Any] = Field(default_factory=dict)


class GraphEdgePublic(BaseModel):
    id: str
    source: str
    target: str
    label: Optional[str] = None
    relation: str = "related_to"
    data: dict[str, Any] = Field(default_factory=dict)


class KnowledgeGraphPublic(BaseModel):
    project_id: str
    nodes: list[GraphNodePublic] = Field(default_factory=list)
    edges: list[GraphEdgePublic] = Field(default_factory=list)
    entity_count: int = 0
    generated_at: Optional[datetime] = None
    cached: bool = False


class KnowledgeGraphResponse(BaseModel):
    success: bool = True
    data: KnowledgeGraphPublic
    message: Optional[str] = None
