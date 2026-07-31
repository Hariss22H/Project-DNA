"""Knowledge graph orchestration — extract entities, build JSON, cache in MongoDB."""

from __future__ import annotations

from typing import Any, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.services.container import services
from app.services.knowledge import KnowledgeGraphBuilder, KnowledgeGraphData
from app.services.knowledge.extractor import DefaultEntityExtractor, EntityExtractor
from app.services.project_service import ProjectService
from app.services.timeline.base import TimelineEvent
from app.utils.time import utc_now

GRAPH_COLLECTION = "knowledge_graphs"


class KnowledgeGraphService:
    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        *,
        extractor: Optional[EntityExtractor] = None,
        builder: Optional[KnowledgeGraphBuilder] = None,
    ) -> None:
        self.db = db
        self.collection = db[GRAPH_COLLECTION]
        self.projects = ProjectService(db)
        self.repositories = db["repositories"]
        self.documents = db["documents"]
        self.extractor = extractor or services.entity_extractor
        self.builder = builder or services.knowledge_graph

    async def get_graph(
        self,
        *,
        user_id: str,
        project_id: str,
        refresh: bool = False,
    ) -> dict[str, Any]:
        project = await self.projects.get_project(user_id=user_id, project_id=project_id)
        if not refresh:
            cached = await self.collection.find_one({"project_id": project_id})
            if cached and cached.get("graph"):
                return {
                    "project_id": project_id,
                    "nodes": cached["graph"].get("nodes") or [],
                    "edges": cached["graph"].get("edges") or [],
                    "entity_count": cached.get("entity_count") or 0,
                    "generated_at": cached.get("generated_at"),
                    "cached": True,
                }

        return await self.build_and_store(user_id=user_id, project_id=project_id, project_name=project["project_name"])

    async def build_and_store(
        self,
        *,
        user_id: str,
        project_id: str,
        project_name: Optional[str] = None,
    ) -> dict[str, Any]:
        if not project_name:
            project = await self.projects.get_project(user_id=user_id, project_id=project_id)
            project_name = project["project_name"]

        repo = await self.repositories.find_one({"project_id": project_id})
        documents = [doc async for doc in self.documents.find({"project_id": project_id})]

        entities = await self.extractor.extract(
            project_id=project_id,
            project_name=project_name or "Project",
            repository=repo,
            documents=documents,
        )
        graph: KnowledgeGraphData = await self.builder.build_graph(
            project_id=project_id,
            entities=entities,
        )
        payload = graph.model_dump()
        now = utc_now()
        record = {
            "project_id": project_id,
            "user_id": user_id,
            "graph": payload,
            "entity_count": len(entities),
            "generated_at": now,
            "updated_at": now,
        }
        existing = await self.collection.find_one({"project_id": project_id})
        if existing:
            await self.collection.update_one({"_id": existing["_id"]}, {"$set": record})
        else:
            record["created_at"] = now
            await self.collection.insert_one(record)

        await services.timeline.add_event(
            TimelineEvent(
                project_id=project_id,
                event_type="knowledge_graph_generated",
                title="Knowledge Graph Generated",
                description=f"Built graph with {len(payload.get('nodes', []))} nodes",
                metadata={
                    "nodes": len(payload.get("nodes", [])),
                    "edges": len(payload.get("edges", [])),
                    "entities": len(entities),
                },
            )
        )

        return {
            "project_id": project_id,
            "nodes": payload.get("nodes") or [],
            "edges": payload.get("edges") or [],
            "entity_count": len(entities),
            "generated_at": now,
            "cached": False,
        }

    async def delete_for_project(self, project_id: str) -> None:
        await self.collection.delete_many({"project_id": project_id})
