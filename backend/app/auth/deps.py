"""Authentication dependencies for protected routes."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.auth.security import decode_access_token
from app.core.dependencies import get_db
from app.core.exceptions import AppError
from app.services.auth_service import AuthService

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> dict[str, Any]:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AppError(
            "Authentication required",
            status_code=401,
            code="not_authenticated",
        )

    payload = decode_access_token(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise AppError(
            "Invalid authentication token",
            status_code=401,
            code="invalid_token",
        )

    user = await AuthService(db).get_user_by_id(user_id)
    if user is None:
        raise AppError(
            "User not found",
            status_code=401,
            code="user_not_found",
        )
    return user


CurrentUser = Annotated[dict[str, Any], Depends(get_current_user)]
