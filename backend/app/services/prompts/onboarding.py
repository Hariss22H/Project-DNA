"""Prompt templates for the AI Project Onboarding Assistant."""

from __future__ import annotations

ONBOARDING_SYSTEM_PROMPT = """You are Project DNA's AI Project Onboarding Assistant.

Your job is to create a complete onboarding briefing for a brand-new developer
using ONLY the provided project knowledge context.

Rules:
1. Ground every claim in the retrieved context, repository summary, documents, graph, timeline, or risks.
2. Never invent APIs, modules, technologies, or risks that are not supported by the context.
3. If a section lacks enough information, write exactly:
   "This information was not found in the indexed project knowledge."
4. Be practical, concise, and structured for a hackathon demo.
5. Prefer bullet points and short paragraphs.
6. Mention real source file names when helpful (README.md, spec.md, etc.).
"""

ONBOARDING_SECTION_ORDER = [
    "Welcome",
    "Project Purpose",
    "Architecture Overview",
    "Technology Stack",
    "Major Modules",
    "Important APIs",
    "Project Workflow",
    "Important Documents",
    "Current Project Risks",
    "Suggested Learning Path",
    "Estimated Onboarding Time",
    "First Tasks Recommendation",
]


def build_onboarding_user_prompt(
    *,
    project_name: str,
    retrieved_context: str,
    project_summary: str,
) -> str:
    sections = "\n".join(f"# {title}" for title in ONBOARDING_SECTION_ORDER)
    return (
        f"Create an onboarding briefing for project: {project_name}\n\n"
        "Use these exact Markdown H1 section headings in this order:\n"
        f"{sections}\n\n"
        "Project metadata and intelligence summary:\n"
        f"{project_summary.strip() or '(none)'}\n\n"
        "Retrieved Knowledge Twin context:\n"
        f"{retrieved_context.strip() or '(no retrieved chunks)'}\n\n"
        "Write the full briefing now."
    )
