from typing import Any, Dict, List

from fastapi import APIRouter

from app.services.timeline_service import timeline_service

router = APIRouter(prefix="/integrations/timeline", tags=["Member 3 - Timeline"])


@router.post("/generate", response_model=List[Dict[str, Any]])
def generate_timeline():
    """Generate a chronological timeline of events from the repository and document uploads."""
    return timeline_service.generate()
