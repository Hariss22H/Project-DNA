import os
import httpx
from dotenv import load_dotenv
from fastapi import HTTPException
from typing import Dict, List, Any, Tuple

# Load environment variables
load_dotenv()

BASE_URL = "https://api.github.com"

class GithubService:
    """Service to handle all GitHub API interactions."""

    def __init__(self):
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        # Add Authorization header if token is provided
        github_token = os.getenv("GITHUB_TOKEN")
        if github_token:
            self.headers["Authorization"] = f"Bearer {github_token}"

    def _get_owner_repo(self) -> Tuple[str, str]:
        """Helper to get and validate owner and repo from environment variables."""
        owner = os.getenv("GITHUB_OWNER")
        repo = os.getenv("GITHUB_REPO")
        if not owner or not repo:
            raise HTTPException(
                status_code=500, 
                detail="GITHUB_OWNER or GITHUB_REPO is not configured in .env"
            )
        return owner, repo

    async def _make_request(self, endpoint: str) -> Any:
        """Helper to make async requests to GitHub REST API."""
        owner, repo = self._get_owner_repo()
        url = f"{BASE_URL}/repos/{owner}/{repo}{endpoint}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            
            if response.status_code != 200:
                try:
                    detail = response.json().get("message", "GitHub API Error")
                except Exception:
                    detail = response.text
                raise HTTPException(status_code=response.status_code, detail=detail)
                
            return response.json()

    async def get_repository(self) -> Dict[str, Any]:
        """Fetch general repository information."""
        return await self._make_request("")

    async def get_readme(self) -> Dict[str, Any]:
        """Fetch the repository README."""
        return await self._make_request("/readme")

    async def get_tree(self, sha: str = "HEAD") -> Dict[str, Any]:
        """Fetch the repository file tree recursively."""
        return await self._make_request(f"/git/trees/{sha}?recursive=1")

    async def get_branches(self) -> List[Any]:
        """Fetch repository branches."""
        return await self._make_request("/branches")

    async def get_commits(self) -> List[Any]:
        """Fetch repository commits."""
        return await self._make_request("/commits")

    async def get_contributors(self) -> List[Any]:
        """Fetch repository contributors."""
        return await self._make_request("/contributors")

    async def get_languages(self) -> Dict[str, int]:
        """Fetch repository languages."""
        return await self._make_request("/languages")

    async def get_metadata(self) -> Dict[str, Any]:
        """Fetch additional repository metadata (aggregated info)."""
        repo_data = await self.get_repository()
        languages = await self.get_languages()
        
        return {
            "name": repo_data.get("name"),
            "owner": repo_data.get("owner", {}).get("login"),
            "description": repo_data.get("description"),
            "stars": repo_data.get("stargazers_count"),
            "forks": repo_data.get("forks_count"),
            "open_issues": repo_data.get("open_issues_count"),
            "languages": languages,
            "license": repo_data.get("license"),
            "default_branch": repo_data.get("default_branch")
        }

# Singleton instance
github_service = GithubService()
