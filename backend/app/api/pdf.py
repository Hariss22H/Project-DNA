from fastapi import APIRouter, File, UploadFile
from typing import Dict, Any
from app.services.pdf_parser import pdf_parser_service

router = APIRouter(prefix="/documents/pdf", tags=["PDF"])

@router.post("/parse", response_model=Dict[str, Any])
async def parse_pdf(file: UploadFile = File(...)):
    """Parse a PDF document and extract text, paragraphs, and metadata."""
    return await pdf_parser_service.parse(file)
