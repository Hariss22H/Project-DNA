"""Document upload API schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.services.ingestion.base import DocumentType


class DocumentPublic(BaseModel):
    id: str
    project_id: str
    file_name: str
    file_type: DocumentType
    file_size: int
    storage_path: str
    char_count: int = 0
    page_count: Optional[int] = None
    status: str = "extracted"
    is_architecture: bool = False
    upload_time: datetime
    created_at: datetime
    updated_at: datetime


class DocumentDetail(DocumentPublic):
    extracted_text: str = ""
    metadata: dict = Field(default_factory=dict)


class DocumentResponse(BaseModel):
    success: bool = True
    data: DocumentPublic
    message: Optional[str] = None


class DocumentDetailResponse(BaseModel):
    success: bool = True
    data: DocumentDetail


class DocumentListResponse(BaseModel):
    success: bool = True
    data: list[DocumentPublic]
