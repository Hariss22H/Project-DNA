"""AI Knowledge Twin chat APIs."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.auth.deps import CurrentUser
from app.core.dependencies import get_db
from app.schemas.chat import (
    ChatAnswerData,
    ChatHistoryItem,
    ChatHistoryResponse,
    ChatRequest,
    ChatResponse,
    ChatSource,
)
from app.services.chat_service import ChatService

router = APIRouter(tags=["AI Chat"])


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Ask the AI Knowledge Twin a project question",
)
async def chat(
    payload: ChatRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> ChatResponse:
    data = await ChatService(db).ask(
        user_id=current_user["id"],
        project_id=payload.project_id,
        question=payload.question,
    )
    return ChatResponse(
        data=ChatAnswerData(
            conversation_id=data.get("conversation_id"),
            project_id=data["project_id"],
            question=data["question"],
            answer=data["answer"],
            confidence=data["confidence"],
            sources=[ChatSource(**source) for source in data.get("sources") or []],
            model_used=data["model_used"],
            fallback_used=data.get("fallback_used", False),
            response_time_ms=data["response_time_ms"],
            retrieved_count=data.get("retrieved_count", 0),
            created_at=data.get("created_at"),
        ),
        message="AI response generated",
    )


@router.get(
    "/projects/{project_id}/chat",
    response_model=ChatHistoryResponse,
    summary="List recent AI chat history for a project",
)
async def chat_history(
    project_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
    limit: int = Query(default=50, ge=1, le=100),
) -> ChatHistoryResponse:
    items = await ChatService(db).list_conversations(
        user_id=current_user["id"],
        project_id=project_id,
        limit=limit,
    )
    return ChatHistoryResponse(data=[ChatHistoryItem(**item) for item in items])
