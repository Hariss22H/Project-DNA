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
        if "onboarding briefing" in user_prompt.lower() or "Onboarding Assistant" in system_prompt:
            answer = _fake_onboarding_briefing(user_prompt)
        else:
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


def _fake_onboarding_briefing(user_prompt: str) -> str:
    snippet = user_prompt.strip()[:320].replace("\n", " ")
    return (
        "# Welcome\n\n"
        "Welcome aboard. This briefing was generated from indexed project knowledge.\n\n"
        "# Project Purpose\n\n"
        f"Based on retrieved context: {snippet}\n\n"
        "# Architecture Overview\n\n"
        "- Frontend, Backend, Database, and AI components are described in indexed sources.\n\n"
        "# Technology Stack\n\n"
        "Technologies detected from repository languages and documentation.\n\n"
        "# Major Modules\n\n"
        "Modules referenced in project knowledge (auth, dashboard, chat, risks, graph).\n\n"
        "# Important APIs\n\n"
        "API details found in retrieved documentation chunks.\n\n"
        "# Project Workflow\n\n"
        "GitHub + Documents → Extraction → Chunking → Embeddings → Qdrant → RAG → Knowledge Twin → Dashboard\n\n"
        "# Important Documents\n\n"
        "Start with README and any architecture / API docs present in indexed knowledge.\n\n"
        "# Current Project Risks\n\n"
        "See risk summaries included in the project intelligence context.\n\n"
        "# Suggested Learning Path\n\n"
        "1. Read README\n2. Understand Architecture\n3. Explore Backend\n4. Explore Frontend\n"
        "5. Review APIs\n6. Understand AI Pipeline\n7. Review Risks\n\n"
        "# Estimated Onboarding Time\n\n"
        "Approximately 30–60 minutes for a first pass through the Knowledge Twin briefing.\n\n"
        "# First Tasks Recommendation\n\n"
        "- Improve documentation gaps\n- Review authentication\n- Explore dashboard APIs\n"
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
