"""Semantic-ish text chunking for RAG indexing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import tiktoken

from app.core.config import get_settings


@dataclass
class TextChunk:
    index: int
    text: str
    token_count: int
    start_token: int
    end_token: int


class ChunkingService:
    """Paragraph-aware chunker with token windows and overlap."""

    def __init__(
        self,
        *,
        chunk_size_tokens: Optional[int] = None,
        chunk_overlap_tokens: Optional[int] = None,
        encoding_name: str = "cl100k_base",
    ) -> None:
        settings = get_settings()
        self.chunk_size = max(chunk_size_tokens or settings.chunk_size_tokens, 50)
        self.chunk_overlap = chunk_overlap_tokens or settings.chunk_overlap_tokens
        self.chunk_overlap = max(0, min(self.chunk_overlap, self.chunk_size // 2))
        try:
            self._encoding = tiktoken.get_encoding(encoding_name)
        except Exception:  # noqa: BLE001
            self._encoding = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        return len(self._encoding.encode(text or ""))

    def chunk_text(self, text: str) -> list[TextChunk]:
        cleaned = (text or "").strip()
        if not cleaned:
            return []

        # Build token stream while keeping decodeable windows.
        tokens = self._encoding.encode(cleaned)
        if not tokens:
            return []

        step = max(self.chunk_size - self.chunk_overlap, 1)
        chunks: list[TextChunk] = []
        start = 0
        while start < len(tokens):
            end = min(start + self.chunk_size, len(tokens))
            window = tokens[start:end]
            chunk_text = self._encoding.decode(window).strip()
            if chunk_text:
                chunks.append(
                    TextChunk(
                        index=len(chunks),
                        text=chunk_text,
                        token_count=len(window),
                        start_token=start,
                        end_token=end,
                    )
                )
            if end >= len(tokens):
                break
            start += step

        # Prefer paragraph boundaries when text is small enough for one/two chunks.
        if len(tokens) <= self.chunk_size:
            return [
                TextChunk(
                    index=0,
                    text=cleaned,
                    token_count=len(tokens),
                    start_token=0,
                    end_token=len(tokens),
                )
            ]

        return chunks or [
            TextChunk(
                index=0,
                text=cleaned,
                token_count=self.count_tokens(cleaned),
                start_token=0,
                end_token=self.count_tokens(cleaned),
            )
        ]
