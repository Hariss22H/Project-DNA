"""RAG pipeline for the AI Knowledge Twin."""

from __future__ import annotations

import time
from typing import Any, Optional

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.services.container import services
from app.services.embeddings.base import EmbeddingService
from app.services.llm.base import LLMResult
from app.services.llm.fallback import LLMFallbackManager
from app.services.prompts.rag import (
    INSUFFICIENT_CONTEXT_ANSWER,
    SYSTEM_PROMPT,
    UNRELATED_OR_EMPTY_RETRIEVAL_ANSWER,
    build_user_prompt,
)
from app.services.vectorstore.base import VectorSearchResult, VectorStore


class RAGService:
    def __init__(
        self,
        *,
        embeddings: Optional[EmbeddingService] = None,
        vector_store: Optional[VectorStore] = None,
        llm_manager: Optional[LLMFallbackManager] = None,
        top_k: Optional[int] = None,
        min_score: Optional[float] = None,
    ) -> None:
        settings = get_settings()
        self.embeddings = embeddings or services.embeddings
        self.vector_store = vector_store or services.vector_store
        self.llm_manager = llm_manager or services.llm_manager
        self.top_k = top_k or settings.rag_top_k
        self.min_score = min_score if min_score is not None else settings.rag_min_score

    async def ask(self, *, project_id: str, question: str) -> dict[str, Any]:
        started = time.perf_counter()
        cleaned_question = (question or "").strip()
        if not cleaned_question:
            raise AppError("Question cannot be empty", status_code=400, code="empty_question")
        if len(cleaned_question) > 4000:
            raise AppError("Question is too long", status_code=400, code="question_too_long")

        indexed = await self.vector_store.count_by_project(project_id)
        if indexed <= 0:
            raise AppError(
                "Project knowledge is not indexed yet. Run POST /api/projects/{id}/index first.",
                status_code=400,
                code="not_indexed",
            )

        query_vector = await self.embeddings.embed_query(cleaned_question)
        results = await self.vector_store.search(
            project_id=project_id,
            query_vector=query_vector,
            top_k=self.top_k,
        )
        relevant = [item for item in results if item.score >= self.min_score]

        # Never answer without retrieval.
        if not relevant:
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            return {
                "answer": UNRELATED_OR_EMPTY_RETRIEVAL_ANSWER,
                "confidence": 0.0,
                "sources": [],
                "model_used": "none",
                "fallback_used": False,
                "response_time_ms": elapsed_ms,
                "retrieved_count": 0,
            }

        context_blocks = [_format_context_block(idx, item) for idx, item in enumerate(relevant, start=1)]
        sources = [_serialize_source(item) for item in relevant]
        confidence = _compute_confidence(relevant, top_k=self.top_k)

        llm_result: LLMResult = await self.llm_manager.generate(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=build_user_prompt(
                question=cleaned_question,
                context_blocks=context_blocks,
            ),
        )

        answer = llm_result.content or INSUFFICIENT_CONTEXT_ANSWER
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return {
            "answer": answer,
            "confidence": confidence,
            "sources": sources,
            "model_used": llm_result.model_used,
            "fallback_used": llm_result.fallback_used,
            "response_time_ms": elapsed_ms,
            "retrieved_count": len(relevant),
        }


def _format_context_block(index: int, item: VectorSearchResult) -> str:
    payload = item.payload or {}
    title = payload.get("title") or payload.get("file_name") or "source"
    source_type = payload.get("source_type") or "chunk"
    text = (payload.get("text") or "").strip()
    return (
        f"[{index}] {title} ({source_type}) | score={item.score:.3f}\n"
        f"{text}"
    )


def _serialize_source(item: VectorSearchResult) -> dict[str, Any]:
    payload = item.payload or {}
    text = (payload.get("text") or "").strip()
    snippet = text[:280] + ("..." if len(text) > 280 else "")
    return {
        "id": item.id,
        "score": round(float(item.score), 4),
        "file_name": payload.get("file_name"),
        "title": payload.get("title") or payload.get("file_name"),
        "source_type": payload.get("source_type"),
        "chunk_index": payload.get("chunk_index"),
        "snippet": snippet,
    }


def _compute_confidence(results: list[VectorSearchResult], *, top_k: int) -> float:
    if not results:
        return 0.0
    avg_score = sum(item.score for item in results) / len(results)
    coverage = min(len(results) / max(top_k, 1), 1.0)
    # Heuristic score in 0–100 for dashboard/frontend display.
    confidence = (avg_score * 0.75 + coverage * 0.25) * 100
    return round(max(0.0, min(confidence, 98.0)), 1)
