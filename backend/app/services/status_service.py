"""Project ingestion status for dashboard / frontend polling."""

from __future__ import annotations

from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.project import ProjectStatus
from app.services.container import services
from app.services.document_service import DocumentService
from app.services.project_service import ProjectService


class StatusService:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.db = db
        self.projects = ProjectService(db)
        self.documents = DocumentService(db)
        self.repositories = db["repositories"]
        self.index_meta = db["index_meta"]

    async def get_status(self, *, user_id: str, project_id: str) -> dict[str, Any]:
        project = await self.projects.get_project(user_id=user_id, project_id=project_id)
        repo = await self.repositories.find_one({"project_id": project_id})
        docs_count = await self.documents.count_documents(project_id)
        has_readme = bool(repo and repo.get("readme_content"))
        github_connected = repo is not None
        ready_for_indexing = github_connected or docs_count > 0
        meta = await self.index_meta.find_one({"project_id": project_id})
        chunks_indexed = int((meta or {}).get("chunks_indexed") or 0)
        if chunks_indexed == 0:
            chunks_indexed = await services.vector_store.count_by_project(project_id)
        is_indexed = chunks_indexed > 0 or project["project_status"] == ProjectStatus.READY.value

        if project["project_status"] == ProjectStatus.INDEXING.value:
            message = "Indexing knowledge into the vector database..."
        elif is_indexed:
            message = "Knowledge base is indexed and ready for AI chat."
        elif ready_for_indexing:
            message = "Sources connected. Call POST /index to build the knowledge base."
        else:
            message = "Connect a GitHub repository or upload documents to continue."

        return {
            "project_id": project_id,
            "project_status": project["project_status"],
            "github_connected": github_connected,
            "documents_count": docs_count,
            "has_readme": has_readme,
            "ready_for_indexing": ready_for_indexing,
            "is_indexed": is_indexed,
            "chunks_indexed": chunks_indexed,
            "message": message,
        }
