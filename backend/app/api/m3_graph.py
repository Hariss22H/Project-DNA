from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.graph_service import graph_service

router = APIRouter(prefix="/graph", tags=["Member 3 - Knowledge Graph"])


class GraphEnrichRequest(BaseModel):
    entities: List[Dict[str, Any]] = Field(default_factory=list)


@router.post("/generate", response_model=Dict[str, Any])
def generate_graph():
    """Generate structured JSON representing a Knowledge Graph of the project."""
    return graph_service.generate()


@router.post("/enrich", response_model=Dict[str, Any])
def enrich_graph(payload: Optional[GraphEnrichRequest] = None):
    """Enrich the structural graph with AI-extracted entity nodes."""
    entities = (payload.entities if payload else []) or []
    return graph_service.enrich(entities)
