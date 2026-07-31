import fitz  # PyMuPDF
from fastapi import UploadFile, HTTPException
from typing import Dict, Any


class PDFParserService:
    async def parse(self, file: UploadFile) -> Dict[str, Any]:
        """Extract text and metadata from a PDF file."""
        filename = file.filename or ""
        if not filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="File must be a PDF")

        doc = None
        try:
            content = await file.read()
            doc = fitz.open(stream=content, filetype="pdf")

            metadata = doc.metadata or {}
            total_pages = doc.page_count
            full_text = ""
            paragraphs = []

            for page in doc:
                text = page.get_text()
                full_text += text + "\n"

                # Basic paragraph splitting
                page_paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
                paragraphs.extend(page_paragraphs)

            return {
                "title": metadata.get("title", ""),
                "author": metadata.get("author", ""),
                "creator": metadata.get("creator", ""),
                "producer": metadata.get("producer", ""),
                "subject": metadata.get("subject", ""),
                "keywords": metadata.get("keywords", ""),
                "creation_date": metadata.get("creationDate", ""),
                "modification_date": metadata.get("modDate", ""),
                "total_pages": total_pages,
                "full_text": full_text.strip(),
                "paragraphs": paragraphs,
                "headings": [],  # Advanced heading detection requires layout analysis
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error parsing PDF: {str(e)}")
        finally:
            if doc is not None:
                doc.close()


pdf_parser_service = PDFParserService()
