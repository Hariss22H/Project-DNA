from fastapi import APIRouter, Query
from typing import Dict, List, Any
from app.services.github_service import github_service

router = APIRouter(prefix="/github", tags=["GitHub"])

@router.get("/repository", response_model=Dict[str, Any])
async def get_repository():
    """
    Get general repository information.
    """
    return await github_service.get_repository()

@router.get("/readme", response_model=Dict[str, Any])
async def get_readme():
    """
    Get the repository README file details and content.
    """
    return await github_service.get_readme()

@router.get("/tree", response_model=Dict[str, Any])
async def get_tree(sha: str = Query("HEAD", description="Branch name or commit SHA")):
    """
    Get the repository file tree recursively.
    """
    return await github_service.get_tree(sha)

@router.get("/branches", response_model=List[Any])
async def get_branches():
    """
    Get all repository branches.
    """
    return await github_service.get_branches()

@router.get("/commits", response_model=List[Any])
async def get_commits():
    """
    Get the repository commit history.
    """
    return await github_service.get_commits()

@router.get("/contributors", response_model=List[Any])
async def get_contributors():
    """
    Get the repository contributors.
    """
    return await github_service.get_contributors()

@router.get("/languages", response_model=Dict[str, int])
async def get_languages():
    """
    Get the repository programming languages and their byte sizes.
    """
    return await github_service.get_languages()

@router.get("/metadata", response_model=Dict[str, Any])
async def get_metadata():
    """
    Get additional repository metadata including aggregated stats.
    """
    return await github_service.get_metadata()
