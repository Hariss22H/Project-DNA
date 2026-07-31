"""GitHub repository API schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.services.github.base import GitHubCommitSummary


class ConnectGitHubRequest(BaseModel):
    repository_url: str = Field(
        ...,
        examples=["https://github.com/tiangolo/fastapi"],
        description="Public GitHub repository URL",
    )


class RepositoryPublic(BaseModel):
    id: str
    project_id: str
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
    last_synced: datetime
    created_at: datetime
    updated_at: datetime


class RepositoryResponse(BaseModel):
    success: bool = True
    data: RepositoryPublic
    message: Optional[str] = None
