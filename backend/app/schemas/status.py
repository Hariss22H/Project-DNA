"""Project ingestion status schemas."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

from app.schemas.project import ProjectStatus


class ProjectStatusData(BaseModel):
    project_id: str
    project_status: ProjectStatus
    github_connected: bool = False
    documents_count: int = 0
    has_readme: bool = False
    ready_for_indexing: bool = False
    is_indexed: bool = False
    chunks_indexed: int = 0
    message: str = ""


class ProjectStatusResponse(BaseModel):
    success: bool = True
    data: ProjectStatusData
    message: Optional[str] = None
