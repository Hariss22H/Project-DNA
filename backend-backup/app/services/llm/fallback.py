"""LLM fallback manager: OpenAI → retry → Gemini."""

from __future__ import annotations

import logging
from typing import Optional

from app.core.exceptions import AppError
from app.services.llm.base import LLMProvider, LLMResult
from app.services.llm.gemini_provider import GeminiProvider
from app.services.llm.openai_provider import OpenAIProvider

logger = logging.getLogger(__name__)


class LLMFallbackManager:
    """Reusable chat completion manager with automatic provider failover."""

    def __init__(
        self,
        *,
        primary: Optional[LLMProvider] = None,
        fallback: Optional[LLMProvider] = None,
        primary_retries: int = 2,
    ) -> None:
        self.primary = primary or OpenAIProvider()
        self.fallback = fallback or GeminiProvider()
        self.primary_retries = max(primary_retries, 1)

    async def generate(self, *, system_prompt: str, user_prompt: str) -> LLMResult:
        attempts = 0
        last_error: Optional[Exception] = None

        for attempt in range(1, self.primary_retries + 1):
            attempts += 1
            try:
                result = await self.primary.generate(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                )
                result.attempts = attempts
                result.fallback_used = False
                return result
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                logger.warning(
                    "Primary LLM attempt %s/%s failed: %s",
                    attempt,
                    self.primary_retries,
                    exc,
                )

        try:
            attempts += 1
            result = await self.fallback.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
            result.attempts = attempts
            result.fallback_used = True
            logger.info("Served response via Gemini fallback (%s)", result.model_used)
            return result
        except Exception as exc:  # noqa: BLE001
            logger.exception("All LLM providers failed")
            raise AppError(
                "AI service unavailable. Please try again shortly.",
                status_code=503,
                code="llm_unavailable",
                details={
                    "primary_error": str(last_error) if last_error else None,
                    "fallback_error": str(exc),
                },
            ) from exc
