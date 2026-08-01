"""RAG pipeline for the AI Knowledge Twin."""

from __future__ import annotations

import logging
import time
from typing import Any, Optional

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.services.container import services
from app.services.embeddings.base import EmbeddingService
from app.services.llm.base import LLMResult
from app.services.llm.fallback import LLMFallbackManager
from app.services.prompts.rag import (
    BEST_EFFORT_SYSTEM_PROMPT,
    INSUFFICIENT_CONTEXT_ANSWER,
    SYSTEM_PROMPT,
    UNRELATED_OR_EMPTY_RETRIEVAL_ANSWER,
    build_user_prompt,
)
from app.services.vectorstore.base import VectorSearchResult, VectorStore

logger = logging.getLogger(__name__)


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
        # Over-fetch a little so we can demote thin metadata while keeping useful docs.
        raw_results = await self.vector_store.search(
            project_id=project_id,
            query_vector=query_vector,
            top_k=max(self.top_k * 2, self.top_k),
        )
        relevant = _select_relevant_chunks(
            raw_results,
            min_score=self.min_score,
            top_k=self.top_k,
        )

        filenames = [
            str((item.payload or {}).get("file_name") or (item.payload or {}).get("title") or "unknown")
            for item in relevant
        ]
        scores = [round(float(item.score), 4) for item in relevant]
        logger.info(
            "RAG retrieval project_id=%s retrieved=%s scores=%s files=%s min_score=%s indexed=%s",
            project_id,
            len(relevant),
            scores,
            filenames,
            self.min_score,
            indexed,
        )

        # Never answer without retrieval.
        if not relevant:
            logger.info(
                "RAG hard-refuse project_id=%s reason=no_chunks_above_threshold raw_top_scores=%s",
                project_id,
                [round(float(item.score), 4) for item in raw_results[:5]],
            )
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
        user_prompt = build_user_prompt(
            question=cleaned_question,
            context_blocks=context_blocks,
        )
        logger.info(
            "RAG prompt project_id=%s prompt_chars=%s context_blocks=%s",
            project_id,
            len(user_prompt),
            len(context_blocks),
        )

        llm_result: LLMResult = await self.llm_manager.generate(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )
        answer = (llm_result.content or "").strip() or INSUFFICIENT_CONTEXT_ANSWER
        model_used = llm_result.model_used
        fallback_used = llm_result.fallback_used

        if _is_refusal(answer) and _has_groundable_content(relevant):
            logger.info(
                "RAG soft-refuse overridden project_id=%s retry=best_effort files=%s",
                project_id,
                filenames,
            )
            retry: LLMResult = await self.llm_manager.generate(
                system_prompt=BEST_EFFORT_SYSTEM_PROMPT,
                user_prompt=user_prompt,
            )
            retry_answer = (retry.content or "").strip()
            if retry_answer and not _is_refusal(retry_answer):
                answer = retry_answer
                model_used = retry.model_used
                fallback_used = fallback_used or retry.fallback_used
            else:
                answer = _extractive_answer(cleaned_question, relevant)
                model_used = f"{model_used}+extractive"
                confidence = max(confidence * 0.85, 25.0)

        if _is_refusal(answer) and not _has_groundable_content(relevant):
            answer = UNRELATED_OR_EMPTY_RETRIEVAL_ANSWER
            confidence = min(confidence, 15.0)

        elapsed_ms = int((time.perf_counter() - started) * 1000)
        logger.info(
            "RAG complete project_id=%s retrieved=%s confidence=%s model=%s refuse=%s elapsed_ms=%s",
            project_id,
            len(relevant),
            confidence,
            model_used,
            _is_refusal(answer),
            elapsed_ms,
        )
        return {
            "answer": answer,
            "confidence": confidence,
            "sources": sources,
            "model_used": model_used,
            "fallback_used": fallback_used,
            "response_time_ms": elapsed_ms,
            "retrieved_count": len(relevant),
        }


def _select_relevant_chunks(
    results: list[VectorSearchResult],
    *,
    min_score: float,
    top_k: int,
) -> list[VectorSearchResult]:
    filtered = [item for item in results if item.score >= min_score]
    if not filtered and results:
        # Soft fallback: keep the best hit if it is not extremely weak.
        best = max(results, key=lambda item: item.score)
        if best.score >= max(min_score - 0.05, 0.0):
            filtered = [best]

    substantive = [
        item
        for item in filtered
        if (item.payload or {}).get("source_type") != "repository_meta"
    ]
    meta = [
        item
        for item in filtered
        if (item.payload or {}).get("source_type") == "repository_meta"
    ]
    # Prefer README/docs/code over thin repository_metadata.txt.
    ranked = substantive + meta
    return ranked[:top_k]


def _has_groundable_content(results: list[VectorSearchResult]) -> bool:
    for item in results:
        payload = item.payload or {}
        text = (payload.get("text") or "").strip()
        source_type = payload.get("source_type")
        if source_type == "repository_meta":
            continue
        if len(text) >= 40:
            return True
    # Metadata-only retrieval can still help for high-level repo questions.
    return any(len(((item.payload or {}).get("text") or "").strip()) >= 80 for item in results)


def _is_refusal(answer: str) -> bool:
    normalized = (answer or "").strip().lower()
    if not normalized:
        return True
    return (
        normalized.startswith("i couldn't find enough")
        or "couldn't find enough project information" in normalized
    )


def _extractive_answer(question: str, results: list[VectorSearchResult]) -> str:
    points: list[str] = []
    for item in results[:4]:
        payload = item.payload or {}
        if payload.get("source_type") == "repository_meta" and len(points) > 0:
            continue
        file_name = payload.get("file_name") or payload.get("title") or "source"
        text = " ".join((payload.get("text") or "").split())
        if len(text) < 40:
            continue
        snippet = text[:420] + ("..." if len(text) > 420 else "")
        points.append(f"- From **{file_name}**: {snippet}")

    if not points:
        return INSUFFICIENT_CONTEXT_ANSWER

    return (
        f"Based on the retrieved project knowledge for “{question.strip()}”:\n\n"
        + "\n".join(points)
        + "\n\nAsk a follow-up if you want more detail from a specific source."
    )


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
    substantive_ratio = sum(
        1 for item in results if (item.payload or {}).get("source_type") != "repository_meta"
    ) / len(results)
    confidence = (avg_score * 0.65 + coverage * 0.20 + substantive_ratio * 0.15) * 100
    return round(max(0.0, min(confidence, 98.0)), 1)
