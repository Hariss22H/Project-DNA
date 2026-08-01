"""GitHub repository orchestration — API-facing, uses pluggable GitHubService."""

from __future__ import annotations

from typing import Any, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.exceptions import AppError
from app.models.serializers import serialize_repository
from app.schemas.project import ProjectStatus
from app.services.container import services
from app.services.github import GitHubService
from app.services.project_service import ProjectService
from app.services.timeline.base import TimelineEvent
from app.utils.ids import to_object_id
from app.utils.time import utc_now

REPOSITORIES_COLLECTION = "repositories"


class RepositoryService:
    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        *,
        github_service: Optional[GitHubService] = None,
    ) -> None:
        self.db = db
        self.collection = db[REPOSITORIES_COLLECTION]
        self.projects = ProjectService(db)
        self.github = github_service or services.github

    async def connect_repository(
        self,
        *,
        user_id: str,
        project_id: str,
        repository_url: str,
    ) -> dict[str, Any]:
        await self.projects.get_project(user_id=user_id, project_id=project_id)

        if not await self.github.validate_repository(repository_url):
            raise AppError(
                "Invalid or unreachable public GitHub repository URL",
                status_code=400,
                code="invalid_github_url",
            )

        fetched = await self.github.fetch_repository(repository_url)
        now = utc_now()
        payload = {
            "project_id": project_id,
            "user_id": user_id,
            "repository_url": fetched.repository_url,
            "owner": fetched.owner,
            "name": fetched.name,
            "full_name": fetched.full_name,
            "description": fetched.description,
            "default_branch": fetched.default_branch,
            "readme_content": fetched.readme_content,
            "structure": fetched.structure,
            "important_files": fetched.important_files,
            "documentation_files": fetched.documentation_files,
            "languages": fetched.languages,
            "topics": fetched.topics,
            "commit_summary": [item.model_dump() for item in fetched.commit_summary],
            "stars": fetched.stars,
            "forks": fetched.forks,
            "raw": fetched.raw,
            "last_synced": now,
            "updated_at": now,
        }

        existing = await self.collection.find_one({"project_id": project_id})
        if existing:
            await self.collection.update_one({"_id": existing["_id"]}, {"$set": payload})
            payload["_id"] = existing["_id"]
            payload["created_at"] = existing["created_at"]
        else:
            payload["created_at"] = now
            result = await self.collection.insert_one(payload)
            payload["_id"] = result.inserted_id

        await self.projects.update_project(
            user_id=user_id,
            project_id=project_id,
            updates={
                "github_repository": fetched.repository_url,
                "project_status": ProjectStatus.CREATED,
            },
        )

        await services.timeline.add_event(
            TimelineEvent(
                project_id=project_id,
                event_type="repository_connected",
                title="Repository Connected",
                description=f"Connected {fetched.full_name}",
                metadata={"repository_url": fetched.repository_url},
            )
        )
        if fetched.readme_content:
            await services.timeline.add_event(
                TimelineEvent(
                    project_id=project_id,
                    event_type="readme_indexed",
                    title="README Indexed",
                    description=f"README extracted from {fetched.full_name}",
                    metadata={"chars": len(fetched.readme_content)},
                )
            )

        return serialize_repository(payload)

    async def get_repository(self, *, user_id: str, project_id: str) -> dict[str, Any]:
        await self.projects.get_project(user_id=user_id, project_id=project_id)
        doc = await self.collection.find_one({"project_id": project_id})
        if doc is None:
            raise AppError(
                "No GitHub repository connected to this project",
                status_code=404,
                code="repository_not_found",
            )
        return serialize_repository(doc)

    async def delete_for_project(self, project_id: str) -> None:
        await self.collection.delete_many({"project_id": project_id})
