"""AI Project Onboarding Assistant tests."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.services.onboarding_service import parse_briefing_sections


async def _ready_project(client: AsyncClient) -> tuple[dict[str, str], str]:
    register = await client.post(
        "/api/auth/register",
        json={
            "full_name": "Onboard User",
            "email": "onboard@company.com",
            "password": "secret123",
        },
    )
    headers = {"Authorization": f"Bearer {register.json()['data']['access_token']}"}
    project = await client.post(
        "/api/projects",
        headers=headers,
        json={"project_name": "Onboard Project", "description": "Knowledge Twin demo"},
    )
    project_id = project.json()["data"]["id"]
    await client.post(
        f"/api/projects/{project_id}/github",
        headers=headers,
        json={"repository_url": "https://github.com/acme/nova-web"},
    )
    indexed = await client.post(f"/api/projects/{project_id}/index", headers=headers)
    assert indexed.status_code == 200
    return headers, project_id


@pytest.mark.asyncio
async def test_onboarding_requires_index(app_client: AsyncClient):
    register = await app_client.post(
        "/api/auth/register",
        json={
            "full_name": "No Index Onboard",
            "email": "noindex-onboard@company.com",
            "password": "secret123",
        },
    )
    headers = {"Authorization": f"Bearer {register.json()['data']['access_token']}"}
    project = await app_client.post(
        "/api/projects",
        headers=headers,
        json={"project_name": "Empty Onboard", "description": ""},
    )
    project_id = project.json()["data"]["id"]
    response = await app_client.post(
        f"/api/projects/{project_id}/onboarding/briefing",
        headers=headers,
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] in {"not_indexed", "insufficient_knowledge"}


@pytest.mark.asyncio
async def test_onboarding_briefing_structured(app_client: AsyncClient):
    headers, project_id = await _ready_project(app_client)
    response = await app_client.post(
        f"/api/projects/{project_id}/onboarding/briefing",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["project_id"] == project_id
    assert data["title"].startswith("AI Onboarding Briefing")
    assert data["markdown"]
    assert data["retrieved_count"] > 0
    assert data["model_used"] == "fake-openai"
    assert len(data["sections"]) >= 12
    titles = [section["title"] for section in data["sections"]]
    assert "Welcome" in titles
    assert "Suggested Learning Path" in titles
    assert "First Tasks Recommendation" in titles
    assert all(section["content"] for section in data["sections"])


def test_parse_briefing_sections_fills_missing():
    markdown = "# Welcome\n\nHello team.\n\n# Project Purpose\n\nSolves knowledge loss.\n"
    sections = parse_briefing_sections(markdown)
    assert sections[0]["title"] == "Welcome"
    assert "Hello" in sections[0]["content"]
    missing = next(item for item in sections if item["title"] == "Important APIs")
    assert "not found in the indexed project knowledge" in missing["content"]
