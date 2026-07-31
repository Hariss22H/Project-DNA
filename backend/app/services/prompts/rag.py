"""Prompt templates for the AI Knowledge Twin."""

from __future__ import annotations

SYSTEM_PROMPT = """You are Project DNA's AI Knowledge Twin for a software project.

Rules you must follow:
1. Answer ONLY using the retrieved project context provided by the user message.
2. Never invent APIs, files, architecture, or decisions that are not supported by the context.
3. If the context is insufficient, say exactly:
   "I couldn't find enough project information to answer this."
4. Be concise, technical, and practical.
5. Mention supporting source titles/file names when possible.
6. If the question is unrelated to the project context, politely refuse and ask for a project-specific question.
"""


def build_user_prompt(*, question: str, context_blocks: list[str]) -> str:
    context = "\n\n".join(context_blocks) if context_blocks else "(no context)"
    return (
        f"Question:\n{question.strip()}\n\n"
        f"Context:\n{context}\n\n"
        "Answer using only the context above."
    )


INSUFFICIENT_CONTEXT_ANSWER = "I couldn't find enough project information to answer this."
UNRELATED_OR_EMPTY_RETRIEVAL_ANSWER = (
    "I couldn't find enough project information to answer this. "
    "Try asking about this project's architecture, documents, APIs, or repository content."
)
