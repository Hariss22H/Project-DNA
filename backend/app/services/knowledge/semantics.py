"""Semantic entity and relationship hints extracted from project knowledge."""

from __future__ import annotations

import re
from typing import Any, Optional

# Canonical semantic concepts for the knowledge graph.
TECHNOLOGIES: list[tuple[str, tuple[str, ...]]] = [
    ("FastAPI", ("fastapi",)),
    ("Flask", ("flask",)),
    ("Django", ("django",)),
    ("React", ("react", "react.js", "reactjs")),
    ("Next.js", ("next.js", "nextjs")),
    ("Vue", ("vue", "vue.js")),
    ("Node.js", ("node.js", "nodejs", "express")),
    ("MongoDB", ("mongodb", "mongo db", "motor")),
    ("PostgreSQL", ("postgresql", "postgres")),
    ("MySQL", ("mysql",)),
    ("Redis", ("redis",)),
    ("Qdrant", ("qdrant",)),
    ("JWT", ("jwt", "json web token")),
    ("OAuth", ("oauth", "oauth2")),
    ("Docker", ("docker", "dockerfile", "docker-compose")),
    ("Kubernetes", ("kubernetes", "k8s")),
    ("OpenAI", ("openai", "gpt-4", "gpt-4o")),
    ("Gemini", ("gemini", "google gemini")),
    ("Vite", ("vite",)),
    ("pytest", ("pytest",)),
    ("TypeScript", ("typescript",)),
    ("Python", ("python", "pyproject.toml")),
]

MODULES: list[tuple[str, tuple[str, ...]]] = [
    ("Backend", ("backend", "server", "api layer")),
    ("Frontend", ("frontend", "client", "ui layer", "react app")),
    ("Authentication", ("authentication", "auth module", "login", "signup", "jwt auth")),
    ("User Management", ("user management", "users", "user model", "user service")),
    ("Knowledge Twin", ("knowledge twin", "rag", "vector", "embeddings", "chat")),
    ("Document Ingestion", ("document", "upload", "pdf", "docx", "ingestion")),
    ("Deployment", ("deployment", "deploy", "ci/cd", "pipeline", "production")),
    ("Testing", ("testing", "unit test", "integration test", "pytest", "test suite")),
    ("Configuration", ("configuration", ".env", "environment variable", "settings")),
    ("REST API", ("rest api", "api endpoint", "openapi", "swagger")),
]

FEATURES: list[tuple[str, tuple[str, ...]]] = [
    ("AI Chat", ("ai chat", "ask ai", "rag chat", "knowledge twin")),
    ("Risk Analysis", ("risk analysis", "risk dashboard", "risk engine")),
    ("Timeline", ("timeline", "project history")),
    ("Knowledge Graph", ("knowledge graph", "entity graph")),
    ("GitHub Integration", ("github", "repository connected", "clone")),
]

# Meaningful relationship templates between known concept names.
RELATION_TEMPLATES: list[tuple[str, str, str, str]] = [
    ("Authentication", "JWT", "uses", "uses"),
    ("Authentication", "OAuth", "uses", "uses"),
    ("Backend", "FastAPI", "built_with", "built with"),
    ("Backend", "Flask", "built_with", "built with"),
    ("Backend", "Django", "built_with", "built with"),
    ("Backend", "MongoDB", "stores_data_in", "stores data in"),
    ("Backend", "PostgreSQL", "stores_data_in", "stores data in"),
    ("Backend", "Qdrant", "indexes_in", "indexes in"),
    ("Frontend", "React", "built_with", "built with"),
    ("Frontend", "Next.js", "built_with", "built with"),
    ("Frontend", "Vite", "built_with", "built with"),
    ("Frontend", "Backend", "communicates_with", "communicates with"),
    ("Frontend", "REST API", "consumes", "consumes"),
    ("Deployment", "Docker", "uses", "uses"),
    ("Deployment", "Kubernetes", "uses", "uses"),
    ("Knowledge Twin", "OpenAI", "powered_by", "powered by"),
    ("Knowledge Twin", "Gemini", "falls_back_to", "falls back to"),
    ("Knowledge Twin", "Qdrant", "retrieves_from", "retrieves from"),
    ("Document Ingestion", "Backend", "part_of", "part of"),
    ("Testing", "pytest", "uses", "uses"),
    ("REST API", "JWT", "secured_by", "secured by"),
    ("Configuration", "Backend", "configures", "configures"),
]


def find_matches(text: str, catalog: list[tuple[str, tuple[str, ...]]]) -> list[str]:
    lowered = (text or "").lower()
    found: list[str] = []
    for name, keywords in catalog:
        if any(keyword in lowered for keyword in keywords):
            found.append(name)
    return found


def structure_signals(structure: list[str]) -> dict[str, Any]:
    paths = [str(path).replace("\\", "/").lower() for path in (structure or [])]
    joined = "\n".join(paths)
    return {
        "has_backend": any(token in joined for token in ("backend/", "app/", "server/", "api/")),
        "has_frontend": any(token in joined for token in ("frontend/", "client/", "web/", "ui/")),
        "has_auth_code": any(
            token in joined
            for token in ("auth", "login", "jwt", "security", "middleware")
        ),
        "has_tests": any(token in joined for token in ("test_", "tests/", "pytest", "spec/")),
        "has_docker": any(token in joined for token in ("dockerfile", "docker-compose")),
        "has_env_example": any(token.endswith(".env.example") or token.endswith(".env.sample") for token in paths),
        "api_paths": [
            path
            for path in paths
            if any(token in path for token in ("/api/", "routes/", "endpoints/", "controllers/"))
        ][:12],
        "backend_paths": [path for path in paths if path.startswith(("backend/", "app/", "server/"))][:20],
        "auth_paths": [
            path
            for path in paths
            if any(token in path for token in ("auth", "login", "jwt", "security"))
        ][:12],
    }


def evidence_snippets(text: str, keywords: tuple[str, ...], *, limit: int = 2) -> list[str]:
    if not text:
        return []
    snippets: list[str] = []
    for raw_line in text.splitlines():
        line = " ".join(raw_line.strip().split())
        if len(line) < 24:
            continue
        lower = line.lower()
        if any(keyword in lower for keyword in keywords):
            snippets.append(line[:180] + ("..." if len(line) > 180 else ""))
        if len(snippets) >= limit:
            break
    return snippets


def slug(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", (value or "").strip().lower()).strip("-")
    return cleaned[:80] or "item"


def classify_commit(message: str) -> tuple[str, str]:
    """Return (friendly_title, category) for a commit message."""
    text = (message or "").strip()
    lower = text.lower()
    rules = [
        (("initial commit", "first commit", "scaffold", "bootstrap"), "Initial Commit", "setup"),
        (("auth", "jwt", "login", "oauth"), "Authentication Module Added", "feature"),
        (("mongo", "postgres", "database", "qdrant"), "Database Integration", "feature"),
        (("frontend", "react", "ui", "vite"), "Frontend Connected", "feature"),
        (("api doc", "swagger", "openapi", "endpoint doc"), "API Documentation Added", "docs"),
        (("readme", "docs", "documentation"), "README Updated", "docs"),
        (("docker", "deploy", "ci", "kubernetes"), "Deployment Configured", "ops"),
        (("fix", "bug", "hotfix", "patch"), "Bug Fixed", "fix"),
        (("merge", "pull request", "pr #"), "Pull Request Merged", "process"),
        (("test", "pytest", "coverage"), "Tests Added", "quality"),
        (("upload", "document", "pdf", "docx"), "Documentation Uploaded", "docs"),
    ]
    for keywords, title, category in rules:
        if any(keyword in lower for keyword in keywords):
            return title, category
    short = text.split("\n")[0][:80] or "Repository Update"
    return short, "commit"


def humanize_event_type(event_type: str) -> str:
    mapping = {
        "project_created": "System",
        "repository_connected": "GitHub",
        "readme_indexed": "Documentation",
        "document_uploaded": "Document",
        "architecture_uploaded": "Document",
        "knowledge_indexed": "AI",
        "knowledge_graph_built": "AI",
        "risk_generated": "AI",
        "github_commit": "GitHub",
    }
    return mapping.get(event_type, "System")
