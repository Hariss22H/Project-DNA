"""LLM provider contracts."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMResult:
    content: str
    model_used: str
    provider: str
    attempts: int = 1
    fallback_used: bool = False


class LLMProvider(ABC):
    name: str

    @abstractmethod
    async def generate(self, *, system_prompt: str, user_prompt: str) -> LLMResult:
        """Generate a completion from system + user prompts."""
