"""Document upload and listing API routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.auth.deps import CurrentUser
from app.core.dependencies import get_db, get_document_extractor
from app.schemas.common import MessageResponse
from app.schemas.document import (
    DocumentDetail,
    DocumentDetailResponse,
    DocumentListResponse,
    DocumentPublic,
    DocumentResponse,
)
from app.services.document_service import DocumentService
from app.services.ingestion import DocumentExtractor

router = APIRouter(prefix="/projects/{project_id}/documents", tags=["Documents"])


@router.post(
    "",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and extract a project document",
)
async def upload_document(
    project_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
    extractor: Annotated[DocumentExtractor, Depends(get_document_extractor)],
    file: UploadFile = File(...),
) -> DocumentResponse:
    content = await file.read()
    data = await DocumentService(db, extractor=extractor).upload_document(
        user_id=current_user["id"],
        project_id=project_id,
        file_name=file.filename or "upload.txt",
        content=content,
    )
    return DocumentResponse(data=DocumentPublic(**data), message="Document uploaded and extracted")


@router.get(
    "",
    response_model=DocumentListResponse,
    summary="List uploaded documents for a project",
)
async def list_documents(
    project_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> DocumentListResponse:
    items = await DocumentService(db).list_documents(
        user_id=current_user["id"],
        project_id=project_id,
    )
    return DocumentListResponse(data=[DocumentPublic(**item) for item in items])


@router.get(
    "/{document_id}",
    response_model=DocumentDetailResponse,
    summary="Get document details including extracted text",
)
async def get_document(
    project_id: str,
    document_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> DocumentDetailResponse:
    data = await DocumentService(db).get_document(
        user_id=current_user["id"],
        project_id=project_id,
        document_id=document_id,
        include_text=True,
    )
    return DocumentDetailResponse(data=DocumentDetail(**data))


@router.delete(
    "/{document_id}",
    response_model=MessageResponse,
    summary="Delete an uploaded document",
)
async def delete_document(
    project_id: str,
    document_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> MessageResponse:
    await DocumentService(db).delete_document(
        user_id=current_user["id"],
        project_id=project_id,
        document_id=document_id,
    )
    return MessageResponse(message="Document deleted")
