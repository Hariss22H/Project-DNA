"""Embedding service contract — OpenAI text-embedding-3-small only for MVP."""

from __future__ import annotations

from abc import ABC, abstractmethod


class EmbeddingService(ABC):
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Embedding model identifier."""

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Vector dimensionality."""

    @abstractmethod
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for one or more texts."""

    async def embed_query(self, text: str) -> list[float]:
        vectors = await self.embed_texts([text])
        return vectors[0]
