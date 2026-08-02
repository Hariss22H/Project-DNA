"""Phase 6 knowledge graph JSON tests."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.services.knowledge import DefaultEntityExtractor, DefaultKnowledgeGraphBuilder


async def _project_with_github(client: AsyncClient) -> tuple[dict[str, str], str]:
    register = await client.post(
        "/api/auth/register",
        json={
            "full_name": "Graph User",
            "email": "graph@company.com",
            "password": "secret123",
        },
    )
    headers = {"Authorization": f"Bearer {register.json()['data']['access_token']}"}
    project = await client.post(
        "/api/projects",
        headers=headers,
        json={"project_name": "Graph Project", "description": "Phase 6"},
    )
    project_id = project.json()["data"]["id"]
    await client.post(
        f"/api/projects/{project_id}/github",
        headers=headers,
        json={"repository_url": "https://github.com/acme/nova-web"},
    )
    return headers, project_id


@pytest.mark.asyncio
async def test_entity_extractor_and_builder_shape():
    extractor = DefaultEntityExtractor()
    entities = await extractor.extract(
        project_id="p1",
        project_name="Nova",
        repository={
            "full_name": "acme/nova-web",
            "repository_url": "https://github.com/acme/nova-web",
            "languages": {"TypeScript": 10, "Python": 5},
            "topics": ["api", "hackathon"],
            "structure": ["src/main.ts", "src/api/routes.ts", "docs/guide.md", "package.json"],
            "important_files": ["package.json", "README.md"],
            "readme_content": "# Nova",
        },
        documents=[
            {"_id": "d1", "file_name": "architecture.md", "file_type": "md", "is_architecture": True}
        ],
    )
    assert any(entity.entity_type == "technology" for entity in entities)
    assert any(entity.entity_type == "document" for entity in entities)

    graph = await DefaultKnowledgeGraphBuilder().build_graph(project_id="p1", entities=entities)
    payload = graph.model_dump()
    assert "nodes" in payload and "edges" in payload
    assert len(payload["nodes"]) >= 3
    assert len(payload["edges"]) >= 2
    assert all("id" in node and "label" in node for node in payload["nodes"])
    assert all("source" in edge and "target" in edge for edge in payload["edges"])


@pytest.mark.asyncio
async def test_graph_api_returns_react_flow_json(app_client: AsyncClient):
    headers, project_id = await _project_with_github(app_client)

    response = await app_client.get(f"/api/projects/{project_id}/graph", headers=headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["project_id"] == project_id
    assert isinstance(data["nodes"], list)
    assert isinstance(data["edges"], list)
    assert data["entity_count"] >= 1
    assert any(node["type"] == "repository" for node in data["nodes"])

    cached = await app_client.get(f"/api/projects/{project_id}/graph", headers=headers)
    assert cached.status_code == 200
    assert cached.json()["data"]["cached"] is True

    rebuilt = await app_client.post(
        f"/api/projects/{project_id}/graph/rebuild",
        headers=headers,
    )
    assert rebuilt.status_code == 200
    assert rebuilt.json()["data"]["cached"] is False

    alias = await app_client.get(f"/api/knowledge-graph/{project_id}", headers=headers)
    assert alias.status_code == 200
    assert "nodes" in alias.json()["data"]


@pytest.mark.asyncio
async def test_dashboard_includes_graph_preview(app_client: AsyncClient):
    headers, project_id = await _project_with_github(app_client)
    dashboard = await app_client.get(f"/api/projects/{project_id}/dashboard", headers=headers)
    assert dashboard.status_code == 200
    preview = dashboard.json()["data"]["knowledge_graph_preview"]
    assert "nodes" in preview and "edges" in preview


@pytest.mark.asyncio
async def test_openapi_includes_phase6_paths(app_client: AsyncClient):
    paths = (await app_client.get("/openapi.json")).json()["paths"]
    assert "/api/projects/{project_id}/graph" in paths
    assert "/api/projects/{project_id}/graph/rebuild" in paths
    assert "/api/knowledge-graph/{project_id}" in paths
