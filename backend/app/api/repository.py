from fastapi import APIRouter
from typing import Dict, List, Any
from app.services.local_repository_service import repository_service

router = APIRouter(prefix="/repository", tags=["Repository"])

# Note: We use synchronous def instead of async def here because 
# os and pathlib file system interactions are synchronous and blocking.
# FastAPI will automatically run these in a background threadpool.

@router.get("/structure", response_model=Dict[str, Any])
def get_structure():
    """
    Get the full recursive hierarchy of the repository (folders and files).
    Ignores generated and hidden folders like .git, node_modules, __pycache__, etc.
    """
    return repository_service.get_structure()

@router.get("/files", response_model=List[Dict[str, Any]])
def get_files():
    """
    Get a flat list of all valid files in the repository.
    Includes file sizes and relative paths.
    """
    return repository_service.get_files()

@router.get("/folders", response_model=List[Dict[str, Any]])
def get_folders():
    """
    Get a flat list of all valid folders in the repository.
    """
    return repository_service.get_folders()

@router.get("/statistics", response_model=Dict[str, Any])
def get_statistics():
    """
    Get aggregated statistics about the local repository:
    - Total folders and files
    - Total repository size
    - Count of files per extension
    - Count of files per programming language
    - Top 10 largest files
    """
    return repository_service.get_statistics()
