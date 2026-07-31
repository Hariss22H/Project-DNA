import hashlib
from datetime import datetime, timezone
from pathlib import Path
from fastapi import UploadFile, HTTPException
from typing import Dict, Any

class MetadataService:
    async def generate(self, file: UploadFile) -> Dict[str, Any]:
        """Generate comprehensive metadata for an uploaded file."""
        try:
            original_filename = file.filename or "unknown"
            path = Path(original_filename)
            extension = path.suffix.lower()
            mime_type = file.content_type or "application/octet-stream"
            
            content = await file.read()
            file_size = len(content)
            
            sha256_hash = hashlib.sha256(content).hexdigest()
            
            # Default text stats
            word_count = 0
            char_count = 0
            reading_time_mins = 0
            language = "Unknown"
            
            text_extensions = {".txt", ".md", ".json", ".py", ".js", ".html", ".css", ".csv"}
            
            if extension in text_extensions:
                try:
                    text = content.decode('utf-8')
                    char_count = len(text)
                    words = text.split()
                    word_count = len(words)
                    reading_time_mins = round(word_count / 200, 2)
                    language = "English" # Best effort default
                except UnicodeDecodeError:
                    pass # Not valid UTF-8, ignore text stats
            
            return {
                "filename": original_filename,
                "extension": extension,
                "mime_type": mime_type,
                "file_size_bytes": file_size,
                "sha256_hash": sha256_hash,
                "created_date": datetime.now(timezone.utc).isoformat(),
                "modified_date": datetime.now(timezone.utc).isoformat(),
                "reading_time_mins": reading_time_mins,
                "word_count": word_count,
                "character_count": char_count,
                "language": language
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error generating metadata: {str(e)}")

metadata_service = MetadataService()
