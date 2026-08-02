"""In-memory vector store for tests / local fallback."""

from __future__ import annotations

import math
from typing import Optional

from app.services.vectorstore.base import VectorPoint, VectorSearchResult, VectorStore


class InMemoryVectorStore(VectorStore):
    def __init__(self) -> None:
        self._points: dict[str, VectorPoint] = {}
        self._vector_size: Optional[int] = None

    async def ensure_collection(self, *, vector_size: int) -> None:
        self._vector_size = vector_size

    async def upsert(self, points: list[VectorPoint]) -> int:
        for point in points:
            self._points[point.id] = point
        return len(points)

    async def delete_by_project(self, project_id: str) -> None:
        to_delete = [
            point_id
            for point_id, point in self._points.items()
            if point.payload.get("project_id") == project_id
        ]
        for point_id in to_delete:
            del self._points[point_id]

    async def search(
        self,
        *,
        project_id: str,
        query_vector: list[float],
        top_k: int = 5,
    ) -> list[VectorSearchResult]:
        scored: list[VectorSearchResult] = []
        for point in self._points.values():
            if point.payload.get("project_id") != project_id:
                continue
            score = _cosine(query_vector, point.vector)
            scored.append(
                VectorSearchResult(id=point.id, score=score, payload=point.payload)
            )
        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[:top_k]

    async def count_by_project(self, project_id: str) -> int:
        return sum(1 for point in self._points.values() if point.payload.get("project_id") == project_id)


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)
