"""Project workspace schemas."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ProjectStatus(str, Enum):
    CREATED = "created"
    INDEXING = "indexing"
    READY = "ready"
    ERROR = "error"


class ProjectCreate(BaseModel):
    project_name: str = Field(..., min_length=1, max_length=160, examples=["Nova Web"])
    description: str = Field(
        default="",
        max_length=2000,
        examples=["Customer-facing web platform knowledge twin"],
    )


class ProjectUpdate(BaseModel):
    project_name: Optional[str] = Field(default=None, min_length=1, max_length=160)
    description: Optional[str] = Field(default=None, max_length=2000)
    github_repository: Optional[str] = Field(default=None, max_length=500)
    project_status: Optional[ProjectStatus] = None


class ProjectPublic(BaseModel):
    id: str
    user_id: str
    project_name: str
    description: str = ""
    github_repository: Optional[str] = None
    project_status: ProjectStatus = ProjectStatus.CREATED
    created_at: datetime
    updated_at: datetime


class ProjectResponse(BaseModel):
    success: bool = True
    data: ProjectPublic
    message: Optional[str] = None


class ProjectListResponse(BaseModel):
    success: bool = True
    data: list[ProjectPublic]
