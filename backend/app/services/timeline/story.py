"""Build a human-readable project memory timeline from system + GitHub events."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from app.services.knowledge.semantics import classify_commit, humanize_event_type
from app.services.timeline.base import TimelineEvent


def enrich_timeline(
    *,
    project_id: str,
    events: list[TimelineEvent],
    repository: Optional[dict[str, Any]] = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Merge persisted events with interpreted GitHub commits into story cards."""
    cards: list[dict[str, Any]] = []

    for event in events:
        cards.append(_from_system_event(event))

    for commit in (repository or {}).get("commit_summary") or []:
        card = _from_commit(project_id, commit)
        if card:
            cards.append(card)

    # Deduplicate near-identical titles+times.
    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for card in cards:
        key = f"{card.get('title')}|{str(card.get('created_at'))[:16]}|{card.get('source')}"
        if key in seen:
            continue
        seen.add(key)
        deduped.append(card)

    deduped.sort(key=lambda item: _sort_key(item.get("created_at")), reverse=True)
    return deduped[: max(1, min(limit, 200))]


def _from_system_event(event: TimelineEvent) -> dict[str, Any]:
    title = _friendly_system_title(event.event_type, event.title)
    source = (event.metadata or {}).get("source") or humanize_event_type(event.event_type)
    return {
        "id": event.id,
        "project_id": event.project_id,
        "event_type": event.event_type,
        "title": title,
        "description": event.description,
        "source": source,
        "metadata": {
            **(event.metadata or {}),
            "source": source,
        },
        "created_at": event.created_at,
    }


def _from_commit(project_id: str, commit: dict[str, Any]) -> Optional[dict[str, Any]]:
    message = (commit.get("message") or "").strip()
    if not message:
        return None
    title, category = classify_commit(message)
    created_at = _parse_date(commit.get("date"))
    author = commit.get("author") or "unknown"
    sha = commit.get("sha") or ""
    return {
        "id": f"commit:{sha or title}",
        "project_id": project_id,
        "event_type": "github_commit",
        "title": title,
        "description": message.split("\n")[0][:220],
        "source": "GitHub",
        "metadata": {
            "source": "GitHub",
            "category": category,
            "author": author,
            "sha": sha,
            "raw_message": message,
        },
        "created_at": created_at,
    }


def _friendly_system_title(event_type: str, fallback: str) -> str:
    mapping = {
        "project_created": "Project Created",
        "repository_connected": "Repository Connected",
        "readme_indexed": "README Processed",
        "document_uploaded": "Documentation Uploaded",
        "architecture_uploaded": "Documentation Uploaded",
        "knowledge_indexed": "Knowledge Base Indexed",
        "knowledge_graph_built": "Knowledge Graph Generated",
        "knowledge_graph_generated": "Knowledge Graph Generated",
        "risk_generated": "Risk Analysis Completed",
    }
    return mapping.get(event_type, fallback or "Project Event")


def _parse_date(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str) and value:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            pass
    return datetime.now(timezone.utc)


def _sort_key(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value or "")
