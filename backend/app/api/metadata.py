from fastapi import APIRouter, File, UploadFile
from typing import Dict, Any
from app.services.metadata_service import metadata_service

router = APIRouter(prefix="/documents", tags=["Metadata"])

@router.post("/metadata", response_model=Dict[str, Any])
async def generate_metadata(file: UploadFile = File(...)):
    """Generate extensive metadata and statistics for a given document."""
    return await metadata_service.generate(file)
