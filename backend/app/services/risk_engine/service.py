"""Context-aware risk detection with optional LLM summarization."""

from __future__ import annotations

import logging
from typing import Any, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.services.container import services
from app.services.knowledge.documentation import (
    combine_knowledge_text,
    has_topic,
    source_inventory,
)
from app.services.llm.fallback import LLMFallbackManager
from app.services.project_service import ProjectService
from app.services.timeline.base import TimelineEvent
from app.utils.ids import oid_str
from app.utils.time import utc_now

logger = logging.getLogger(__name__)

RISKS_COLLECTION = "ai_risks"


class RiskEngine:
    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        *,
        llm_manager: Optional[LLMFallbackManager] = None,
        use_llm_summary: bool = True,
    ) -> None:
        self.db = db
        self.collection = db[RISKS_COLLECTION]
        self.projects = ProjectService(db)
        self.repositories = db["repositories"]
        self.documents = db["documents"]
        self.index_meta = db["index_meta"]
        self.llm_manager = llm_manager or services.llm_manager
        self.use_llm_summary = use_llm_summary

    async def analyze_project(self, *, user_id: str, project_id: str) -> list[dict[str, Any]]:
        await self.projects.get_project(user_id=user_id, project_id=project_id)
        repo = await self.repositories.find_one({"project_id": project_id})
        docs = [doc async for doc in self.documents.find({"project_id": project_id})]
        meta = await self.index_meta.find_one({"project_id": project_id})
        chunks_indexed = int((meta or {}).get("chunks_indexed") or 0)

        detected = self._detect_risks(repo=repo, docs=docs, chunks_indexed=chunks_indexed)
        if self.use_llm_summary and detected:
            detected = await self._enrich_with_llm(detected)

        await self.collection.delete_many({"project_id": project_id})
        now = utc_now()
        stored: list[dict[str, Any]] = []
        for risk in detected:
            doc = {
                "project_id": project_id,
                "user_id": user_id,
                "title": risk["title"],
                "description": risk["description"],
                "severity": risk["severity"],
                "recommendation": risk["recommendation"],
                "rule_id": risk["rule_id"],
                "generated_at": now,
                "created_at": now,
            }
            result = await self.collection.insert_one(doc)
            doc["_id"] = result.inserted_id
            stored.append(_serialize_risk(doc))

        await services.timeline.add_event(
            TimelineEvent(
                project_id=project_id,
                event_type="risk_generated",
                title="Risk Generated",
                description=f"Generated {len(stored)} project risk insight(s)",
                metadata={"count": len(stored)},
            )
        )
        return stored

    async def list_risks(self, *, user_id: str, project_id: str) -> list[dict[str, Any]]:
        await self.projects.get_project(user_id=user_id, project_id=project_id)
        cursor = self.collection.find({"project_id": project_id}).sort("generated_at", -1)
        return [_serialize_risk(doc) async for doc in cursor]

    def _detect_risks(
        self,
        *,
        repo: Optional[dict[str, Any]],
        docs: list[dict[str, Any]],
        chunks_indexed: int,
    ) -> list[dict[str, Any]]:
        risks: list[dict[str, Any]] = []
        inventory = source_inventory(repo=repo, docs=docs)
        knowledge = combine_knowledge_text(repo=repo, docs=docs)

        if repo is None and inventory["uploaded_doc_count"] == 0:
            risks.append(
                _risk(
                    rule_id="no_sources",
                    title="No knowledge sources connected",
                    description="This project has neither a GitHub repository nor uploaded documents.",
                    severity="high",
                    recommendation="Connect a public GitHub repository or upload project documentation.",
                )
            )
            return risks

        if repo is not None and not inventory["has_readme"]:
            risks.append(
                _risk(
                    rule_id="missing_readme",
                    title="Missing project overview",
                    description=(
                        "The connected repository does not include usable README content, "
                        "so newcomers lack a project overview."
                    ),
                    severity="high",
                    recommendation="Add a README.md that explains purpose, setup, and key modules.",
                )
            )
        elif inventory["has_readme"] and inventory["readme_chars"] < 180 and not has_topic(knowledge, "overview"):
            risks.append(
                _risk(
                    rule_id="missing_overview",
                    title="Missing project overview",
                    description=(
                        "Available documentation does not clearly explain what the project is "
                        "or how the system fits together."
                    ),
                    severity="medium",
                    recommendation="Expand README/overview docs with goals, users, and major components.",
                )
            )

        # Architecture risk is content-aware: README/docs that explain architecture are enough.
        if not has_topic(knowledge, "architecture"):
            risks.append(
                _risk(
                    rule_id="missing_architecture_knowledge",
                    title="Missing architecture knowledge",
                    description=(
                        "Indexed sources do not describe system architecture, components, or tech stack "
                        "clearly enough for reliable onboarding."
                    ),
                    severity="medium",
                    recommendation=(
                        "Document architecture in README, architecture notes, or design docs — "
                        "filename alone is not required if the knowledge exists."
                    ),
                )
            )

        if not has_topic(knowledge, "testing"):
            risks.append(
                _risk(
                    rule_id="no_testing_documentation",
                    title="No testing documentation",
                    description="No clear testing guidance was found across README, docs, or uploads.",
                    severity="medium",
                    recommendation="Document how to run tests, what suites exist, and quality expectations.",
                )
            )

        if not has_topic(knowledge, "deployment"):
            risks.append(
                _risk(
                    rule_id="no_deployment_instructions",
                    title="No deployment instructions",
                    description="Deployment/runbook guidance appears missing from indexed project knowledge.",
                    severity="medium",
                    recommendation="Add deployment steps, environments, and operational prerequisites.",
                )
            )

        if inventory["source_count"] < 2 or inventory["total_chars"] < 600:
            risks.append(
                _risk(
                    rule_id="poor_documentation_coverage",
                    title="Poor documentation coverage",
                    description=(
                        f"Only {inventory['source_count']} substantive source(s) "
                        f"(~{inventory['total_chars']} chars) are available for knowledge extraction."
                    ),
                    severity="medium",
                    recommendation=(
                        "Increase coverage with README, task/spec docs, API notes, and uploaded PDFs/Markdown."
                    ),
                )
            )
        elif inventory["structure_count"] >= 40 and inventory["total_chars"] < 2500:
            risks.append(
                _risk(
                    rule_id="sparse_repository_documentation",
                    title="Sparse repository documentation",
                    description=(
                        f"Repository structure lists {inventory['structure_count']} paths, "
                        "but indexed documentation remains thin relative to codebase size."
                    ),
                    severity="medium",
                    recommendation="Document critical modules, APIs, and operational workflows first.",
                )
            )

        if chunks_indexed == 0:
            risks.append(
                _risk(
                    rule_id="not_indexed",
                    title="Knowledge base not indexed",
                    description="No vector chunks are indexed for AI retrieval yet.",
                    severity="medium",
                    recommendation="Run project indexing so the AI Knowledge Twin can answer grounded questions.",
                )
            )

        authors = {
            (item.get("author") or "").strip()
            for item in ((repo or {}).get("commit_summary") or [])
            if (item.get("author") or "").strip()
        }
        if inventory["structure_count"] >= 25 and 0 < len(authors) <= 1:
            risks.append(
                _risk(
                    rule_id="single_contributor_concentration",
                    title="Only one contributor owns critical modules",
                    description=(
                        "Recent commit history is concentrated in a single contributor, "
                        "increasing bus-factor risk for critical modules."
                    ),
                    severity="low",
                    recommendation="Share ownership via pairing, reviews, and module documentation.",
                )
            )

        important = {path.lower() for path in ((repo or {}).get("important_files") or [])}
        dependency_markers = {
            "package.json",
            "requirements.txt",
            "pyproject.toml",
            "go.mod",
            "pom.xml",
            "cargo.toml",
        }
        if (
            len(important.intersection(dependency_markers)) >= 2
            and inventory["total_chars"] < 800
            and not has_topic(knowledge, "api")
        ):
            risks.append(
                _risk(
                    rule_id="high_dependency_modules",
                    title="High dependency modules with weak docs",
                    description=(
                        "Multiple dependency manifests were detected, but supporting integration "
                        "documentation looks weak."
                    ),
                    severity="low",
                    recommendation="Document external service dependencies and integration boundaries.",
                )
            )

        return risks

    async def _enrich_with_llm(self, risks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        bullets = "\n".join(
            f"- ({risk['severity']}) {risk['title']}: {risk['description']}" for risk in risks
        )
        prompt = (
            "Summarize these software project documentation risks in 2 short sentences "
            "for an engineering dashboard. Keep it practical.\n\n"
            f"{bullets}"
        )
        try:
            result = await self.llm_manager.generate(
                system_prompt=(
                    "You summarize project risks clearly and briefly. "
                    "Do not invent risks that are not listed."
                ),
                user_prompt=prompt,
            )
            summary = result.content.strip()
            if summary and risks:
                risks[0]["description"] = f"{risks[0]['description']} Summary: {summary}"
        except Exception as exc:  # noqa: BLE001 — rules still useful without LLM
            logger.warning("Risk LLM summarization skipped: %s", exc)
        return risks


def _risk(
    *,
    rule_id: str,
    title: str,
    description: str,
    severity: str,
    recommendation: str,
) -> dict[str, Any]:
    return {
        "rule_id": rule_id,
        "title": title,
        "description": description,
        "severity": severity,
        "recommendation": recommendation,
    }


def _serialize_risk(doc: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": oid_str(doc["_id"]),
        "project_id": str(doc["project_id"]),
        "title": doc["title"],
        "description": doc.get("description") or "",
        "severity": doc.get("severity") or "medium",
        "recommendation": doc.get("recommendation") or "",
        "rule_id": doc.get("rule_id"),
        "generated_at": doc.get("generated_at") or doc.get("created_at"),
    }
