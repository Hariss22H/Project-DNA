"""Timeline service contracts — activity events stored in MongoDB (Phase 5)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TimelineEvent(BaseModel):
    id: Optional[str] = None
    project_id: str
    event_type: str
    title: str
    description: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class TimelineService(ABC):
    """Member 3 may enrich event generation; Member 1 owns persistence APIs."""

    @abstractmethod
    async def add_event(self, event: TimelineEvent) -> TimelineEvent:
        """Persist a timeline event and return the stored record."""

    @abstractmethod
    async def list_events(self, project_id: str, *, limit: int = 100) -> list[TimelineEvent]:
        """Return timeline events for a project, newest first."""
