"""Vector database services."""

from app.services.vectorstore.base import VectorPoint, VectorSearchResult, VectorStore
from app.services.vectorstore.memory import InMemoryVectorStore
from app.services.vectorstore.qdrant_store import QdrantVectorStore

__all__ = [
    "VectorPoint",
    "VectorSearchResult",
    "VectorStore",
    "InMemoryVectorStore",
    "QdrantVectorStore",
]


def build_default_vector_store() -> VectorStore:
    """Prefer Qdrant Cloud; fall back to in-memory when URL is unset (local/dev)."""
    from app.core.config import get_settings

    settings = get_settings()
    if settings.qdrant_url:
        return QdrantVectorStore()
    return InMemoryVectorStore()
