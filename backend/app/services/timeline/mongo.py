"""MongoDB-backed timeline persistence."""

from __future__ import annotations

from typing import Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database.mongodb import mongodb
from app.services.timeline.base import TimelineEvent, TimelineService
from app.utils.ids import oid_str
from app.utils.time import utc_now

TIMELINE_COLLECTION = "timeline_events"


class MongoTimelineService(TimelineService):
    """Stores timeline events in MongoDB. DB is resolved lazily for easy wiring."""

    def __init__(self, db: Optional[AsyncIOMotorDatabase] = None) -> None:
        self._db = db

    def _collection(self):
        db = self._db or mongodb.get_db()
        return db[TIMELINE_COLLECTION]

    async def add_event(self, event: TimelineEvent) -> TimelineEvent:
        created_at = event.created_at or utc_now()
        doc = {
            "project_id": event.project_id,
            "event_type": event.event_type,
            "title": event.title,
            "description": event.description,
            "metadata": event.metadata or {},
            "created_at": created_at,
        }
        result = await self._collection().insert_one(doc)
        return event.model_copy(update={"id": oid_str(result.inserted_id), "created_at": created_at})

    async def list_events(self, project_id: str, *, limit: int = 100) -> list[TimelineEvent]:
        cursor = (
            self._collection()
            .find({"project_id": project_id})
            .sort("created_at", -1)
            .limit(max(1, min(limit, 200)))
        )
        items: list[TimelineEvent] = []
        async for doc in cursor:
            items.append(
                TimelineEvent(
                    id=oid_str(doc["_id"]),
                    project_id=doc["project_id"],
                    event_type=doc.get("event_type") or "event",
                    title=doc.get("title") or "Event",
                    description=doc.get("description"),
                    metadata=doc.get("metadata") or {},
                    created_at=doc["created_at"],
                )
            )
        return items
