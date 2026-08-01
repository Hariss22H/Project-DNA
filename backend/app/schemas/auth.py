"""Auth request/response schemas."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.schemas.user import UserPublic


class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=120, examples=["Priya Sharma"])
    email: EmailStr = Field(..., examples=["priya@company.com"])
    password: str = Field(..., min_length=6, max_length=128, examples=["secret123"])
    role: str = Field(
        default="Project manager",
        max_length=64,
        examples=["Project manager"],
        description="UI role label (not used for authorization in MVP).",
    )


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    new_password: str = Field(..., min_length=6, max_length=128)
    confirm_password: str = Field(..., min_length=6, max_length=128)


class AuthTokenData(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


class AuthResponse(BaseModel):
    success: bool = True
    data: AuthTokenData
    message: Optional[str] = None


class MeResponse(BaseModel):
    success: bool = True
    data: UserPublic
