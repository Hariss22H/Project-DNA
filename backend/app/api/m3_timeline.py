from typing import Any, Dict, List

from fastapi import APIRouter, Query

from app.services.timeline_service import timeline_service

router = APIRouter(prefix="/timeline", tags=["Member 3 - Timeline"])


@router.post("/generate", response_model=List[Dict[str, Any]])
async def generate_timeline(
    include_github: bool = Query(
        default=True,
        description="Include live GitHub commits when GITHUB_OWNER/REPO are configured",
    ),
):
    """Generate a chronological timeline from local uploads/repo (+ optional GitHub)."""
    if include_github:
        return await timeline_service.generate_with_github()
    return timeline_service.generate()
