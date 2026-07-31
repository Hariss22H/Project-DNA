"""Qdrant Cloud vector store implementation."""

from __future__ import annotations

import logging
from typing import Optional
from uuid import NAMESPACE_URL, uuid5

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qmodels

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.services.vectorstore.base import VectorPoint, VectorSearchResult, VectorStore

logger = logging.getLogger(__name__)


class QdrantVectorStore(VectorStore):
    def __init__(
        self,
        *,
        url: Optional[str] = None,
        api_key: Optional[str] = None,
        collection: Optional[str] = None,
    ) -> None:
        settings = get_settings()
        self._url = url if url is not None else settings.qdrant_url
        self._api_key = api_key if api_key is not None else settings.qdrant_api_key
        self._collection = collection or settings.qdrant_collection
        self._client: Optional[AsyncQdrantClient] = None

    def _get_client(self) -> AsyncQdrantClient:
        if not self._url:
            raise AppError(
                "QDRANT_URL is not configured",
                status_code=500,
                code="qdrant_not_configured",
            )
        if self._client is None:
            self._client = AsyncQdrantClient(url=self._url, api_key=self._api_key or None)
        return self._client

    async def ensure_collection(self, *, vector_size: int) -> None:
        client = self._get_client()
        try:
            collections = await client.get_collections()
            existing = {item.name for item in collections.collections}
            if self._collection in existing:
                return
            await client.create_collection(
                collection_name=self._collection,
                vectors_config=qmodels.VectorParams(
                    size=vector_size,
                    distance=qmodels.Distance.COSINE,
                ),
            )
            await client.create_payload_index(
                collection_name=self._collection,
                field_name="project_id",
                field_schema=qmodels.PayloadSchemaType.KEYWORD,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to ensure Qdrant collection")
            raise AppError(
                "Failed to initialize Qdrant collection",
                status_code=502,
                code="qdrant_init_failed",
                details=str(exc),
            ) from exc

    async def upsert(self, points: list[VectorPoint]) -> int:
        if not points:
            return 0
        client = self._get_client()
        qdrant_points = [
            qmodels.PointStruct(
                id=_to_qdrant_id(point.id),
                vector=point.vector,
                payload={**point.payload, "point_key": point.id},
            )
            for point in points
        ]
        try:
            await client.upsert(collection_name=self._collection, points=qdrant_points)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Qdrant upsert failed")
            raise AppError(
                "Failed to upsert vectors into Qdrant",
                status_code=502,
                code="qdrant_upsert_failed",
                details=str(exc),
            ) from exc
        return len(points)

    async def delete_by_project(self, project_id: str) -> None:
        client = self._get_client()
        try:
            await client.delete(
                collection_name=self._collection,
                points_selector=qmodels.FilterSelector(
                    filter=qmodels.Filter(
                        must=[
                            qmodels.FieldCondition(
                                key="project_id",
                                match=qmodels.MatchValue(value=project_id),
                            )
                        ]
                    )
                ),
            )
        except Exception as exc:  # noqa: BLE001
            # Collection may not exist yet on first index.
            logger.warning("Qdrant delete_by_project warning: %s", exc)

    async def search(
        self,
        *,
        project_id: str,
        query_vector: list[float],
        top_k: int = 5,
    ) -> list[VectorSearchResult]:
        client = self._get_client()
        try:
            results = await client.search(
                collection_name=self._collection,
                query_vector=query_vector,
                limit=top_k,
                query_filter=qmodels.Filter(
                    must=[
                        qmodels.FieldCondition(
                            key="project_id",
                            match=qmodels.MatchValue(value=project_id),
                        )
                    ]
                ),
                with_payload=True,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Qdrant search failed")
            raise AppError(
                "Failed to search Qdrant",
                status_code=502,
                code="qdrant_search_failed",
                details=str(exc),
            ) from exc

        output: list[VectorSearchResult] = []
        for item in results:
            payload = dict(item.payload or {})
            point_id = str(payload.get("point_key") or item.id)
            output.append(
                VectorSearchResult(
                    id=point_id,
                    score=float(item.score or 0.0),
                    payload=payload,
                )
            )
        return output

    async def count_by_project(self, project_id: str) -> int:
        client = self._get_client()
        try:
            result = await client.count(
                collection_name=self._collection,
                count_filter=qmodels.Filter(
                    must=[
                        qmodels.FieldCondition(
                            key="project_id",
                            match=qmodels.MatchValue(value=project_id),
                        )
                    ]
                ),
                exact=True,
            )
            return int(result.count)
        except Exception:  # noqa: BLE001
            return 0


def _to_qdrant_id(point_id: str) -> str:
    """Convert arbitrary string ids into stable UUIDs for Qdrant."""
    return str(uuid5(NAMESPACE_URL, point_id))
