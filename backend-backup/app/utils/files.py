"""File upload helpers."""

from __future__ import annotations

import re
from pathlib import Path

from app.core.exceptions import AppError
from app.services.ingestion.base import DocumentType

ALLOWED_EXTENSIONS = {
    ".pdf": DocumentType.PDF,
    ".docx": DocumentType.DOCX,
    ".md": DocumentType.MARKDOWN,
    ".markdown": DocumentType.MARKDOWN,
    ".txt": DocumentType.TXT,
}

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB


def detect_document_type(file_name: str) -> DocumentType:
    suffix = Path(file_name).suffix.lower()
    doc_type = ALLOWED_EXTENSIONS.get(suffix)
    if doc_type is None:
        raise AppError(
            "Unsupported file type. Allowed: PDF, DOCX, Markdown, TXT",
            status_code=400,
            code="unsupported_file_type",
            details={"allowed": sorted({ext.lstrip(".") for ext in ALLOWED_EXTENSIONS})},
        )
    return doc_type


def sanitize_filename(file_name: str) -> str:
    name = Path(file_name).name.strip() or "upload.bin"
    name = re.sub(r"[^\w.\- ()]+", "_", name)
    return name[:180]


def ensure_upload_dir(base_dir: Path, project_id: str) -> Path:
    path = base_dir / project_id
    path.mkdir(parents=True, exist_ok=True)
    return path
