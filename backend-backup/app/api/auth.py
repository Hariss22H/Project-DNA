"""Authentication API routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.auth.deps import CurrentUser
from app.core.dependencies import get_db
from app.schemas.auth import (
    AuthResponse,
    AuthTokenData,
    LoginRequest,
    MeResponse,
    RegisterRequest,
)
from app.schemas.user import UserPublic
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(
    payload: RegisterRequest,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> AuthResponse:
    data = await AuthService(db).register(
        full_name=payload.full_name,
        email=str(payload.email),
        password=payload.password,
        role=payload.role,
    )
    return AuthResponse(
        data=AuthTokenData(**data),
        message="Registration successful",
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Login and receive a JWT",
)
async def login(
    payload: LoginRequest,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> AuthResponse:
    data = await AuthService(db).login(
        email=str(payload.email),
        password=payload.password,
    )
    return AuthResponse(data=AuthTokenData(**data), message="Login successful")


@router.get(
    "/me",
    response_model=MeResponse,
    summary="Get the current authenticated user",
)
async def me(current_user: CurrentUser) -> MeResponse:
    return MeResponse(data=UserPublic(**current_user))
