"""Document upload and extraction orchestration."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.exceptions import AppError
from app.models.serializers import serialize_document
from app.services.container import services
from app.services.ingestion import DocumentExtractor
from app.services.project_service import ProjectService
from app.services.timeline.base import TimelineEvent
from app.utils.files import (
    MAX_UPLOAD_BYTES,
    detect_document_type,
    ensure_upload_dir,
    sanitize_filename,
)
from app.utils.ids import to_object_id
from app.utils.time import utc_now

DOCUMENTS_COLLECTION = "documents"


class DocumentService:
    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        *,
        extractor: Optional[DocumentExtractor] = None,
        upload_root: Optional[Path] = None,
    ) -> None:
        self.db = db
        self.collection = db[DOCUMENTS_COLLECTION]
        self.projects = ProjectService(db)
        self.extractor = extractor or services.document_extractor
        self.upload_root = upload_root or Path(__file__).resolve().parents[2] / "uploads"

    async def upload_document(
        self,
        *,
        user_id: str,
        project_id: str,
        file_name: str,
        content: bytes,
    ) -> dict[str, Any]:
        await self.projects.get_project(user_id=user_id, project_id=project_id)

        if not content:
            raise AppError("Uploaded file is empty", status_code=400, code="empty_upload")
        if len(content) > MAX_UPLOAD_BYTES:
            raise AppError(
                f"File exceeds maximum size of {MAX_UPLOAD_BYTES // (1024 * 1024)} MB",
                status_code=400,
                code="file_too_large",
            )

        safe_name = sanitize_filename(file_name)
        file_type = detect_document_type(safe_name)
        extracted = await self.extractor.extract(
            file_name=safe_name,
            file_type=file_type,
            content=content,
        )

        project_dir = ensure_upload_dir(self.upload_root, project_id)
        stored_name = f"{uuid.uuid4().hex}_{safe_name}"
        storage_path = project_dir / stored_name
        storage_path.write_bytes(content)

        now = utc_now()
        is_architecture = "architecture" in safe_name.lower()
        doc = {
            "project_id": project_id,
            "user_id": user_id,
            "file_name": safe_name,
            "file_type": file_type.value,
            "file_size": len(content),
            "storage_path": str(storage_path),
            "extracted_text": extracted.text,
            "char_count": extracted.char_count,
            "page_count": extracted.page_count,
            "metadata": extracted.metadata,
            "status": "extracted",
            "is_architecture": is_architecture,
            "upload_time": now,
            "created_at": now,
            "updated_at": now,
        }
        result = await self.collection.insert_one(doc)
        doc["_id"] = result.inserted_id

        event_title = "Architecture Uploaded" if is_architecture else "Document Uploaded"
        event_type = "architecture_uploaded" if is_architecture else "document_uploaded"
        await services.timeline.add_event(
            TimelineEvent(
                project_id=project_id,
                event_type=event_type,
                title=event_title,
                description=safe_name,
                metadata={
                    "document_id": str(result.inserted_id),
                    "file_type": file_type.value,
                    "char_count": extracted.char_count,
                },
            )
        )

        return serialize_document(doc)

    async def list_documents(self, *, user_id: str, project_id: str) -> list[dict[str, Any]]:
        await self.projects.get_project(user_id=user_id, project_id=project_id)
        cursor = self.collection.find({"project_id": project_id}).sort("created_at", -1)
        return [serialize_document(doc) async for doc in cursor]

    async def get_document(
        self,
        *,
        user_id: str,
        project_id: str,
        document_id: str,
        include_text: bool = False,
    ) -> dict[str, Any]:
        await self.projects.get_project(user_id=user_id, project_id=project_id)
        doc = await self.collection.find_one(
            {
                "_id": to_object_id(document_id, field_name="document_id"),
                "project_id": project_id,
            }
        )
        if doc is None:
            raise AppError("Document not found", status_code=404, code="document_not_found")
        return serialize_document(doc, include_text=include_text)

    async def delete_document(
        self,
        *,
        user_id: str,
        project_id: str,
        document_id: str,
    ) -> None:
        await self.projects.get_project(user_id=user_id, project_id=project_id)
        doc = await self.collection.find_one(
            {
                "_id": to_object_id(document_id, field_name="document_id"),
                "project_id": project_id,
            }
        )
        if doc is None:
            raise AppError("Document not found", status_code=404, code="document_not_found")

        await self.collection.delete_one({"_id": doc["_id"]})
        storage_path = doc.get("storage_path")
        if storage_path:
            path = Path(storage_path)
            if path.exists():
                path.unlink(missing_ok=True)

    async def count_documents(self, project_id: str) -> int:
        return await self.collection.count_documents({"project_id": project_id})

    async def delete_for_project(self, project_id: str) -> None:
        cursor = self.collection.find({"project_id": project_id})
        async for doc in cursor:
            storage_path = doc.get("storage_path")
            if storage_path:
                Path(storage_path).unlink(missing_ok=True)
        await self.collection.delete_many({"project_id": project_id})
