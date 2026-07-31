from fastapi import APIRouter
from typing import Dict, Any
from app.services.graph_service import graph_service

router = APIRouter(prefix="/graph", tags=["Knowledge Graph"])

@router.post("/generate", response_model=Dict[str, Any])
def generate_graph():
    """Generate structured JSON representing a Knowledge Graph of the project."""
    return graph_service.generate()
