"""Prompt templates."""

from app.services.prompts.rag import (
    INSUFFICIENT_CONTEXT_ANSWER,
    SYSTEM_PROMPT,
    UNRELATED_OR_EMPTY_RETRIEVAL_ANSWER,
    build_user_prompt,
)

__all__ = [
    "SYSTEM_PROMPT",
    "build_user_prompt",
    "INSUFFICIENT_CONTEXT_ANSWER",
    "UNRELATED_OR_EMPTY_RETRIEVAL_ANSWER",
]
