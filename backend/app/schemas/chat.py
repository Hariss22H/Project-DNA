"""AI chat schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    project_id: str = Field(..., examples=["665f1c2e9b1e4a0012ab34cd"])
    question: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        examples=["Explain the authentication flow in this project."],
    )


class ChatSource(BaseModel):
    id: str
    score: float
    file_name: Optional[str] = None
    title: Optional[str] = None
    source_type: Optional[str] = None
    chunk_index: Optional[int] = None
    snippet: str = ""


class ChatAnswerData(BaseModel):
    conversation_id: Optional[str] = None
    project_id: str
    question: str
    answer: str
    confidence: float = Field(..., description="Heuristic confidence score 0-100")
    sources: list[ChatSource] = Field(default_factory=list)
    model_used: str
    fallback_used: bool = False
    response_time_ms: int
    retrieved_count: int = 0
    created_at: Optional[datetime] = None


class ChatResponse(BaseModel):
    success: bool = True
    data: ChatAnswerData
    message: Optional[str] = None


class ChatHistoryItem(BaseModel):
    conversation_id: str
    project_id: str
    question: str
    answer: str
    confidence: float
    sources: list[Any] = Field(default_factory=list)
    model_used: str
    fallback_used: bool = False
    response_time_ms: int = 0
    created_at: datetime


class ChatHistoryResponse(BaseModel):
    success: bool = True
    data: list[ChatHistoryItem]
