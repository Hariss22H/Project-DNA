from typing import Any, Dict

from fastapi import APIRouter

from app.services.graph_service import graph_service

router = APIRouter(prefix="/integrations/graph", tags=["Member 3 - Knowledge Graph"])


@router.post("/generate", response_model=Dict[str, Any])
def generate_graph():
    """Generate structured JSON representing a Knowledge Graph of the project."""
    return graph_service.generate()
