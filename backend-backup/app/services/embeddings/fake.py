"""Deterministic fake embeddings for tests (no OpenAI calls)."""

from __future__ import annotations

import hashlib

from app.services.embeddings.base import EmbeddingService


class FakeEmbeddingService(EmbeddingService):
    def __init__(self, *, dimensions: int = 1536, model_name: str = "fake-embedding") -> None:
        self._dimensions = dimensions
        self._model_name = model_name

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimensions(self) -> int:
        return self._dimensions

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            digest = hashlib.sha256(text.encode("utf-8")).digest()
            values: list[float] = []
            while len(values) < self._dimensions:
                for byte in digest:
                    values.append((byte / 255.0) * 2 - 1)
                    if len(values) >= self._dimensions:
                        break
                digest = hashlib.sha256(digest).digest()
            # L2 normalize lightly for cosine-friendly comparisons.
            norm = sum(v * v for v in values) ** 0.5 or 1.0
            vectors.append([v / norm for v in values])
        return vectors
