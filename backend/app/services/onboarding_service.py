"""AI Project Onboarding Assistant — reuses the shared RAG retrieval pipeline."""

from __future__ import annotations

import logging
import re
import time
from typing import Any, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.exceptions import AppError
from app.services.container import services
from app.services.project_service import ProjectService
from app.services.prompts.onboarding import (
    ONBOARDING_SECTION_ORDER,
    ONBOARDING_SYSTEM_PROMPT,
    build_onboarding_user_prompt,
)
from app.services.rag import RAGService
from app.services.timeline.base import TimelineEvent
from app.utils.time import utc_now

logger = logging.getLogger(__name__)

ONBOARDING_QUERIES = [
    "project purpose architecture overview technology stack",
    "authentication APIs modules backend frontend workflow",
    "deployment setup documentation risks onboarding",
]

SECTION_ICONS = {
    "Welcome": "sparkles",
    "Project Purpose": "target",
    "Architecture Overview": "layers",
    "Technology Stack": "cpu",
    "Major Modules": "boxes",
    "Important APIs": "route",
    "Project Workflow": "git-branch",
    "Important Documents": "file-text",
    "Current Project Risks": "shield-alert",
    "Suggested Learning Path": "map",
    "Estimated Onboarding Time": "clock",
    "First Tasks Recommendation": "list-checks",
}


class OnboardingService:
    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        *,
        rag: Optional[RAGService] = None,
    ) -> None:
        self.db = db
        self.projects = ProjectService(db)
        self.repositories = db["repositories"]
        self.documents = db["documents"]
        self.risks = db["ai_risks"]
        self.graphs = db["knowledge_graphs"]
        self.rag = rag or RAGService()

    async def generate_briefing(self, *, user_id: str, project_id: str) -> dict[str, Any]:
        started = time.perf_counter()
        project = await self.projects.get_project(user_id=user_id, project_id=project_id)
        project_name = project.get("project_name") or "Project"

        side_context = await self._collect_side_context(project_id=project_id, project=project)
        retrieval = await self._retrieve_merged_context(project_id)
        if retrieval["retrieved_count"] <= 0:
            raise AppError(
                "Not enough indexed project knowledge to generate an onboarding briefing. "
                "Connect sources and run indexing first.",
                status_code=400,
                code="insufficient_knowledge",
            )

        retrieved_context = "\n\n".join(retrieval["context_blocks"])
        user_prompt = build_onboarding_user_prompt(
            project_name=project_name,
            retrieved_context=retrieved_context,
            project_summary=side_context["summary_text"],
        )
        logger.info(
            "Onboarding briefing project_id=%s retrieved=%s prompt_chars=%s",
            project_id,
            retrieval["retrieved_count"],
            len(user_prompt),
        )

        llm_result = await services.llm_manager.generate(
            system_prompt=ONBOARDING_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )
        markdown = (llm_result.content or "").strip()
        if not markdown:
            markdown = self._fallback_briefing(project_name=project_name, side_context=side_context)

        sections = parse_briefing_sections(markdown)
        elapsed_ms = int((time.perf_counter() - started) * 1000)

        await services.timeline.add_event(
            TimelineEvent(
                project_id=project_id,
                event_type="onboarding_briefing_generated",
                title="Onboarding Briefing Generated",
                description=f"AI Project Onboarding Assistant created a briefing for {project_name}.",
                metadata={
                    "source": "AI",
                    "sections": len(sections),
                    "retrieved_count": retrieval["retrieved_count"],
                },
                created_at=utc_now(),
            )
        )

        return {
            "project_id": project_id,
            "project_name": project_name,
            "title": f"AI Onboarding Briefing — {project_name}",
            "markdown": markdown,
            "sections": sections,
            "sources": retrieval["sources"],
            "confidence": retrieval["confidence"],
            "model_used": llm_result.model_used,
            "fallback_used": llm_result.fallback_used,
            "retrieved_count": retrieval["retrieved_count"],
            "response_time_ms": elapsed_ms,
            "generated_at": utc_now(),
        }

    async def _retrieve_merged_context(self, project_id: str) -> dict[str, Any]:
        merged: dict[str, Any] = {
            "relevant": [],
            "context_blocks": [],
            "sources": [],
            "confidence": 0.0,
            "retrieved_count": 0,
        }
        seen_ids: set[str] = set()
        all_scores: list[float] = []

        for query in ONBOARDING_QUERIES:
            try:
                result = await self.rag.retrieve(project_id=project_id, question=query, top_k=6)
            except AppError:
                raise
            except Exception as exc:  # noqa: BLE001
                logger.warning("Onboarding retrieval query failed (%s): %s", query, exc)
                continue

            for item, block, source in zip(
                result["relevant"],
                result["context_blocks"],
                result["sources"],
            ):
                item_id = str(item.id)
                if item_id in seen_ids:
                    continue
                seen_ids.add(item_id)
                merged["relevant"].append(item)
                merged["context_blocks"].append(block)
                merged["sources"].append(source)
                all_scores.append(float(item.score))

        merged["retrieved_count"] = len(merged["sources"])
        if all_scores:
            merged["confidence"] = round(min(98.0, (sum(all_scores) / len(all_scores)) * 100), 1)
        return merged

    async def _collect_side_context(self, *, project_id: str, project: dict[str, Any]) -> dict[str, Any]:
        repo = await self.repositories.find_one({"project_id": project_id})
        docs = [doc async for doc in self.documents.find({"project_id": project_id}).limit(20)]
        risks = [doc async for doc in self.risks.find({"project_id": project_id}).sort("generated_at", -1).limit(8)]
        graph = await self.graphs.find_one({"project_id": project_id})
        timeline_events = await services.timeline.list_events(project_id, limit=8)

        languages = list(((repo or {}).get("languages") or {}).keys())
        doc_names = [str(doc.get("file_name") or "document") for doc in docs]
        if repo and (repo.get("readme_content") or "").strip():
            doc_names = ["README.md", *doc_names]
        for item in (repo or {}).get("documentation_files") or []:
            if item.get("path"):
                doc_names.append(str(item["path"]))

        graph_nodes = []
        if graph:
            payload = graph.get("payload") or graph
            nodes = payload.get("nodes") or []
            graph_nodes = [
                f"{node.get('label')} ({node.get('type')})"
                for node in nodes[:25]
                if node.get("label")
            ]

        risk_lines = [
            f"- ({risk.get('severity')}) {risk.get('title')}: {risk.get('description')}"
            for risk in risks
        ]
        timeline_lines = [
            f"- {event.title}: {event.description or ''}"
            for event in timeline_events
        ]

        summary_text = "\n".join(
            [
                f"Project name: {project.get('project_name')}",
                f"Project description: {project.get('description') or 'N/A'}",
                f"Repository: {(repo or {}).get('full_name') or 'not connected'}",
                f"Repo description: {(repo or {}).get('description') or 'N/A'}",
                f"Languages: {', '.join(languages) or 'N/A'}",
                f"Important files: {', '.join((repo or {}).get('important_files') or []) or 'N/A'}",
                f"Documents: {', '.join(dict.fromkeys(doc_names)) or 'N/A'}",
                f"Knowledge graph entities: {', '.join(graph_nodes) or 'N/A'}",
                "Timeline highlights:",
                *(timeline_lines or ["- None"]),
                "Current risks:",
                *(risk_lines or ["- None detected yet"]),
                "Canonical product workflow reminder:",
                "GitHub + Documents → Extraction → Chunking → Embeddings → Qdrant → RAG → Knowledge Twin → Dashboard",
            ]
        )
        return {
            "summary_text": summary_text,
            "documents": list(dict.fromkeys(doc_names)),
            "risks": risks,
            "languages": languages,
        }

    def _fallback_briefing(self, *, project_name: str, side_context: dict[str, Any]) -> str:
        docs = ", ".join(side_context.get("documents") or []) or "This information was not found in the indexed project knowledge."
        risks = side_context.get("risks") or []
        risk_text = "\n".join(
            f"- **{risk.get('title')}** ({risk.get('severity')}): {risk.get('description')}"
            for risk in risks
        ) or "This information was not found in the indexed project knowledge."
        stack = ", ".join(side_context.get("languages") or []) or "This information was not found in the indexed project knowledge."
        return (
            f"# Welcome\n\nWelcome to {project_name}. This briefing was generated from indexed project knowledge.\n\n"
            f"# Project Purpose\n\nThis information was not found in the indexed project knowledge.\n\n"
            f"# Architecture Overview\n\nThis information was not found in the indexed project knowledge.\n\n"
            f"# Technology Stack\n\n{stack}\n\n"
            f"# Major Modules\n\nThis information was not found in the indexed project knowledge.\n\n"
            f"# Important APIs\n\nThis information was not found in the indexed project knowledge.\n\n"
            "# Project Workflow\n\n"
            "GitHub + Documents → Extraction → Chunking → Embeddings → Qdrant → RAG → Knowledge Twin → Dashboard\n\n"
            f"# Important Documents\n\n{docs}\n\n"
            f"# Current Project Risks\n\n{risk_text}\n\n"
            "# Suggested Learning Path\n\n"
            "1. Read README\n2. Understand Architecture\n3. Explore Backend\n4. Explore Frontend\n"
            "5. Review APIs\n6. Understand AI Pipeline\n7. Review Risks\n\n"
            "# Estimated Onboarding Time\n\nApproximately 30–60 minutes, depending on documentation completeness.\n\n"
            "# First Tasks Recommendation\n\n"
            "- Improve documentation gaps\n- Review authentication flow\n- Explore dashboard APIs\n"
        )


def parse_briefing_sections(markdown: str) -> list[dict[str, str]]:
    """Split markdown briefing into ordered section cards."""
    text = (markdown or "").strip()
    if not text:
        return []

    # Normalize alternate heading styles to H1 markers.
    normalized = re.sub(r"^##\s+", "# ", text, flags=re.MULTILINE)
    parts = re.split(r"(?m)^#\s+", normalized)
    found: dict[str, str] = {}
    for part in parts:
        chunk = part.strip()
        if not chunk:
            continue
        lines = chunk.splitlines()
        title = lines[0].strip().strip("#").strip()
        body = "\n".join(lines[1:]).strip()
        if not title:
            continue
        found[title.lower()] = body or "This information was not found in the indexed project knowledge."

    sections: list[dict[str, str]] = []
    for title in ONBOARDING_SECTION_ORDER:
        body = found.get(title.lower())
        if body is None:
            # Fuzzy match close titles from the model.
            body = next(
                (
                    content
                    for key, content in found.items()
                    if title.lower() in key or key in title.lower()
                ),
                "This information was not found in the indexed project knowledge.",
            )
        sections.append(
            {
                "title": title,
                "content": body,
                "icon": SECTION_ICONS.get(title, "sparkles"),
            }
        )

    # Include any unexpected extra sections from the model.
    known = {title.lower() for title in ONBOARDING_SECTION_ORDER}
    for key, content in found.items():
        if key in known:
            continue
        pretty = key.title()
        sections.append({"title": pretty, "content": content, "icon": "sparkles"})
    return sections
