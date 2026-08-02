"""Service container — single place to swap Member 3 / infra implementations."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.services.embeddings import EmbeddingService, OpenAIEmbeddingService
from app.services.github import GitHubService, HttpGitHubService
from app.services.ingestion import CompositeDocumentExtractor, DocumentExtractor
from app.services.knowledge import (
    DefaultKnowledgeGraphBuilder,
    KnowledgeGraphBuilder,
)
from app.services.knowledge.extractor import DefaultEntityExtractor, EntityExtractor
from app.services.llm import LLMFallbackManager
from app.services.timeline import MongoTimelineService, TimelineService
from app.services.vectorstore import VectorStore, build_default_vector_store


@dataclass
class ServiceContainer:
    """Holds pluggable service implementations for the app lifetime."""

    github: GitHubService = field(default_factory=HttpGitHubService)
    document_extractor: DocumentExtractor = field(default_factory=CompositeDocumentExtractor)
    knowledge_graph: KnowledgeGraphBuilder = field(default_factory=DefaultKnowledgeGraphBuilder)
    entity_extractor: EntityExtractor = field(default_factory=DefaultEntityExtractor)
    timeline: TimelineService = field(default_factory=MongoTimelineService)
    embeddings: EmbeddingService = field(default_factory=OpenAIEmbeddingService)
    vector_store: VectorStore = field(default_factory=build_default_vector_store)
    llm_manager: LLMFallbackManager = field(default_factory=LLMFallbackManager)

    def set_github_service(self, service: GitHubService) -> None:
        self.github = service

    def set_document_extractor(self, service: DocumentExtractor) -> None:
        self.document_extractor = service

    def set_knowledge_graph_builder(self, service: KnowledgeGraphBuilder) -> None:
        self.knowledge_graph = service

    def set_entity_extractor(self, service: EntityExtractor) -> None:
        self.entity_extractor = service

    def set_timeline_service(self, service: TimelineService) -> None:
        self.timeline = service

    def set_embeddings(self, service: EmbeddingService) -> None:
        self.embeddings = service

    def set_vector_store(self, service: VectorStore) -> None:
        self.vector_store = service

    def set_llm_manager(self, service: LLMFallbackManager) -> None:
        self.llm_manager = service


services = ServiceContainer()
