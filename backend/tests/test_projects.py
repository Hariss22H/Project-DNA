"""Phase 1 project CRUD API tests."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


async def _auth_header(client: AsyncClient, email: str = "dev@company.com") -> dict[str, str]:
    response = await client.post(
        "/api/auth/register",
        json={
            "full_name": "Dev User",
            "email": email,
            "password": "secret123",
            "role": "Organization admin",
        },
    )
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_project_crud_flow(app_client: AsyncClient):
    headers = await _auth_header(app_client)

    created = await app_client.post(
        "/api/projects",
        headers=headers,
        json={"project_name": "Nova Web", "description": "Demo project"},
    )
    assert created.status_code == 201
    project = created.json()["data"]
    project_id = project["id"]
    assert project["project_name"] == "Nova Web"
    assert project["project_status"] == "created"

    listed = await app_client.get("/api/projects", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()["data"]) == 1

    fetched = await app_client.get(f"/api/projects/{project_id}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["data"]["id"] == project_id

    updated = await app_client.put(
        f"/api/projects/{project_id}",
        headers=headers,
        json={"description": "Updated description", "project_status": "ready"},
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["description"] == "Updated description"
    assert updated.json()["data"]["project_status"] == "ready"

    deleted = await app_client.delete(f"/api/projects/{project_id}", headers=headers)
    assert deleted.status_code == 200
    assert deleted.json()["success"] is True

    missing = await app_client.get(f"/api/projects/{project_id}", headers=headers)
    assert missing.status_code == 404


@pytest.mark.asyncio
async def test_projects_require_auth(app_client: AsyncClient):
    response = await app_client.get("/api/projects")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_user_cannot_access_another_users_project(app_client: AsyncClient):
    owner_headers = await _auth_header(app_client, email="owner@company.com")
    created = await app_client.post(
        "/api/projects",
        headers=owner_headers,
        json={"project_name": "Private", "description": ""},
    )
    project_id = created.json()["data"]["id"]

    other_headers = await _auth_header(app_client, email="other@company.com")
    response = await app_client.get(f"/api/projects/{project_id}", headers=other_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_openapi_includes_phase1_paths(app_client: AsyncClient):
    schema = (await app_client.get("/openapi.json")).json()
    paths = schema["paths"]
    assert "/api/auth/register" in paths
    assert "/api/auth/login" in paths
    assert "/api/auth/me" in paths
    assert "/api/projects" in paths
    assert "/api/projects/{project_id}" in paths
