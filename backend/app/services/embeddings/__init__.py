"""Embedding generation services (OpenAI only for MVP)."""

from app.services.embeddings.base import EmbeddingService
from app.services.embeddings.fake import FakeEmbeddingService
from app.services.embeddings.openai_embeddings import OpenAIEmbeddingService

__all__ = ["EmbeddingService", "FakeEmbeddingService", "OpenAIEmbeddingService"]
