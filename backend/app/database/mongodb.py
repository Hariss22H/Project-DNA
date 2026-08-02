"""MongoDB connection lifecycle using Motor."""

from __future__ import annotations

import logging
from typing import Optional

import certifi
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.server_api import ServerApi

from app.core.config import Settings, get_settings
from app.core.exceptions import AppError, DB_UNAVAILABLE_MESSAGE

logger = logging.getLogger(__name__)


class MongoDB:
    """Holds the shared Motor client/database for the app lifetime."""

    def __init__(self) -> None:
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None

    async def connect(self, settings: Optional[Settings] = None) -> None:
        settings = settings or get_settings()
        if self.client is not None:
            return

        # certifi CA bundle avoids common Windows/OpenSSL trust-store gaps with Atlas.
        self.client = AsyncIOMotorClient(
            settings.mongodb_uri,
            serverSelectionTimeoutMS=8000,
            connectTimeoutMS=8000,
            tlsCAFile=certifi.where(),
            server_api=ServerApi("1"),
        )
        self.db = self.client[settings.mongodb_db_name]
        logger.info("MongoDB client initialized for database '%s'", settings.mongodb_db_name)

        # Fail fast during startup so logs clearly show Atlas/network problems.
        try:
            await self.client.admin.command("ping")
            logger.info("MongoDB ping succeeded")
        except Exception as exc:  # noqa: BLE001
            logger.error("MongoDB ping failed on startup: %s", exc)

    async def disconnect(self) -> None:
        if self.client is not None:
            self.client.close()
            self.client = None
            self.db = None
            logger.info("MongoDB client closed")

    def get_db(self) -> AsyncIOMotorDatabase:
        if self.db is None:
            raise RuntimeError("MongoDB has not been initialized. Call connect() first.")
        return self.db

    async def ping(self) -> bool:
        """Return True when the database responds to ping."""
        if self.client is None:
            return False
        try:
            await self.client.admin.command("ping")
            return True
        except Exception as exc:  # noqa: BLE001 — health check must not raise
            logger.warning("MongoDB ping failed: %s", exc)
            return False


mongodb = MongoDB()


def raise_db_unavailable(exc: Exception) -> None:
    """Convert low-level Mongo errors into a user-facing AppError."""
    details = str(exc)
    raise AppError(
        DB_UNAVAILABLE_MESSAGE,
        status_code=503,
        code="database_unavailable",
        details=details[:300],
    ) from exc


async def get_database() -> AsyncIOMotorDatabase:
    """FastAPI dependency that yields the active database."""
    return mongodb.get_db()
