"""Indexing API schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.schemas.project import ProjectStatus


class IndexResultData(BaseModel):
    project_id: str
    project_status: ProjectStatus
    chunks_indexed: int
    sources_indexed: int
    embedding_model: str
    vector_size: int
    last_indexed_at: Optional[datetime] = None
    message: str = ""


class IndexResponse(BaseModel):
    success: bool = True
    data: IndexResultData
    message: Optional[str] = None


class IndexStatusData(BaseModel):
    project_id: str
    project_status: ProjectStatus
    chunks_indexed: int = 0
    sources_indexed: int = 0
    embedding_model: str
    vector_size: int
    last_indexed_at: Optional[datetime] = None
    is_indexed: bool = False


class IndexStatusResponse(BaseModel):
    success: bool = True
    data: IndexStatusData
