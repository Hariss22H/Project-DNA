"""Dashboard aggregation for heuristic project intelligence metrics."""

from __future__ import annotations

from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.services.container import services
from app.services.knowledge_graph_service import KnowledgeGraphService
from app.services.project_service import ProjectService
from app.services.risk_engine import RiskEngine


class DashboardService:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.db = db
        self.projects = ProjectService(db)
        self.repositories = db["repositories"]
        self.documents = db["documents"]
        self.index_meta = db["index_meta"]
        self.conversations = db["ai_conversations"]
        self.risks = RiskEngine(db, use_llm_summary=False)

    async def get_dashboard(self, *, user_id: str, project_id: str) -> dict[str, Any]:
        project = await self.projects.get_project(user_id=user_id, project_id=project_id)
        repo = await self.repositories.find_one({"project_id": project_id})
        docs = [doc async for doc in self.documents.find({"project_id": project_id}).sort("created_at", -1)]
        meta = await self.index_meta.find_one({"project_id": project_id})
        risks = await self.risks.list_risks(user_id=user_id, project_id=project_id)
        if not risks:
            # Generate a first-pass risk set for demo/dashboard readiness.
            risks = await RiskEngine(self.db, use_llm_summary=False).analyze_project(
                user_id=user_id,
                project_id=project_id,
            )
        timeline = await services.timeline.list_events(project_id)
        recent_chats = [
            {
                "conversation_id": str(doc["_id"]),
                "question": doc.get("user_question"),
                "answer": (doc.get("ai_response") or "")[:220],
                "confidence": float(doc.get("confidence_score") or 0),
                "created_at": doc.get("created_at"),
            }
            async for doc in self.conversations.find({"project_id": project_id})
            .sort("created_at", -1)
            .limit(5)
        ]

        from app.services.knowledge.documentation import combine_knowledge_text, has_topic

        has_readme = bool(repo and (repo.get("readme_content") or "").strip())
        knowledge_text = combine_knowledge_text(repo=repo, docs=docs)
        architecture_count = sum(
            1
            for doc in docs
            if doc.get("is_architecture") or "architecture" in (doc.get("file_name") or "").lower()
        )
        # Content-aware: README/spec that explain architecture count as architecture knowledge.
        if architecture_count == 0 and has_topic(knowledge_text, "architecture"):
            architecture_count = 1
        docs_count = len(docs) + len((repo or {}).get("documentation_files") or [])
        chunks_indexed = int((meta or {}).get("chunks_indexed") or 0)
        if chunks_indexed == 0:
            chunks_indexed = await services.vector_store.count_by_project(project_id)

        knowledge_coverage = _knowledge_coverage(
            has_readme=has_readme,
            docs_count=docs_count,
            architecture_count=architecture_count,
            chunks_indexed=chunks_indexed,
            github_connected=repo is not None,
        )
        health_score = _health_score(knowledge_coverage, risks)
        ai_confidence = await self._avg_confidence(project_id)

        connected_sources = []
        if repo is not None:
            connected_sources.append(
                {"type": "github", "label": repo.get("full_name") or repo.get("repository_url")}
            )
        if has_readme:
            connected_sources.append({"type": "readme", "label": "README.md"})
        if architecture_count:
            connected_sources.append(
                {"type": "architecture", "label": f"{architecture_count} architecture file(s)"}
            )
        if docs_count:
            connected_sources.append({"type": "documents", "label": f"{docs_count} document(s)"})

        insights = _build_insights(
            project_name=project["project_name"],
            knowledge_coverage=knowledge_coverage,
            risks=risks,
            chunks_indexed=chunks_indexed,
            docs_count=docs_count,
        )

        return {
            "project_id": project_id,
            "project_name": project["project_name"],
            "project_status": project["project_status"],
            "health_score": health_score,
            "health_label": _health_label(health_score),
            "knowledge_coverage": knowledge_coverage,
            "ai_confidence": ai_confidence,
            "connected_sources": connected_sources,
            "connected_sources_count": len(connected_sources),
            "indexed_documents_count": docs_count,
            "chunks_indexed": chunks_indexed,
            "github_connected": repo is not None,
            "has_readme": has_readme,
            "risks": risks[:10],
            "risk_count": len(risks),
            "high_risk_count": sum(1 for risk in risks if risk.get("severity") == "high"),
            "timeline": [
                {
                    "id": event.id,
                    "event_type": event.event_type,
                    "title": event.title,
                    "description": event.description,
                    "created_at": event.created_at,
                }
                for event in timeline[:15]
            ],
            "recent_documents": [
                {
                    "id": str(doc["_id"]),
                    "file_name": doc.get("file_name"),
                    "file_type": doc.get("file_type"),
                    "upload_time": doc.get("upload_time") or doc.get("created_at"),
                }
                for doc in docs[:5]
            ],
            "recent_conversations": recent_chats,
            "ai_insights": insights,
            "knowledge_graph_preview": await self._graph_preview(
                user_id=user_id,
                project_id=project_id,
            ),
        }

    async def _graph_preview(self, *, user_id: str, project_id: str) -> dict[str, Any]:
        try:
            graph = await KnowledgeGraphService(self.db).get_graph(
                user_id=user_id,
                project_id=project_id,
                refresh=False,
            )
            return {
                "nodes": (graph.get("nodes") or [])[:25],
                "edges": (graph.get("edges") or [])[:40],
                "entity_count": graph.get("entity_count") or 0,
            }
        except Exception:  # noqa: BLE001 — dashboard should still load
            return {"nodes": [], "edges": [], "entity_count": 0}

    async def _avg_confidence(self, project_id: str) -> float:
        scores: list[float] = []
        cursor = self.conversations.find({"project_id": project_id}).sort("created_at", -1).limit(20)
        async for doc in cursor:
            scores.append(float(doc.get("confidence_score") or 0))
        if not scores:
            return 0.0
        return round(sum(scores) / len(scores), 1)


def _knowledge_coverage(
    *,
    has_readme: bool,
    docs_count: int,
    architecture_count: int,
    chunks_indexed: int,
    github_connected: bool,
) -> float:
    score = 0.0
    if github_connected:
        score += 20
    if has_readme:
        score += 20
    if architecture_count:
        score += 20
    score += min(docs_count * 8, 24)
    if chunks_indexed > 0:
        score += 16
    return round(min(score, 100.0), 1)


def _health_score(knowledge_coverage: float, risks: list[dict[str, Any]]) -> float:
    penalty = 0.0
    for risk in risks:
        severity = risk.get("severity")
        if severity == "high":
            penalty += 12
        elif severity == "medium":
            penalty += 7
        else:
            penalty += 3
    score = knowledge_coverage - min(penalty, 45)
    return round(max(score, 5.0), 1)


def _health_label(score: float) -> str:
    if score >= 85:
        return "Excellent"
    if score >= 70:
        return "Good"
    if score >= 50:
        return "Fair"
    return "Needs attention"


def _build_insights(
    *,
    project_name: str,
    knowledge_coverage: float,
    risks: list[dict[str, Any]],
    chunks_indexed: int,
    docs_count: int,
) -> list[dict[str, str]]:
    insights: list[dict[str, str]] = []
    insights.append(
        {
            "title": "Knowledge coverage",
            "detail": f"{project_name} knowledge coverage is at {knowledge_coverage}%.",
        }
    )
    if chunks_indexed > 0:
        insights.append(
            {
                "title": "AI retrieval ready",
                "detail": f"{chunks_indexed} chunks are indexed for grounded AI answers.",
            }
        )
    else:
        insights.append(
            {
                "title": "Indexing recommended",
                "detail": "Run indexing to enable the AI Knowledge Twin.",
            }
        )
    if risks:
        top = risks[0]
        insights.append(
            {
                "title": "Top risk",
                "detail": f"{top['title']}: {top.get('recommendation') or top.get('description')}",
            }
        )
    elif docs_count:
        insights.append(
            {
                "title": "Documentation momentum",
                "detail": f"{docs_count} document(s) are available with no open generated risks.",
            }
        )
    return insights[:5]
