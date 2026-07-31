"""OpenAI chat provider (primary)."""

from __future__ import annotations

import logging
from typing import Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.services.llm.base import LLMProvider, LLMResult

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.2,
    ) -> None:
        settings = get_settings()
        self._api_key = api_key if api_key is not None else settings.openai_api_key
        self._model = model or settings.openai_chat_model
        self._temperature = temperature

    async def generate(self, *, system_prompt: str, user_prompt: str) -> LLMResult:
        if not self._api_key:
            raise AppError(
                "OPENAI_API_KEY is not configured",
                status_code=500,
                code="openai_not_configured",
            )
        try:
            llm = ChatOpenAI(
                api_key=self._api_key,
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
            logger.warning("OpenAI generation failed: %s", exc)
            raise AppError(
                "OpenAI generation failed",
                status_code=502,
                code="openai_failed",
                details=str(exc),
            ) from exc
