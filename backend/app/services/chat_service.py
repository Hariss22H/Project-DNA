"""Chat orchestration and conversation persistence."""

from __future__ import annotations

from typing import Any, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.services.project_service import ProjectService
from app.services.rag import RAGService
from app.utils.ids import oid_str
from app.utils.time import utc_now

CONVERSATIONS_COLLECTION = "ai_conversations"


class ChatService:
    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        *,
        rag_service: Optional[RAGService] = None,
    ) -> None:
        self.db = db
        self.collection = db[CONVERSATIONS_COLLECTION]
        self.projects = ProjectService(db)
        self.rag = rag_service or RAGService()

    async def ask(
        self,
        *,
        user_id: str,
        project_id: str,
        question: str,
    ) -> dict[str, Any]:
        await self.projects.get_project(user_id=user_id, project_id=project_id)
        result = await self.rag.ask(project_id=project_id, question=question)

        now = utc_now()
        doc = {
            "project_id": project_id,
            "user_id": user_id,
            "user_question": question.strip(),
            "ai_response": result["answer"],
            "confidence_score": result["confidence"],
            "sources": result["sources"],
            "model_used": result["model_used"],
            "fallback_used": result["fallback_used"],
            "response_time_ms": result["response_time_ms"],
            "retrieved_count": result["retrieved_count"],
            "created_at": now,
        }
        insert = await self.collection.insert_one(doc)
        result["conversation_id"] = oid_str(insert.inserted_id)
        result["project_id"] = project_id
        result["question"] = question.strip()
        result["created_at"] = now
        return result

    async def list_conversations(
        self,
        *,
        user_id: str,
        project_id: str,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        await self.projects.get_project(user_id=user_id, project_id=project_id)
        cursor = (
            self.collection.find({"project_id": project_id, "user_id": user_id})
            .sort("created_at", -1)
            .limit(max(1, min(limit, 100)))
        )
        items: list[dict[str, Any]] = []
        async for doc in cursor:
            items.append(
                {
                    "conversation_id": oid_str(doc["_id"]),
                    "project_id": doc["project_id"],
                    "question": doc.get("user_question") or "",
                    "answer": doc.get("ai_response") or "",
                    "confidence": float(doc.get("confidence_score") or 0),
                    "sources": doc.get("sources") or [],
                    "model_used": doc.get("model_used") or "none",
                    "fallback_used": bool(doc.get("fallback_used")),
                    "response_time_ms": int(doc.get("response_time_ms") or 0),
                    "created_at": doc["created_at"],
                }
            )
        return items
