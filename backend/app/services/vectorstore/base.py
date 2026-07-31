"""Vector store contract for project-isolated chunk storage."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

from pydantic import BaseModel, Field


class VectorPoint(BaseModel):
    id: str
    vector: list[float]
    payload: dict[str, Any] = Field(default_factory=dict)


class VectorSearchResult(BaseModel):
    id: str
    score: float
    payload: dict[str, Any] = Field(default_factory=dict)


class VectorStore(ABC):
    @abstractmethod
    async def ensure_collection(self, *, vector_size: int) -> None:
        """Create collection if missing."""

    @abstractmethod
    async def upsert(self, points: list[VectorPoint]) -> int:
        """Insert or update points. Returns count upserted."""

    @abstractmethod
    async def delete_by_project(self, project_id: str) -> None:
        """Remove all vectors for a project."""

    @abstractmethod
    async def search(
        self,
        *,
        project_id: str,
        query_vector: list[float],
        top_k: int = 5,
    ) -> list[VectorSearchResult]:
        """Similarity search scoped to one project."""

    @abstractmethod
    async def count_by_project(self, project_id: str) -> int:
        """Count indexed vectors for a project."""
