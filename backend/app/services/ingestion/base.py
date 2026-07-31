"""Document ingestion contracts for Member 3 extractors."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    MARKDOWN = "md"
    TXT = "txt"


class ExtractedDocument(BaseModel):
    """Normalized text payload produced by any document extractor."""

    file_name: str
    file_type: DocumentType
    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    page_count: Optional[int] = None
    char_count: int = 0


class DocumentExtractor(ABC):
    """Abstract extractor. Member 3 implements format-specific logic."""

    @abstractmethod
    def supports(self, file_type: DocumentType) -> bool:
        """Return True when this extractor can handle the given type."""

    @abstractmethod
    async def extract(
        self,
        *,
        file_name: str,
        file_type: DocumentType,
        content: bytes,
    ) -> ExtractedDocument:
        """Extract clean text from raw file bytes."""
