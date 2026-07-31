"""Phase 3 chunking / embeddings / indexing tests."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.services.chunking import ChunkingService
from app.services.container import services
from app.services.embeddings import FakeEmbeddingService
from app.services.vectorstore import InMemoryVectorStore, VectorPoint


async def _auth_project_with_github(client: AsyncClient) -> tuple[dict[str, str], str]:
    register = await client.post(
        "/api/auth/register",
        json={
            "full_name": "Indexer",
            "email": "index@company.com",
            "password": "secret123",
        },
    )
    headers = {"Authorization": f"Bearer {register.json()['data']['access_token']}"}
    project = await client.post(
        "/api/projects",
        headers=headers,
        json={"project_name": "Indexed Project", "description": "Phase 3"},
    )
    project_id = project.json()["data"]["id"]
    await client.post(
        f"/api/projects/{project_id}/github",
        headers=headers,
        json={"repository_url": "https://github.com/acme/nova-web"},
    )
    return headers, project_id


@pytest.mark.asyncio
async def test_chunking_respects_size_and_overlap():
    chunker = ChunkingService(chunk_size_tokens=50, chunk_overlap_tokens=10)
    text = "\n\n".join([f"Paragraph {i}. " + ("word " * 20) for i in range(8)])
    chunks = chunker.chunk_text(text)
    assert len(chunks) >= 2
    assert all(chunk.token_count <= 60 for chunk in chunks)
    assert all(chunk.text.strip() for chunk in chunks)


@pytest.mark.asyncio
async def test_index_project_end_to_end(app_client: AsyncClient):
    headers, project_id = await _auth_project_with_github(app_client)

    indexed = await app_client.post(f"/api/projects/{project_id}/index", headers=headers)
    assert indexed.status_code == 200
    data = indexed.json()["data"]
    assert data["chunks_indexed"] > 0
    assert data["sources_indexed"] >= 1
    assert data["project_status"] == "ready"
    assert data["embedding_model"] == "fake-embedding"

    status = await app_client.get(f"/api/projects/{project_id}/index", headers=headers)
    assert status.status_code == 200
    assert status.json()["data"]["is_indexed"] is True
    assert status.json()["data"]["chunks_indexed"] > 0

    project_status = await app_client.get(f"/api/projects/{project_id}/status", headers=headers)
    body = project_status.json()["data"]
    assert body["is_indexed"] is True
    assert body["chunks_indexed"] > 0
    assert body["project_status"] == "ready"

    assert await services.vector_store.count_by_project(project_id) > 0


@pytest.mark.asyncio
async def test_index_without_sources_fails(app_client: AsyncClient):
    register = await app_client.post(
        "/api/auth/register",
        json={
            "full_name": "Empty",
            "email": "empty-index@company.com",
            "password": "secret123",
        },
    )
    headers = {"Authorization": f"Bearer {register.json()['data']['access_token']}"}
    project = await app_client.post(
        "/api/projects",
        headers=headers,
        json={"project_name": "Empty", "description": ""},
    )
    project_id = project.json()["data"]["id"]
    response = await app_client.post(f"/api/projects/{project_id}/index", headers=headers)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "nothing_to_index"


@pytest.mark.asyncio
async def test_vector_store_project_isolation():
    store = InMemoryVectorStore()
    await store.ensure_collection(vector_size=4)
    await store.upsert(
        [
            VectorPoint(id="a1", vector=[1, 0, 0, 0], payload={"project_id": "p1", "text": "alpha"}),
            VectorPoint(id="b1", vector=[0, 1, 0, 0], payload={"project_id": "p2", "text": "beta"}),
        ]
    )
    results = await store.search(project_id="p1", query_vector=[1, 0, 0, 0], top_k=5)
    assert len(results) == 1
    assert results[0].payload["project_id"] == "p1"

    await store.delete_by_project("p1")
    assert await store.count_by_project("p1") == 0
    assert await store.count_by_project("p2") == 1


@pytest.mark.asyncio
async def test_fake_embeddings_are_deterministic():
    service = FakeEmbeddingService(dimensions=16)
    first = await service.embed_texts(["hello world"])
    second = await service.embed_texts(["hello world"])
    assert first == second
    assert len(first[0]) == 16


@pytest.mark.asyncio
async def test_reindex_replaces_previous_vectors(app_client: AsyncClient):
    headers, project_id = await _auth_project_with_github(app_client)
    first = await app_client.post(f"/api/projects/{project_id}/index", headers=headers)
    count_first = first.json()["data"]["chunks_indexed"]
    second = await app_client.post(f"/api/projects/{project_id}/index", headers=headers)
    count_second = second.json()["data"]["chunks_indexed"]
    assert count_first == count_second
    assert await services.vector_store.count_by_project(project_id) == count_second


@pytest.mark.asyncio
async def test_openapi_includes_phase3_paths(app_client: AsyncClient):
    paths = (await app_client.get("/openapi.json")).json()["paths"]
    assert "/api/projects/{project_id}/index" in paths
