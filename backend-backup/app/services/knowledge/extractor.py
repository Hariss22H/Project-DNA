"""Project entity extraction for knowledge graph (Member 3 can replace)."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Any, Optional

from app.services.knowledge.base import ProjectEntity


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
    """Heuristic extractor good enough for a hackathon React Flow demo."""

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
                    },
                )
            )

            for language, bytes_count in (repository.get("languages") or {}).items():
                add(
                    ProjectEntity(
                        id=f"tech:{project_id}:{_slug(language)}",
                        name=str(language),
                        entity_type="technology",
                        metadata={"bytes": bytes_count, "source": "github_languages"},
                    )
                )

            for topic in (repository.get("topics") or [])[:12]:
                add(
                    ProjectEntity(
                        id=f"feature:{project_id}:{_slug(topic)}",
                        name=str(topic),
                        entity_type="feature",
                        metadata={"source": "github_topics"},
                    )
                )

            modules = _top_level_modules(repository.get("structure") or [])
            for module in modules[:20]:
                add(
                    ProjectEntity(
                        id=f"module:{project_id}:{_slug(module)}",
                        name=module,
                        entity_type="module",
                        metadata={"path": module, "source": "repository_structure"},
                    )
                )

            for path in (repository.get("important_files") or [])[:25]:
                add(
                    ProjectEntity(
                        id=f"file:{project_id}:{_slug(path)}",
                        name=path,
                        entity_type="file",
                        metadata={"path": path, "source": "important_files"},
                    )
                )

            for path in (repository.get("structure") or []):
                lower = path.lower()
                if any(token in lower for token in ("/api/", "routes/", "endpoints/", "controllers/")):
                    add(
                        ProjectEntity(
                            id=f"api:{project_id}:{_slug(path)}",
                            name=path,
                            entity_type="api",
                            metadata={"path": path, "source": "structure_heuristic"},
                        )
                    )
                if len([e for e in entities if e.entity_type == "api"]) >= 12:
                    break

            if repository.get("readme_content"):
                add(
                    ProjectEntity(
                        id=f"doc:{project_id}:readme",
                        name="README.md",
                        entity_type="document",
                        metadata={"source": "readme"},
                    )
                )

        for doc in documents[:40]:
            file_name = doc.get("file_name") or "document"
            add(
                ProjectEntity(
                    id=f"doc:{project_id}:{doc.get('_id') or _slug(file_name)}",
                    name=file_name,
                    entity_type="document",
                    metadata={
                        "file_type": doc.get("file_type"),
                        "is_architecture": bool(doc.get("is_architecture")),
                        "source": "uploaded_document",
                    },
                )
            )
            # Lightweight tech hints from filenames.
            lower = file_name.lower()
            for tech in ("docker", "kubernetes", "fastapi", "react", "postgres", "mongo", "redis"):
                if tech in lower:
                    add(
                        ProjectEntity(
                            id=f"tech:{project_id}:{tech}",
                            name=tech.title() if tech != "fastapi" else "FastAPI",
                            entity_type="technology",
                            metadata={"source": "document_filename"},
                        )
                    )

        return entities


def _slug(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", (value or "").strip().lower()).strip("-")
    return cleaned[:80] or "item"


def _top_level_modules(structure: list[str]) -> list[str]:
    modules: list[str] = []
    seen: set[str] = set()
    for path in structure:
        part = path.split("/")[0].strip()
        if not part or "." in part:
            continue
        if part.lower() in {"node_modules", ".git", "dist", "build", "coverage", "__pycache__"}:
            continue
        if part in seen:
            continue
        seen.add(part)
        modules.append(part)
    return modules
