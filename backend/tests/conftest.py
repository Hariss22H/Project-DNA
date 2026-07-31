"""Shared pytest fixtures for Phase 0+."""

from __future__ import annotations

import os
from typing import AsyncIterator, Optional

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from mongomock_motor import AsyncMongoMockClient

# Ensure settings are predictable before app import.
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("MONGODB_URI", "mongodb://localhost:27017")
os.environ.setdefault("MONGODB_DB_NAME", "project_dna_test")
os.environ.setdefault("JWT_SECRET", "test-secret-key")
os.environ.setdefault("QDRANT_URL", "")
os.environ.setdefault("OPENAI_API_KEY", "")
os.environ.setdefault("RAG_MIN_SCORE", "-1.0")
os.environ.setdefault("RAG_TOP_K", "5")

from app.core.config import Settings, get_settings
from app.database.indexes import ensure_indexes
from app.database.mongodb import mongodb
from app.main import create_app
from app.services.container import services
from app.services.embeddings import FakeEmbeddingService
from app.services.github import StubGitHubService
from app.services.ingestion import StubDocumentExtractor
from app.services.knowledge import DefaultKnowledgeGraphBuilder, DefaultEntityExtractor
from app.services.llm import build_fake_llm_manager
from app.services.timeline import MongoTimelineService
from app.services.vectorstore import InMemoryVectorStore


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def _reset_services():
    """Keep pluggable services deterministic across tests."""
    services.set_github_service(StubGitHubService())
    services.set_document_extractor(StubDocumentExtractor())
    services.set_knowledge_graph_builder(DefaultKnowledgeGraphBuilder())
    services.set_entity_extractor(DefaultEntityExtractor())
    services.set_timeline_service(MongoTimelineService())
    services.set_embeddings(FakeEmbeddingService(dimensions=32))
    services.set_vector_store(InMemoryVectorStore())
    services.set_llm_manager(build_fake_llm_manager())
    yield


@pytest_asyncio.fixture
async def app_client(monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[AsyncClient]:
    """ASGI test client with an in-memory MongoDB mock (no live Atlas needed)."""

    async def mock_connect(settings: Optional[Settings] = None) -> None:
        settings = settings or get_settings()
        client = AsyncMongoMockClient()
        mongodb.client = client
        mongodb.db = client[settings.mongodb_db_name]

    async def mock_ping() -> bool:
        return mongodb.client is not None

    monkeypatch.setattr(mongodb, "connect", mock_connect)
    monkeypatch.setattr(mongodb, "ping", mock_ping)

    # Initialize DB before requests (do not rely solely on ASGI lifespan).
    await mock_connect()
    await ensure_indexes(mongodb.get_db())
    services.set_timeline_service(MongoTimelineService(mongodb.get_db()))

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    await mongodb.disconnect()
