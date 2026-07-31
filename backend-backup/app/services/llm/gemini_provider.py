"""Gemini chat provider (fallback)."""

from __future__ import annotations

import logging
from typing import Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.services.llm.base import LLMProvider, LLMResult

logger = logging.getLogger(__name__)


class GeminiProvider(LLMProvider):
    name = "gemini"

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.2,
    ) -> None:
        settings = get_settings()
        self._api_key = api_key if api_key is not None else settings.gemini_api_key
        self._model = model or settings.gemini_fallback_model
        self._temperature = temperature

    async def generate(self, *, system_prompt: str, user_prompt: str) -> LLMResult:
        if not self._api_key:
            raise AppError(
                "GEMINI_API_KEY is not configured",
                status_code=500,
                code="gemini_not_configured",
            )
        try:
            llm = ChatGoogleGenerativeAI(
                google_api_key=self._api_key,
                model=self._model,
                temperature=self._temperature,
            )
            response = await llm.ainvoke(
                [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt),
                ]
            )
            content = response.content if isinstance(response.content, str) else str(response.content)
            return LLMResult(
                content=content.strip(),
                model_used=self._model,
                provider=self.name,
            )
        except AppError:
            raise
        except Exception as exc:  # noqa: BLE001
            logger.warning("Gemini generation failed: %s", exc)
            raise AppError(
                "Gemini generation failed",
                status_code=502,
                code="gemini_failed",
                details=str(exc),
            ) from exc
