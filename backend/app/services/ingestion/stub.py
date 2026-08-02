"""Stub document extractor for Phase 0 / fallback text formats."""

from __future__ import annotations

from app.core.exceptions import AppError
from app.services.ingestion.base import DocumentExtractor, DocumentType, ExtractedDocument


class StubDocumentExtractor(DocumentExtractor):
    """Handles TXT/Markdown via UTF-8 decode; rejects binary formats until M3 lands."""

    def supports(self, file_type: DocumentType) -> bool:
        return file_type in {DocumentType.TXT, DocumentType.MARKDOWN}

    async def extract(
        self,
        *,
        file_name: str,
        file_type: DocumentType,
        content: bytes,
    ) -> ExtractedDocument:
        if not self.supports(file_type):
            raise AppError(
                f"Extractor stub does not support '{file_type.value}'. "
                "Member 3 should provide PDF/DOCX extractors.",
                status_code=501,
                code="extractor_not_implemented",
            )

        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise AppError(
                "Unable to decode document as UTF-8",
                status_code=400,
                code="decode_error",
            ) from exc

        cleaned = "\n".join(line.rstrip() for line in text.splitlines()).strip()
        return ExtractedDocument(
            file_name=file_name,
            file_type=file_type,
            text=cleaned,
            metadata={"source": "stub_extractor"},
            char_count=len(cleaned),
        )
