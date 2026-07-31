"""OpenAI embedding client (text-embedding-3-small only)."""

from __future__ import annotations

import logging
from typing import Optional

from openai import AsyncOpenAI

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.services.embeddings.base import EmbeddingService

logger = logging.getLogger(__name__)


class OpenAIEmbeddingService(EmbeddingService):
    """Uses OpenAI embeddings only — never mix providers (same vector space)."""

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        dimensions: Optional[int] = None,
    ) -> None:
        settings = get_settings()
        self._api_key = api_key if api_key is not None else settings.openai_api_key
        self._model = model or settings.openai_embedding_model
        self._dimensions = dimensions or settings.embedding_dimensions
        self._client = AsyncOpenAI(api_key=self._api_key or "missing-key")

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def dimensions(self) -> int:
        return self._dimensions

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if not self._api_key:
            raise AppError(
                "OPENAI_API_KEY is not configured",
                status_code=500,
                code="openai_not_configured",
            )

        # OpenAI rejects empty strings; keep alignment with input order.
        sanitized = [text if text.strip() else " " for text in texts]
        try:
            response = await self._client.embeddings.create(
                model=self._model,
                input=sanitized,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("OpenAI embedding request failed")
            raise AppError(
                "Failed to generate embeddings",
                status_code=502,
                code="embedding_failed",
                details=str(exc),
            ) from exc

        ordered = sorted(response.data, key=lambda item: item.index)
        return [item.embedding for item in ordered]
