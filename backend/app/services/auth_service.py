"""Authentication and user persistence service."""

from __future__ import annotations

from typing import Any, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.auth.security import create_access_token, hash_password, verify_password
from app.core.exceptions import AppError
from app.models.serializers import serialize_user
from app.schemas.user import build_initials
from app.utils.ids import to_object_id
from app.utils.time import utc_now

USERS_COLLECTION = "users"


class AuthService:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.collection = db[USERS_COLLECTION]

    async def register(
        self,
        *,
        full_name: str,
        email: str,
        password: str,
        role: str = "Project manager",
    ) -> dict[str, Any]:
        normalized_email = email.strip().lower()
        existing = await self.collection.find_one({"email": normalized_email})
        if existing:
            raise AppError(
                "An account with this email already exists",
                status_code=409,
                code="email_taken",
            )

        now = utc_now()
        doc = {
            "full_name": full_name.strip(),
            "email": normalized_email,
            "password_hash": hash_password(password),
            "role": role.strip() or "Project manager",
            "initials": build_initials(full_name),
            "avatar_url": None,
            "created_at": now,
            "updated_at": now,
        }
        result = await self.collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        user = serialize_user(doc)
        token = create_access_token(user["id"], extra_claims={"email": user["email"]})
        return {"access_token": token, "token_type": "bearer", "user": user}

    async def login(self, *, email: str, password: str) -> dict[str, Any]:
        normalized_email = email.strip().lower()
        doc = await self.collection.find_one({"email": normalized_email})
        if doc is None or not verify_password(password, doc["password_hash"]):
            raise AppError(
                "Invalid email or password",
                status_code=401,
                code="invalid_credentials",
            )

        user = serialize_user(doc)
        token = create_access_token(user["id"], extra_claims={"email": user["email"]})
        return {"access_token": token, "token_type": "bearer", "user": user}

    async def get_user_by_id(self, user_id: str) -> Optional[dict[str, Any]]:
        doc = await self.collection.find_one({"_id": to_object_id(user_id, field_name="user_id")})
        if doc is None:
            return None
        return serialize_user(doc)
