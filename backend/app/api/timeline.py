from fastapi import APIRouter
from typing import List, Dict, Any
from app.services.timeline_service import timeline_service

router = APIRouter(prefix="/timeline", tags=["Timeline"])

@router.post("/generate", response_model=List[Dict[str, Any]])
def generate_timeline():
    """Generate a chronological timeline of events from the repository and document uploads."""
    return timeline_service.generate()
