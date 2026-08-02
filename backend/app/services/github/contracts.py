"""GitHub service contracts owned by Member 1 (API/orchestration).

Member 3 implements `GitHubService` without changing API routes.
Swap the concrete class via the service registry in `app.services.registry`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

from pydantic import BaseModel, Field, HttpUrl


class GitHubCommitSummary(BaseModel):
    sha: str
    message: str
    author: Optional[str] = None
    date: Optional[str] = None


class GitHubRepositoryData(BaseModel):
    """Normalized repository payload returned by the GitHub connector."""

    repository_url: str
    full_name: str
    description: Optional[str] = None
    default_branch: str = "main"
    readme_content: Optional[str] = None
    structure: list[str] = Field(default_factory=list)
    important_files: list[str] = Field(default_factory=list)
    languages: dict[str, int] = Field(default_factory=dict)
    topics: list[str] = Field(default_factory=list)
    commit_summary: list[GitHubCommitSummary] = Field(default_factory=list)
    stars: int = 0
    forks: int = 0
    raw_metadata: dict[str, Any] = Field(default_factory=dict)


class GitHubService(ABC):
    """Interface for public GitHub repository intelligence (Member 3)."""

    @abstractmethod
    async def validate_repository(self, repository_url: str) -> bool:
        """Return True when the URL points to an accessible public repository."""

    @abstractmethod
    async def fetch_repository(self, repository_url: str) -> GitHubRepositoryData:
        """Fetch README, structure, commits, and metadata for indexing."""
