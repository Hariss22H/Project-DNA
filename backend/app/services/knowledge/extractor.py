"""Semantic entity extraction for the AI Knowledge Graph."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

from app.services.knowledge.base import ProjectEntity
from app.services.knowledge.semantics import (
    FEATURES,
    MODULES,
    TECHNOLOGIES,
    find_matches,
    slug,
    structure_signals,
)


class EntityExtractor(ABC):
    @abstractmethod
    async def extract(
        self,
        *,
        project_id: str,
        project_name: str,
        repository: Optional[dict[str, Any]],
        documents: list[dict[str, Any]],
    ) -> list[ProjectEntity]:
        """Extract graph entities from repository + documents."""


class DefaultEntityExtractor(EntityExtractor):
    """Extract meaningful project concepts, not just folder names."""

    async def extract(
        self,
        *,
        project_id: str,
        project_name: str,
        repository: Optional[dict[str, Any]],
        documents: list[dict[str, Any]],
    ) -> list[ProjectEntity]:
        entities: list[ProjectEntity] = []
        seen: set[str] = set()

        def add(entity: ProjectEntity) -> None:
            if entity.id in seen:
                return
            seen.add(entity.id)
            entities.append(entity)

        corpus = _build_corpus(repository, documents)
        signals = structure_signals((repository or {}).get("structure") or [])

        add(
            ProjectEntity(
                id=f"project:{project_id}",
                name=project_name or "Project",
                entity_type="repository",
                metadata={"project_id": project_id, "kind": "project_root"},
            )
        )

        if repository:
            full_name = repository.get("full_name") or repository.get("name") or "repository"
            add(
                ProjectEntity(
                    id=f"repo:{project_id}",
                    name=str(full_name),
                    entity_type="repository",
                    metadata={
                        "url": repository.get("repository_url"),
                        "default_branch": repository.get("default_branch"),
                        "description": repository.get("description"),
                    },
                )
            )

        # Semantic modules / features / technologies from docs + structure.
        for name in find_matches(corpus, MODULES):
            add(
                ProjectEntity(
                    id=f"module:{project_id}:{slug(name)}",
                    name=name,
                    entity_type="module",
                    metadata={"source": "semantic_extraction"},
                )
            )
        for name in find_matches(corpus, FEATURES):
            add(
                ProjectEntity(
                    id=f"feature:{project_id}:{slug(name)}",
                    name=name,
                    entity_type="feature",
                    metadata={"source": "semantic_extraction"},
                )
            )
        for name in find_matches(corpus, TECHNOLOGIES):
            add(
                ProjectEntity(
                    id=f"tech:{project_id}:{slug(name)}",
                    name=name,
                    entity_type="technology",
                    metadata={"source": "semantic_extraction"},
                )
            )

        # Language stats from GitHub still useful.
        for language, bytes_count in ((repository or {}).get("languages") or {}).items():
            add(
                ProjectEntity(
                    id=f"tech:{project_id}:{slug(str(language))}",
                    name=str(language),
                    entity_type="technology",
                    metadata={"bytes": bytes_count, "source": "github_languages"},
                )
            )

        # Ensure core architecture nodes exist when structure implies them.
        if signals["has_backend"]:
            add(
                ProjectEntity(
                    id=f"module:{project_id}:backend",
                    name="Backend",
                    entity_type="module",
                    metadata={"source": "repository_structure"},
                )
            )
        if signals["has_frontend"]:
            add(
                ProjectEntity(
                    id=f"module:{project_id}:frontend",
                    name="Frontend",
                    entity_type="module",
                    metadata={"source": "repository_structure"},
                )
            )
        if signals["has_auth_code"]:
            add(
                ProjectEntity(
                    id=f"module:{project_id}:authentication",
                    name="Authentication",
                    entity_type="module",
                    metadata={"source": "repository_structure", "paths": signals["auth_paths"][:5]},
                )
            )
        if signals["api_paths"]:
            add(
                ProjectEntity(
                    id=f"api:{project_id}:rest-api",
                    name="REST API",
                    entity_type="api",
                    metadata={"paths": signals["api_paths"][:8], "source": "structure_heuristic"},
                )
            )

        if repository and (repository.get("readme_content") or "").strip():
            add(
                ProjectEntity(
                    id=f"doc:{project_id}:readme",
                    name="README.md",
                    entity_type="document",
                    metadata={"source": "readme", "role": "project_overview"},
                )
            )

        for item in ((repository or {}).get("documentation_files") or [])[:20]:
            path = item.get("path") or "document"
            add(
                ProjectEntity(
                    id=f"doc:{project_id}:repo:{slug(path)}",
                    name=str(path).split("/")[-1],
                    entity_type="document",
                    metadata={"path": path, "source": "repository_documentation"},
                )
            )

        for doc in documents[:40]:
            file_name = doc.get("file_name") or "document"
            add(
                ProjectEntity(
                    id=f"doc:{project_id}:{doc.get('_id') or slug(file_name)}",
                    name=file_name,
                    entity_type="document",
                    metadata={
                        "file_type": doc.get("file_type"),
                        "source": "uploaded_document",
                    },
                )
            )

        return entities


def _build_corpus(repository: Optional[dict[str, Any]], documents: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    if repository:
        parts.append(str(repository.get("description") or ""))
        parts.append(str(repository.get("readme_content") or ""))
        parts.append(" ".join(repository.get("topics") or []))
        parts.append(" ".join((repository.get("languages") or {}).keys()))
        parts.append(" ".join(repository.get("important_files") or []))
        parts.append(" ".join((repository.get("structure") or [])[:120]))
        for item in repository.get("documentation_files") or []:
            parts.append(str(item.get("path") or ""))
            parts.append(str(item.get("content") or "")[:4000])
    for doc in documents:
        parts.append(str(doc.get("file_name") or ""))
        parts.append(str(doc.get("extracted_text") or "")[:4000])
    return "\n".join(parts)
