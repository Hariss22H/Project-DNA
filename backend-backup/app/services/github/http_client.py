"""GitHub REST API connector (default implementation; Member 3 may replace)."""

from __future__ import annotations

import base64
import logging
import re
from typing import Any, Optional
from urllib.parse import urlparse

import httpx

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.services.github.base import GitHubCommitSummary, GitHubRepositoryData, GitHubService

logger = logging.getLogger(__name__)

GITHUB_URL_RE = re.compile(
    r"^https?://(www\.)?github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?/?$",
    re.IGNORECASE,
)


class HttpGitHubService(GitHubService):
    """Fetches public repository metadata via the GitHub REST API."""

    def __init__(self, *, token: Optional[str] = None, timeout: float = 20.0) -> None:
        settings = get_settings()
        self._token = token if token is not None else settings.github_token
        self._timeout = timeout

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "Project-DNA-Hackathon",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    @staticmethod
    def parse_owner_repo(repository_url: str) -> tuple[str, str]:
        match = GITHUB_URL_RE.match(repository_url.strip())
        if not match:
            raise AppError(
                "Invalid GitHub repository URL. Expected https://github.com/{owner}/{repo}",
                status_code=400,
                code="invalid_github_url",
            )
        return match.group("owner"), match.group("repo")

    async def validate_repository(self, repository_url: str) -> bool:
        try:
            owner, repo = self.parse_owner_repo(repository_url)
        except AppError:
            return False

        async with httpx.AsyncClient(timeout=self._timeout, headers=self._headers()) as client:
            response = await client.get(f"https://api.github.com/repos/{owner}/{repo}")
            return response.status_code == 200

    async def fetch_repository(self, repository_url: str) -> GitHubRepositoryData:
        owner, repo = self.parse_owner_repo(repository_url)
        async with httpx.AsyncClient(timeout=self._timeout, headers=self._headers()) as client:
            meta_resp = await client.get(f"https://api.github.com/repos/{owner}/{repo}")
            if meta_resp.status_code == 404:
                raise AppError(
                    "GitHub repository not found or is private",
                    status_code=404,
                    code="github_repo_not_found",
                )
            if meta_resp.status_code != 200:
                raise AppError(
                    f"GitHub API error while fetching repository ({meta_resp.status_code})",
                    status_code=502,
                    code="github_api_error",
                    details=meta_resp.text[:300],
                )

            meta = meta_resp.json()
            default_branch = meta.get("default_branch") or "main"
            full_name = meta.get("full_name") or f"{owner}/{repo}"

            readme = await self._fetch_readme(client, owner, repo)
            structure, important_files = await self._fetch_structure(
                client, owner, repo, default_branch
            )
            languages = await self._fetch_json(
                client, f"https://api.github.com/repos/{owner}/{repo}/languages"
            )
            commits = await self._fetch_json(
                client,
                f"https://api.github.com/repos/{owner}/{repo}/commits",
                params={"per_page": 10},
            )

        commit_summary: list[GitHubCommitSummary] = []
        if isinstance(commits, list):
            for item in commits[:10]:
                commit = item.get("commit") or {}
                author = (commit.get("author") or {}).get("name")
                date = (commit.get("author") or {}).get("date")
                commit_summary.append(
                    GitHubCommitSummary(
                        sha=(item.get("sha") or "")[:12],
                        message=(commit.get("message") or "").split("\n")[0][:200],
                        author=author,
                        date=date,
                    )
                )

        return GitHubRepositoryData(
            repository_url=meta.get("html_url") or f"https://github.com/{full_name}",
            owner=owner,
            name=repo,
            full_name=full_name,
            description=meta.get("description"),
            default_branch=default_branch,
            readme_content=readme,
            structure=structure,
            important_files=important_files,
            languages=languages if isinstance(languages, dict) else {},
            topics=meta.get("topics") or [],
            commit_summary=commit_summary,
            stars=int(meta.get("stargazers_count") or 0),
            forks=int(meta.get("forks_count") or 0),
            raw={
                "private": meta.get("private"),
                "language": meta.get("language"),
                "homepage": meta.get("homepage"),
            },
        )

    async def _fetch_readme(
        self, client: httpx.AsyncClient, owner: str, repo: str
    ) -> Optional[str]:
        response = await client.get(f"https://api.github.com/repos/{owner}/{repo}/readme")
        if response.status_code != 200:
            return None
        payload = response.json()
        content = payload.get("content")
        encoding = payload.get("encoding")
        if not content:
            return None
        if encoding == "base64":
            try:
                return base64.b64decode(content).decode("utf-8", errors="replace")
            except Exception:  # noqa: BLE001
                logger.warning("Failed to decode README for %s/%s", owner, repo)
                return None
        return str(content)

    async def _fetch_structure(
        self,
        client: httpx.AsyncClient,
        owner: str,
        repo: str,
        branch: str,
    ) -> tuple[list[str], list[str]]:
        response = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}",
            params={"recursive": "1"},
        )
        if response.status_code != 200:
            return [], []

        tree = response.json().get("tree") or []
        paths = [item.get("path") for item in tree if item.get("path")]
        # Keep payload small for hackathon demo storage.
        structure = paths[:200]
        important_names = {
            "readme.md",
            "readme",
            "package.json",
            "requirements.txt",
            "pyproject.toml",
            "dockerfile",
            "docker-compose.yml",
            "architecture.md",
            "docs/architecture.md",
        }
        important_files = [
            path
            for path in structure
            if path.lower().split("/")[-1] in important_names
            or path.lower() in important_names
        ][:40]
        return structure, important_files

    async def _fetch_json(
        self,
        client: httpx.AsyncClient,
        url: str,
        params: Optional[dict[str, Any]] = None,
    ) -> Any:
        response = await client.get(url, params=params)
        if response.status_code != 200:
            return [] if "commits" in url else {}
        return response.json()
