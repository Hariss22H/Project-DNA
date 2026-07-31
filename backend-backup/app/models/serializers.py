"""Convert MongoDB documents into API-safe dictionaries."""

from __future__ import annotations

from typing import Any

from app.schemas.user import build_initials
from app.utils.ids import oid_str


def serialize_user(doc: dict[str, Any]) -> dict[str, Any]:
    full_name = doc.get("full_name", "")
    return {
        "id": oid_str(doc["_id"]),
        "full_name": full_name,
        "email": doc["email"],
        "role": doc.get("role", "Project manager"),
        "initials": doc.get("initials") or build_initials(full_name),
        "avatar_url": doc.get("avatar_url"),
        "created_at": doc["created_at"],
        "updated_at": doc["updated_at"],
    }


def serialize_project(doc: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": oid_str(doc["_id"]),
        "user_id": str(doc["user_id"]),
        "project_name": doc["project_name"],
        "description": doc.get("description") or "",
        "github_repository": doc.get("github_repository"),
        "project_status": doc.get("project_status", "created"),
        "created_at": doc["created_at"],
        "updated_at": doc["updated_at"],
    }


def serialize_repository(doc: dict[str, Any], *, include_readme: bool = True) -> dict[str, Any]:
    data = {
        "id": oid_str(doc["_id"]),
        "project_id": str(doc["project_id"]),
        "repository_url": doc["repository_url"],
        "owner": doc["owner"],
        "name": doc["name"],
        "full_name": doc["full_name"],
        "description": doc.get("description"),
        "default_branch": doc.get("default_branch", "main"),
        "structure": doc.get("structure") or [],
        "important_files": doc.get("important_files") or [],
        "languages": doc.get("languages") or {},
        "topics": doc.get("topics") or [],
        "commit_summary": doc.get("commit_summary") or [],
        "stars": int(doc.get("stars") or 0),
        "forks": int(doc.get("forks") or 0),
        "last_synced": doc["last_synced"],
        "created_at": doc["created_at"],
        "updated_at": doc["updated_at"],
    }
    if include_readme:
        data["readme_content"] = doc.get("readme_content")
    return data


def serialize_document(doc: dict[str, Any], *, include_text: bool = False) -> dict[str, Any]:
    data = {
        "id": oid_str(doc["_id"]),
        "project_id": str(doc["project_id"]),
        "file_name": doc["file_name"],
        "file_type": doc["file_type"],
        "file_size": int(doc.get("file_size") or 0),
        "storage_path": doc.get("storage_path") or "",
        "char_count": int(doc.get("char_count") or 0),
        "page_count": doc.get("page_count"),
        "status": doc.get("status", "extracted"),
        "is_architecture": bool(doc.get("is_architecture")),
        "upload_time": doc.get("upload_time") or doc["created_at"],
        "created_at": doc["created_at"],
        "updated_at": doc["updated_at"],
    }
    if include_text:
        data["extracted_text"] = doc.get("extracted_text") or ""
        data["metadata"] = doc.get("metadata") or {}
    return data
