"""Knowledge graph contracts — JSON for React Flow (no Neo4j)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class GraphNode(BaseModel):
    id: str
    label: str
    type: Literal["file", "module", "technology", "api", "document", "feature", "repository", "other"] = "other"
    data: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    label: Optional[str] = None
    relation: str = "related_to"
    data: dict[str, Any] = Field(default_factory=dict)


class KnowledgeGraphData(BaseModel):
    """Payload consumed directly by the frontend React Flow page."""

    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)


class ProjectEntity(BaseModel):
    """Lightweight extracted entity used to build the graph."""

    id: str
    name: str
    entity_type: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class KnowledgeGraphBuilder(ABC):
    """Member 3 implements entity extraction + relationship mapping."""

    @abstractmethod
    async def build_graph(
        self,
        *,
        project_id: str,
        entities: list[ProjectEntity],
    ) -> KnowledgeGraphData:
        """Build React Flow compatible graph JSON from project entities."""
