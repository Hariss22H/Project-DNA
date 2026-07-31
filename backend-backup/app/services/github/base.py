"""GitHub service contract owned by Member 1 (API/orchestration).

Member 3 implements this interface. The API layer must only depend on
`GitHubService`, never on a concrete connector.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

from pydantic import BaseModel, Field


class GitHubCommitSummary(BaseModel):
    sha: str
    message: str
    author: Optional[str] = None
    date: Optional[str] = None


class GitHubRepositoryData(BaseModel):
    """Normalized repository payload returned by any GitHub connector."""

    repository_url: str
    owner: str
    name: str
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
    raw: dict[str, Any] = Field(default_factory=dict)


class GitHubService(ABC):
    """Abstract GitHub connector. Swap implementations without touching routes."""

    @abstractmethod
    async def validate_repository(self, repository_url: str) -> bool:
        """Return True when the public repository URL is reachable."""

    @abstractmethod
    async def fetch_repository(self, repository_url: str) -> GitHubRepositoryData:
        """Fetch README, metadata, structure, and commit summary."""
