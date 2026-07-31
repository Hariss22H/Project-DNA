"""Database package."""

from app.database.indexes import ensure_indexes
from app.database.mongodb import get_database, mongodb

__all__ = ["get_database", "mongodb", "ensure_indexes"]
