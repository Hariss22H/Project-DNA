"""In-memory timeline stub for Phase 0 (replaced with MongoDB in Phase 5)."""

from __future__ import annotations

import uuid

from app.services.timeline.base import TimelineEvent, TimelineService


class StubTimelineService(TimelineService):
    def __init__(self) -> None:
        self._events: list[TimelineEvent] = []

    async def add_event(self, event: TimelineEvent) -> TimelineEvent:
        stored = event.model_copy(update={"id": event.id or str(uuid.uuid4())})
        self._events.append(stored)
        return stored

    async def list_events(self, project_id: str, *, limit: int = 100) -> list[TimelineEvent]:
        items = [event for event in self._events if event.project_id == project_id]
        items = sorted(items, key=lambda item: item.created_at, reverse=True)
        return items[: max(1, min(limit, 200))]
