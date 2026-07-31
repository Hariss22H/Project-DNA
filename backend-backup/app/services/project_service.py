"""Project workspace CRUD service."""

from __future__ import annotations

from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.exceptions import AppError
from app.models.serializers import serialize_project
from app.schemas.project import ProjectStatus
from app.utils.ids import to_object_id
from app.utils.time import utc_now

PROJECTS_COLLECTION = "projects"


class ProjectService:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.collection = db[PROJECTS_COLLECTION]

    async def create_project(
        self,
        *,
        user_id: str,
        project_name: str,
        description: str = "",
    ) -> dict[str, Any]:
        now = utc_now()
        doc = {
            "user_id": user_id,
            "project_name": project_name.strip(),
            "description": (description or "").strip(),
            "github_repository": None,
            "project_status": ProjectStatus.CREATED.value,
            "created_at": now,
            "updated_at": now,
        }
        result = await self.collection.insert_one(doc)
        doc["_id"] = result.inserted_id

        from app.services.container import services
        from app.services.timeline.base import TimelineEvent

        await services.timeline.add_event(
            TimelineEvent(
                project_id=str(result.inserted_id),
                event_type="project_created",
                title="Project Created",
                description=doc["project_name"],
            )
        )
        return serialize_project(doc)

    async def list_projects(self, *, user_id: str) -> list[dict[str, Any]]:
        cursor = self.collection.find({"user_id": user_id}).sort("created_at", -1)
        return [serialize_project(doc) async for doc in cursor]

    async def get_project(self, *, user_id: str, project_id: str) -> dict[str, Any]:
        doc = await self._get_owned_doc(user_id=user_id, project_id=project_id)
        return serialize_project(doc)

    async def update_project(
        self,
        *,
        user_id: str,
        project_id: str,
        updates: dict[str, Any],
    ) -> dict[str, Any]:
        clean = {key: value for key, value in updates.items() if value is not None}
        if "project_name" in clean:
            clean["project_name"] = str(clean["project_name"]).strip()
            if not clean["project_name"]:
                raise AppError(
                    "Project name cannot be empty",
                    status_code=400,
                    code="invalid_project_name",
                )
        if "description" in clean:
            clean["description"] = str(clean["description"]).strip()
        if "github_repository" in clean:
            value = clean["github_repository"]
            clean["github_repository"] = value.strip() if isinstance(value, str) and value.strip() else None
        if "project_status" in clean:
            status = clean["project_status"]
            clean["project_status"] = status.value if isinstance(status, ProjectStatus) else str(status)

        if not clean:
            return await self.get_project(user_id=user_id, project_id=project_id)

        clean["updated_at"] = utc_now()
        oid = to_object_id(project_id, field_name="project_id")
        result = await self.collection.update_one(
            {"_id": oid, "user_id": user_id},
            {"$set": clean},
        )
        if result.matched_count == 0:
            raise AppError("Project not found", status_code=404, code="project_not_found")
        return await self.get_project(user_id=user_id, project_id=project_id)

    async def delete_project(self, *, user_id: str, project_id: str) -> None:
        oid = to_object_id(project_id, field_name="project_id")
        result = await self.collection.delete_one({"_id": oid, "user_id": user_id})
        if result.deleted_count == 0:
            raise AppError("Project not found", status_code=404, code="project_not_found")

        from app.services.document_service import DocumentService
        from app.services.indexing_service import IndexingService
        from app.services.knowledge_graph_service import KnowledgeGraphService
        from app.services.repository_service import RepositoryService

        db = self.collection.database
        await RepositoryService(db).delete_for_project(project_id)
        await DocumentService(db).delete_for_project(project_id)
        await IndexingService(db).delete_project_vectors(project_id)
        await KnowledgeGraphService(db).delete_for_project(project_id)

    async def _get_owned_doc(self, *, user_id: str, project_id: str) -> dict[str, Any]:
        oid = to_object_id(project_id, field_name="project_id")
        doc = await self.collection.find_one({"_id": oid, "user_id": user_id})
        if doc is None:
            raise AppError("Project not found", status_code=404, code="project_not_found")
        return doc
