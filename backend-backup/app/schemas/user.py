"""User schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserPublic(BaseModel):
    id: str
    full_name: str
    email: EmailStr
    role: str = "Project manager"
    initials: str = ""
    avatar_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime


def build_initials(full_name: str) -> str:
    parts = [part for part in full_name.strip().split() if part]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return f"{parts[0][0]}{parts[-1][0]}".upper()
