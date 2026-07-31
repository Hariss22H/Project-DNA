import uuid
import re
from datetime import datetime, timezone
from pathlib import Path
from fastapi import UploadFile, HTTPException

# Determine uploads directory relative to the backend root
UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"
# Automatically create the directory if it does not exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB
CHUNK_SIZE = 1024 * 1024  # 1 MB

class UploadService:
    """Service to handle secure document uploads."""
    
    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename by removing invalid characters.
        Replaces anything that isn't alphanumeric, dot, underscore, or dash.
        """
        return re.sub(r'[^a-zA-Z0-9.\-_]', '_', filename)

    async def save_upload_file(self, upload_file: UploadFile) -> dict:
        """
        Validate and save an uploaded document to the local filesystem.
        Enforces file type and size restrictions.
        Returns structured metadata.
        """
        original_filename = upload_file.filename or "unknown"
        path = Path(original_filename)
        extension = path.suffix.lower()

        # 1. Validate File Extension
        if extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type: {extension}. Allowed types are: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        # 2. Prevent Duplicate Filenames & Sanitize
        safe_original = self.sanitize_filename(original_filename)
        unique_id = uuid.uuid4().hex
        stored_filename = f"{unique_id}_{safe_original}"
        
        file_path = UPLOAD_DIR / stored_filename

        # 3. Stream File to Disk & Validate Size On-The-Fly
        file_size = 0
        try:
            with open(file_path, "wb") as buffer:
                while content := await upload_file.read(CHUNK_SIZE):
                    file_size += len(content)
                    if file_size > MAX_FILE_SIZE:
                        raise HTTPException(
                            status_code=413, 
                            detail="File too large. Maximum allowed size is 25 MB."
                        )
                    buffer.write(content)
        except HTTPException:
            # If size validation fails, clean up the partial file
            if file_path.exists():
                file_path.unlink()
            raise
        except Exception as e:
            # Clean up on generic I/O errors
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

        # 4. Return Structured Metadata
        return {
            "original_filename": original_filename,
            "stored_filename": stored_filename,
            "file_size": file_size,
            "mime_type": upload_file.content_type or "application/octet-stream",
            "extension": extension,
            "upload_time": datetime.now(timezone.utc).isoformat(),
        }

# Singleton instance
upload_service = UploadService()
