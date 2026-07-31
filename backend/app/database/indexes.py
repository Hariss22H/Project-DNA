"""MongoDB index bootstrap for the hackathon MVP."""

from __future__ import annotations

import logging

from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


async def ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    """Create indexes required by Phase 1+ features."""
    await db["users"].create_index("email", unique=True)
    await db["projects"].create_index([("user_id", 1), ("created_at", -1)])
    await db["projects"].create_index("user_id")
    await db["repositories"].create_index("project_id", unique=True)
    await db["documents"].create_index([("project_id", 1), ("created_at", -1)])
    await db["index_meta"].create_index("project_id", unique=True)
    await db["ai_conversations"].create_index([("project_id", 1), ("created_at", -1)])
    await db["ai_conversations"].create_index([("user_id", 1), ("project_id", 1)])
    await db["timeline_events"].create_index([("project_id", 1), ("created_at", -1)])
    await db["ai_risks"].create_index([("project_id", 1), ("generated_at", -1)])
    await db["knowledge_graphs"].create_index("project_id", unique=True)
    logger.info("MongoDB indexes ensured")
