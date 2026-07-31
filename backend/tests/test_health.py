"""Phase 0 health / root endpoint tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_endpoint(app_client: AsyncClient):
    response = await app_client.get("/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["docs"] == "/docs"
    assert "/health" in payload["data"]["health"]


@pytest.mark.asyncio
async def test_health_endpoint_reports_mongodb(app_client: AsyncClient):
    response = await app_client.get("/api/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] in {"ok", "degraded"}
    assert payload["data"]["version"]
    assert any(dep["name"] == "mongodb" for dep in payload["data"]["dependencies"])


@pytest.mark.asyncio
async def test_openapi_docs_available(app_client: AsyncClient):
    docs = await app_client.get("/docs")
    openapi = await app_client.get("/openapi.json")
    assert docs.status_code == 200
    assert openapi.status_code == 200
    schema = openapi.json()
    assert "paths" in schema
    assert "/api/health" in schema["paths"]
