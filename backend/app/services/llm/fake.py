"""Deterministic fake LLM for tests."""

from __future__ import annotations

from app.services.llm.base import LLMProvider, LLMResult
from app.services.llm.fallback import LLMFallbackManager


class FakeLLMProvider(LLMProvider):
    name = "fake"

    def __init__(self, *, model_name: str = "fake-llm", fail: bool = False) -> None:
        self._model_name = model_name
        self._fail = fail

    async def generate(self, *, system_prompt: str, user_prompt: str) -> LLMResult:
        if self._fail:
            raise RuntimeError(f"{self._model_name} forced failure")
        # Echo a grounded-looking answer using retrieved context markers.
        snippet = user_prompt
        if "Context:" in user_prompt:
            snippet = user_prompt.split("Context:", 1)[1].strip()[:280]
        answer = (
            "Based on the retrieved project knowledge: "
            f"{snippet if snippet else 'No extra detail available.'}"
        )
        return LLMResult(
            content=answer,
            model_used=self._model_name,
            provider=self.name,
        )


def build_fake_llm_manager(
    *,
    primary_fail: bool = False,
    fallback_fail: bool = False,
) -> LLMFallbackManager:
    return LLMFallbackManager(
        primary=FakeLLMProvider(model_name="fake-openai", fail=primary_fail),
        fallback=FakeLLMProvider(model_name="fake-gemini", fail=fallback_fail),
        primary_retries=2 if primary_fail else 1,
    )
