"""Context-aware AI risk detection with evidence and recommendations."""

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
from app.services.knowledge.semantics import evidence_snippets, structure_signals
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
            detected = await self._enrich_with_llm(detected, repo=repo, docs=docs)

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
                "evidence": risk.get("evidence") or [],
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
                title="Risk Analysis Completed",
                description=f"AI consultant generated {len(stored)} context-aware risk insight(s).",
                metadata={"count": len(stored), "source": "AI"},
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
        signals = structure_signals((repo or {}).get("structure") or [])
        source_names = _source_names(repo=repo, docs=docs)

        if repo is None and inventory["uploaded_doc_count"] == 0:
            risks.append(
                _risk(
                    rule_id="no_sources",
                    title="No knowledge sources connected",
                    description="This project has neither a GitHub repository nor uploaded documents.",
                    severity="high",
                    recommendation="Connect a public GitHub repository or upload project documentation.",
                    evidence=["No repository connected", "No uploaded documents"],
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
                    evidence=["Repository connected but README content is empty"],
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
                    evidence=[
                        f"README is only {inventory['readme_chars']} characters",
                        *source_names[:2],
                    ],
                )
            )

        # Content-aware architecture: README explanation is enough.
        if not has_topic(knowledge, "architecture"):
            risks.append(
                _risk(
                    rule_id="missing_architecture_knowledge",
                    title="Architecture is not explained clearly",
                    description=(
                        "Indexed sources do not describe system architecture, components, or tech stack "
                        "clearly enough for reliable onboarding."
                    ),
                    severity="medium",
                    recommendation=(
                        "Add a short architecture section covering major components and data flow. "
                        "A dedicated Architecture.pdf is optional if README already explains it."
                    ),
                    evidence=[
                        "No architecture/system-design explanation found in indexed knowledge",
                        f"Reviewed sources: {', '.join(source_names[:4]) or 'none'}",
                    ],
                )
            )

        if not has_topic(knowledge, "api") and (signals["api_paths"] or signals["has_backend"]):
            risks.append(
                _risk(
                    rule_id="missing_api_documentation",
                    title="Missing API documentation",
                    description=(
                        "The project appears to expose backend/API surfaces, but indexed knowledge "
                        "does not explain endpoints, contracts, or usage."
                    ),
                    severity="medium",
                    recommendation="Document key APIs, auth requirements, and example requests in README or API notes.",
                    evidence=[
                        *(f"API-related path: {path}" for path in signals["api_paths"][:3]),
                        "Little or no API explanation found in documentation text",
                    ],
                )
            )

        if signals["has_auth_code"] and not _auth_documented_well(knowledge):
            auth_evidence = [f"Auth-related path: {path}" for path in signals["auth_paths"][:3]]
            auth_evidence.extend(
                evidence_snippets(knowledge, ("auth", "jwt", "login", "token"), limit=1)
                or ["Authentication terms appear thinly or not at all in docs"]
            )
            risks.append(
                _risk(
                    rule_id="auth_module_underdocumented",
                    title="Authentication module has limited documentation",
                    description=(
                        "The repository contains authentication-related code, but there is little "
                        "explanation of token flow, security decisions, or implementation details."
                    ),
                    severity="high",
                    recommendation=(
                        "Add a short authentication design section covering login, token issuance, "
                        "and protected-route behavior."
                    ),
                    evidence=auth_evidence,
                )
            )

        if not has_topic(knowledge, "testing") and not signals["has_tests"]:
            risks.append(
                _risk(
                    rule_id="no_testing_documentation",
                    title="No testing or testing guide found",
                    description="No clear testing guidance or test suites were found across code and docs.",
                    severity="medium",
                    recommendation="Document how to run tests and add at least a basic test guide for critical flows.",
                    evidence=["No testing keywords in docs", "No obvious test directories/files in structure sample"],
                )
            )
        elif not has_topic(knowledge, "testing") and signals["has_tests"]:
            risks.append(
                _risk(
                    rule_id="tests_without_guide",
                    title="Tests exist but lack a testing guide",
                    description="Test files appear in the repository, but documentation does not explain how to run them.",
                    severity="low",
                    recommendation="Add a Testing section with commands, scope, and expected coverage.",
                    evidence=["Test-related paths detected in repository structure", "No testing guide in indexed docs"],
                )
            )

        if not has_topic(knowledge, "deployment") and not signals["has_docker"]:
            risks.append(
                _risk(
                    rule_id="no_deployment_instructions",
                    title="Missing deployment instructions",
                    description="Deployment/runbook guidance appears missing from indexed project knowledge.",
                    severity="medium",
                    recommendation="Add deployment steps, environments, and operational prerequisites.",
                    evidence=["No deployment/Docker guidance found in indexed knowledge"],
                )
            )

        if not signals["has_env_example"] and ".env" not in knowledge and "environment variable" not in knowledge:
            if inventory["structure_count"] >= 15:
                risks.append(
                    _risk(
                        rule_id="missing_configuration_docs",
                        title="Configuration or environment setup missing",
                        description=(
                            "The project likely needs environment configuration, but setup docs "
                            "and env examples are weak or missing."
                        ),
                        severity="medium",
                        recommendation="Add `.env.example` and document required keys for local setup.",
                        evidence=[
                            "No .env.example detected in repository structure sample",
                            "Little environment-setup guidance in documentation",
                        ],
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
                    evidence=[
                        f"Source count: {inventory['source_count']}",
                        f"Approx. documentation characters: {inventory['total_chars']}",
                        *source_names[:3],
                    ],
                )
            )
        elif signals["has_backend"] and inventory["total_chars"] < 1800:
            risks.append(
                _risk(
                    rule_id="large_backend_thin_docs",
                    title="Large backend but almost no documentation",
                    description=(
                        "Backend structure is present, but documentation volume is low relative "
                        "to the amount of server-side code suggested by the repository."
                    ),
                    severity="medium",
                    recommendation="Document backend modules, APIs, and data stores used by the service layer.",
                    evidence=[
                        f"Backend paths detected: {len(signals['backend_paths'])}",
                        f"Documentation characters: {inventory['total_chars']}",
                    ],
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
                    evidence=[
                        f"Structure paths sampled: {inventory['structure_count']}",
                        f"Documentation characters: {inventory['total_chars']}",
                    ],
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
                    evidence=["chunks_indexed = 0"],
                )
            )

        authors = {
            (item.get("author") or "").strip()
            for item in ((repo or {}).get("commit_summary") or [])
            if (item.get("author") or "").strip()
        }
        if inventory["structure_count"] >= 25 and 0 < len(authors) <= 1:
            author_name = next(iter(authors))
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
                    evidence=[
                        f"Recent commit authors: {author_name}",
                        f"Structure paths sampled: {inventory['structure_count']}",
                    ],
                )
            )

        # Prefer higher severity first for demo readability.
        severity_rank = {"high": 0, "medium": 1, "low": 2}
        risks.sort(key=lambda item: severity_rank.get(item.get("severity"), 9))
        return risks

    async def _enrich_with_llm(
        self,
        risks: list[dict[str, Any]],
        *,
        repo: Optional[dict[str, Any]],
        docs: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        bullets = "\n".join(
            f"- ({risk['severity']}) {risk['title']}: {risk['description']}" for risk in risks[:8]
        )
        context_bits = [
            f"Repository: {(repo or {}).get('full_name') or 'none'}",
            f"Documents: {len(docs)}",
            f"README chars: {len(((repo or {}).get('readme_content') or ''))}",
        ]
        prompt = (
            "You are an AI project consultant. Rewrite each risk into a sharper consultant-style "
            "explanation in 1 sentence. Keep the same risks; do not invent new ones. "
            "Return plain text bullets matching the input order.\n\n"
            f"Context: {'; '.join(context_bits)}\n\nRisks:\n{bullets}"
        )
        try:
            result = await self.llm_manager.generate(
                system_prompt=(
                    "You refine software project risk explanations clearly and briefly. "
                    "Do not invent risks that are not listed."
                ),
                user_prompt=prompt,
            )
            lines = [
                line.lstrip("-• ").strip()
                for line in (result.content or "").splitlines()
                if line.strip()
            ]
            for index, risk in enumerate(risks[: len(lines)]):
                refined = lines[index]
                if refined and len(refined) > 20:
                    # Keep title; replace explanation body when LLM is useful.
                    if ":" in refined:
                        refined = refined.split(":", 1)[-1].strip()
                    risk["description"] = refined
        except Exception as exc:  # noqa: BLE001 — rules still useful without LLM
            logger.warning("Risk LLM enrichment skipped: %s", exc)
        return risks


def _auth_documented_well(knowledge: str) -> bool:
    if not knowledge:
        return False
    strong_signals = (
        "token flow",
        "jwt authentication",
        "authorization header",
        "access token",
        "refresh token",
        "login flow",
        "auth middleware",
        "protected endpoint",
        "bearer token",
    )
    hits = sum(1 for signal in strong_signals if signal in knowledge)
    return hits >= 2 or ("authentication" in knowledge and "jwt" in knowledge and "endpoint" in knowledge)


def _source_names(*, repo: Optional[dict[str, Any]], docs: list[dict[str, Any]]) -> list[str]:
    names: list[str] = []
    if repo and (repo.get("readme_content") or "").strip():
        names.append("README.md")
    for item in (repo or {}).get("documentation_files") or []:
        path = item.get("path")
        if path:
            names.append(str(path))
    for doc in docs:
        name = doc.get("file_name")
        if name:
            names.append(str(name))
    return names


def _risk(
    *,
    rule_id: str,
    title: str,
    description: str,
    severity: str,
    recommendation: str,
    evidence: Optional[list[str]] = None,
) -> dict[str, Any]:
    return {
        "rule_id": rule_id,
        "title": title,
        "description": description,
        "severity": severity,
        "recommendation": recommendation,
        "evidence": [item for item in (evidence or []) if item][:5],
    }


def _serialize_risk(doc: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": oid_str(doc["_id"]),
        "project_id": str(doc["project_id"]),
        "title": doc["title"],
        "description": doc.get("description") or "",
        "severity": doc.get("severity") or "medium",
        "recommendation": doc.get("recommendation") or "",
        "evidence": list(doc.get("evidence") or []),
        "rule_id": doc.get("rule_id"),
        "generated_at": doc.get("generated_at") or doc.get("created_at"),
    }
