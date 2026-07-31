"""Shared FastAPI dependencies."""

from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import Settings, get_settings
from app.database.mongodb import get_database
from app.services.container import ServiceContainer, services
from app.services.embeddings import EmbeddingService
from app.services.github import GitHubService
from app.services.ingestion import DocumentExtractor
from app.services.knowledge import KnowledgeGraphBuilder
from app.services.knowledge.extractor import EntityExtractor
from app.services.timeline import TimelineService
from app.services.vectorstore import VectorStore


def get_app_settings() -> Settings:
    return get_settings()


async def get_db() -> AsyncIOMotorDatabase:
    return await get_database()


def get_services() -> ServiceContainer:
    return services


def get_github_service() -> GitHubService:
    return services.github


def get_document_extractor() -> DocumentExtractor:
    return services.document_extractor


def get_knowledge_graph_builder() -> KnowledgeGraphBuilder:
    return services.knowledge_graph


def get_entity_extractor() -> EntityExtractor:
    return services.entity_extractor


def get_timeline_service() -> TimelineService:
    return services.timeline


def get_embedding_service() -> EmbeddingService:
    return services.embeddings


def get_vector_store() -> VectorStore:
    return services.vector_store
