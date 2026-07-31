from fastapi import APIRouter, File, UploadFile
from typing import Dict, Any
from app.services.upload_service import upload_service

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.post("/upload", response_model=Dict[str, Any])
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a single document to the system.
    
    Supported file types: PDF, DOCX, TXT, MD
    Maximum file size: 25 MB
    """
    return await upload_service.save_upload_file(file)
