"""Authentication API routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.auth.deps import CurrentUser
from app.core.dependencies import get_db
from app.core.exceptions import AppError
from app.schemas.auth import (
    AuthResponse,
    AuthTokenData,
    ForgotPasswordRequest,
    LoginRequest,
    MeResponse,
    RegisterRequest,
    ResetPasswordRequest,
)
from app.schemas.common import MessageResponse
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


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    summary="Verify a registered email before password reset",
)
async def forgot_password(
    payload: ForgotPasswordRequest,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> MessageResponse:
    exists = await AuthService(db).email_exists(str(payload.email))
    if not exists:
        raise AppError(
            "No account found with this email.",
            status_code=404,
            code="user_not_found",
        )
    return MessageResponse(message="Email verified. You can set a new password.")


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Reset password for a registered email",
)
async def reset_password(
    payload: ResetPasswordRequest,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> MessageResponse:
    if payload.new_password != payload.confirm_password:
        raise AppError(
            "Passwords do not match.",
            status_code=400,
            code="password_mismatch",
        )
    await AuthService(db).reset_password(
        email=str(payload.email),
        new_password=payload.new_password,
    )
    return MessageResponse(message="Password updated successfully. You can sign in now.")
