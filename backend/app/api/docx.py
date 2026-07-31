from fastapi import APIRouter, File, UploadFile
from typing import Dict, Any
from app.services.docx_parser import docx_parser_service

router = APIRouter(prefix="/documents/docx", tags=["DOCX"])

@router.post("/parse", response_model=Dict[str, Any])
async def parse_docx(file: UploadFile = File(...)):
    """Parse a DOCX document and extract structure, paragraphs, headings, tables, and metadata."""
    return await docx_parser_service.parse(file)
