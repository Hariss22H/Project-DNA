"""Helpers for identifying and scoring project documentation coverage."""

from __future__ import annotations

from typing import Any, Iterable, Optional

DOC_BASENAMES = {
    "readme",
    "readme.md",
    "task.md",
    "spec.md",
    "specification.md",
    "architecture.md",
    "architecture.pdf",
    "architecture.docx",
    "contributing.md",
    "changelog.md",
    "overview.md",
    "design.md",
    "api.md",
    "deployment.md",
    "deploy.md",
    "testing.md",
    "tests.md",
    "install.md",
    "setup.md",
    "security.md",
}

DOC_EXTENSIONS = {".md", ".txt", ".rst", ".pdf", ".docx", ".adoc"}

TOPIC_KEYWORDS = {
    "overview": ("overview", "introduction", "about this project", "project summary", "what is"),
    "architecture": (
        "architecture",
        "system design",
        "high-level design",
        "components",
        "module structure",
        "tech stack",
        "technology stack",
    ),
    "testing": ("test", "testing", "pytest", "unit test", "integration test", "qa", "coverage"),
    "deployment": (
        "deploy",
        "deployment",
        "docker",
        "kubernetes",
        "ci/cd",
        "pipeline",
        "production",
        "hosting",
    ),
    "api": ("api", "endpoint", "rest", "graphql", "route"),
    "auth": ("auth", "jwt", "oauth", "login", "authentication"),
}


def basename(path: str) -> str:
    return (path or "").replace("\\", "/").split("/")[-1].lower()


def is_documentation_path(path: str) -> bool:
    """Return True when a repository path looks like documentation worth indexing."""
    if not path:
        return False
    lower = path.replace("\\", "/").lower()
    name = basename(lower)
    if name in DOC_BASENAMES:
        return True
    if "architecture" in name:
        return True
    if any(token in name for token in ("spec", "task", "design", "overview", "guide", "deploy", "test")):
        if any(name.endswith(ext) for ext in DOC_EXTENSIONS):
            return True
    if lower.startswith("docs/") or "/docs/" in f"/{lower}":
        if any(name.endswith(ext) for ext in DOC_EXTENSIONS | {""}):
            return True
    return False


def select_documentation_paths(structure: Iterable[str], *, limit: int = 20) -> list[str]:
    selected: list[str] = []
    seen: set[str] = set()
    for path in structure or []:
        if not path or path in seen:
            continue
        if not is_documentation_path(path):
            continue
        # Skip README here; it is already indexed via readme_content.
        if basename(path).startswith("readme"):
            continue
        seen.add(path)
        selected.append(path)
        if len(selected) >= limit:
            break
    return selected


def combine_knowledge_text(
    *,
    repo: Optional[dict[str, Any]],
    docs: list[dict[str, Any]],
) -> str:
    parts: list[str] = []
    if repo:
        if repo.get("readme_content"):
            parts.append(str(repo["readme_content"]))
        if repo.get("description"):
            parts.append(str(repo["description"]))
        for item in repo.get("documentation_files") or []:
            parts.append(str(item.get("path") or ""))
            parts.append(str(item.get("content") or ""))
        for path in repo.get("important_files") or []:
            parts.append(str(path))
        for path in (repo.get("structure") or [])[:80]:
            parts.append(str(path))
    for doc in docs:
        parts.append(str(doc.get("file_name") or ""))
        parts.append(str(doc.get("extracted_text") or ""))
    return "\n".join(parts).lower()


def has_topic(text: str, topic: str) -> bool:
    keywords = TOPIC_KEYWORDS.get(topic) or ()
    return any(keyword in text for keyword in keywords)


def source_inventory(
    *,
    repo: Optional[dict[str, Any]],
    docs: list[dict[str, Any]],
) -> dict[str, Any]:
    readme = ((repo or {}).get("readme_content") or "").strip()
    doc_files = list((repo or {}).get("documentation_files") or [])
    uploaded_texts = [(doc.get("extracted_text") or "").strip() for doc in docs]
    total_chars = len(readme) + sum(len(item.get("content") or "") for item in doc_files) + sum(
        len(text) for text in uploaded_texts
    )
    source_count = (
        (1 if readme else 0)
        + len([item for item in doc_files if (item.get("content") or "").strip()])
        + len([text for text in uploaded_texts if text])
    )
    return {
        "has_readme": bool(readme),
        "readme_chars": len(readme),
        "repo_doc_count": len(doc_files),
        "uploaded_doc_count": len(docs),
        "source_count": source_count,
        "total_chars": total_chars,
        "structure_count": len((repo or {}).get("structure") or []),
    }
