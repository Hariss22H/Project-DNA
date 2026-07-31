"""Phase 4 RAG chat + LLM fallback tests."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.services.container import services
from app.services.llm import LLMFallbackManager, build_fake_llm_manager
from app.services.llm.fake import FakeLLMProvider
from app.services.prompts.rag import UNRELATED_OR_EMPTY_RETRIEVAL_ANSWER
from app.services.rag import RAGService
from app.services.vectorstore import InMemoryVectorStore


async def _ready_project(client: AsyncClient) -> tuple[dict[str, str], str]:
    register = await client.post(
        "/api/auth/register",
        json={
            "full_name": "Chat User",
            "email": "chat@company.com",
            "password": "secret123",
        },
    )
    headers = {"Authorization": f"Bearer {register.json()['data']['access_token']}"}
    project = await client.post(
        "/api/projects",
        headers=headers,
        json={"project_name": "Chat Project", "description": "Phase 4"},
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
async def test_chat_requires_index(app_client: AsyncClient):
    register = await app_client.post(
        "/api/auth/register",
        json={
            "full_name": "No Index",
            "email": "noindex-chat@company.com",
            "password": "secret123",
        },
    )
    headers = {"Authorization": f"Bearer {register.json()['data']['access_token']}"}
    project = await app_client.post(
        "/api/projects",
        headers=headers,
        json={"project_name": "Empty Chat", "description": ""},
    )
    project_id = project.json()["data"]["id"]
    response = await app_client.post(
        "/api/chat",
        headers=headers,
        json={"project_id": project_id, "question": "What is the architecture?"},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "not_indexed"


@pytest.mark.asyncio
async def test_chat_returns_grounded_answer_and_sources(app_client: AsyncClient):
    headers, project_id = await _ready_project(app_client)

    response = await app_client.post(
        "/api/chat",
        headers=headers,
        json={
            "project_id": project_id,
            "question": "Explain the project README and architecture.",
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["answer"]
    assert data["model_used"] == "fake-openai"
    assert data["fallback_used"] is False
    assert data["confidence"] >= 0
    assert data["retrieved_count"] > 0
    assert isinstance(data["sources"], list)
    assert data["response_time_ms"] >= 0
    assert data["conversation_id"]

    history = await app_client.get(f"/api/projects/{project_id}/chat", headers=headers)
    assert history.status_code == 200
    assert len(history.json()["data"]) == 1
    assert history.json()["data"][0]["question"].startswith("Explain the project")


@pytest.mark.asyncio
async def test_llm_fallback_to_gemini():
    manager = build_fake_llm_manager(primary_fail=True, fallback_fail=False)
    result = await manager.generate(
        system_prompt="sys",
        user_prompt="Context:\nAuth uses JWT\n\nQuestion: how does auth work?",
    )
    assert result.fallback_used is True
    assert result.model_used == "fake-gemini"
    assert result.attempts >= 2


@pytest.mark.asyncio
async def test_llm_all_providers_fail():
    manager = LLMFallbackManager(
        primary=FakeLLMProvider(model_name="boom-openai", fail=True),
        fallback=FakeLLMProvider(model_name="boom-gemini", fail=True),
        primary_retries=2,
    )
    with pytest.raises(Exception) as exc:
        await manager.generate(system_prompt="s", user_prompt="u")
    assert getattr(exc.value, "code", "") == "llm_unavailable"


@pytest.mark.asyncio
async def test_rag_rejects_when_no_relevant_retrieval():
    store = InMemoryVectorStore()
    await store.ensure_collection(vector_size=32)
    # Indexed count > 0 but scores filtered out by high min_score.
    from app.services.vectorstore import VectorPoint

    await store.upsert(
        [
            VectorPoint(
                id="p1:readme:0",
                vector=[1.0] + [0.0] * 31,
                payload={
                    "project_id": "proj-1",
                    "text": "hello",
                    "file_name": "README.md",
                    "title": "README",
                    "source_type": "readme",
                    "chunk_index": 0,
                },
            )
        ]
    )
    services.set_vector_store(store)
    rag = RAGService(min_score=0.99, top_k=3)
    # Query embedding won't match perfectly → filtered out
    result = await rag.ask(project_id="proj-1", question="totally unrelated astronomy question")
    assert result["model_used"] == "none"
    assert result["sources"] == []
    assert UNRELATED_OR_EMPTY_RETRIEVAL_ANSWER in result["answer"]


@pytest.mark.asyncio
async def test_openapi_includes_phase4_paths(app_client: AsyncClient):
    paths = (await app_client.get("/openapi.json")).json()["paths"]
    assert "/api/chat" in paths
    assert "/api/projects/{project_id}/chat" in paths
