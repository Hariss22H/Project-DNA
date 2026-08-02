"""Phase 5 timeline, risks, and dashboard API tests."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


async def _project_with_github(client: AsyncClient) -> tuple[dict[str, str], str]:
    register = await client.post(
        "/api/auth/register",
        json={
            "full_name": "Dash User",
            "email": "dash@company.com",
            "password": "secret123",
        },
    )
    headers = {"Authorization": f"Bearer {register.json()['data']['access_token']}"}
    project = await client.post(
        "/api/projects",
        headers=headers,
        json={"project_name": "Dash Project", "description": "Phase 5"},
    )
    project_id = project.json()["data"]["id"]
    await client.post(
        f"/api/projects/{project_id}/github",
        headers=headers,
        json={"repository_url": "https://github.com/acme/nova-web"},
    )
    return headers, project_id


@pytest.mark.asyncio
async def test_timeline_lists_persisted_events(app_client: AsyncClient):
    headers, project_id = await _project_with_github(app_client)
    response = await app_client.get(f"/api/projects/{project_id}/timeline", headers=headers)
    assert response.status_code == 200
    events = response.json()["data"]
    types = {item["event_type"] for item in events}
    assert "project_created" in types
    assert "repository_connected" in types

    alias = await app_client.get(f"/api/timeline/{project_id}", headers=headers)
    assert alias.status_code == 200
    assert len(alias.json()["data"]) >= 2


@pytest.mark.asyncio
async def test_risk_analysis_and_list(app_client: AsyncClient):
    headers, project_id = await _project_with_github(app_client)
    analyzed = await app_client.post(
        f"/api/projects/{project_id}/risks/analyze",
        headers=headers,
    )
    assert analyzed.status_code == 200
    risks = analyzed.json()["data"]
    assert len(risks) >= 1
    titles = " ".join(risk["title"].lower() for risk in risks)
    assert "architecture" in titles or "document" in titles or "indexed" in titles

    listed = await app_client.get(f"/api/projects/{project_id}/risks", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()["data"]) == len(risks)


@pytest.mark.asyncio
async def test_dashboard_returns_kpis(app_client: AsyncClient):
    headers, project_id = await _project_with_github(app_client)
    await app_client.post(f"/api/projects/{project_id}/index", headers=headers)

    response = await app_client.get(f"/api/projects/{project_id}/dashboard", headers=headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["project_id"] == project_id
    assert 0 <= data["health_score"] <= 100
    assert 0 <= data["knowledge_coverage"] <= 100
    assert data["github_connected"] is True
    assert data["chunks_indexed"] > 0
    assert isinstance(data["connected_sources"], list)
    assert isinstance(data["ai_insights"], list)
    assert isinstance(data["timeline"], list)
    assert isinstance(data["risks"], list)

    alias = await app_client.get(f"/api/dashboard/{project_id}", headers=headers)
    assert alias.status_code == 200
    assert alias.json()["data"]["project_name"] == "Dash Project"


@pytest.mark.asyncio
async def test_openapi_includes_phase5_paths(app_client: AsyncClient):
    paths = (await app_client.get("/openapi.json")).json()["paths"]
    assert "/api/projects/{project_id}/timeline" in paths
    assert "/api/projects/{project_id}/risks" in paths
    assert "/api/projects/{project_id}/risks/analyze" in paths
    assert "/api/projects/{project_id}/dashboard" in paths
    assert "/api/dashboard/{project_id}" in paths
