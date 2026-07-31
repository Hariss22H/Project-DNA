"""ObjectId helpers."""

from __future__ import annotations

from bson import ObjectId

from app.core.exceptions import AppError


def to_object_id(value: str, *, field_name: str = "id") -> ObjectId:
    if not ObjectId.is_valid(value):
        raise AppError(
            f"Invalid {field_name}",
            status_code=400,
            code="invalid_id",
        )
    return ObjectId(value)


def oid_str(value: ObjectId | str) -> str:
    return str(value)
