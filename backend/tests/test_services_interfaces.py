"""Ensure Member 3 plug-in interfaces work without touching the API layer."""

import pytest

from app.services.container import services
from app.services.github import GitHubService, GitHubRepositoryData, StubGitHubService
from app.services.ingestion import DocumentType, StubDocumentExtractor
from app.services.knowledge import ProjectEntity, StubKnowledgeGraphBuilder
from app.services.timeline import TimelineEvent


@pytest.mark.asyncio
async def test_stub_github_service_fetch():
    service: GitHubService = StubGitHubService()
    assert await service.validate_repository("https://github.com/acme/nova-web")
    data = await service.fetch_repository("https://github.com/acme/nova-web")
    assert isinstance(data, GitHubRepositoryData)
    assert data.full_name == "acme/nova-web"
    assert data.readme_content


@pytest.mark.asyncio
async def test_stub_github_rejects_invalid_url():
    service = StubGitHubService()
    assert not await service.validate_repository("https://gitlab.com/acme/nova")


@pytest.mark.asyncio
async def test_stub_document_extractor_txt():
    extractor = StubDocumentExtractor()
    result = await extractor.extract(
        file_name="notes.txt",
        file_type=DocumentType.TXT,
        content=b"Hello Project DNA\n",
    )
    assert result.char_count > 0
    assert "Hello Project DNA" in result.text


@pytest.mark.asyncio
async def test_stub_document_extractor_pdf_not_implemented():
    extractor = StubDocumentExtractor()
    with pytest.raises(Exception) as exc:
        await extractor.extract(
            file_name="arch.pdf",
            file_type=DocumentType.PDF,
            content=b"%PDF",
        )
    assert getattr(exc.value, "code", "") == "extractor_not_implemented"


@pytest.mark.asyncio
async def test_stub_knowledge_graph_json_shape():
    builder = StubKnowledgeGraphBuilder()
    graph = await builder.build_graph(
        project_id="proj-1",
        entities=[
            ProjectEntity(id="tech:python", name="Python", entity_type="technology"),
            ProjectEntity(id="doc:readme", name="README", entity_type="document"),
        ],
    )
    assert isinstance(graph.nodes, list)
    assert isinstance(graph.edges, list)
    payload = graph.model_dump()
    assert "nodes" in payload and "edges" in payload
    assert len(payload["nodes"]) == 3
    assert len(payload["edges"]) == 2


@pytest.mark.asyncio
async def test_service_container_swap_does_not_require_api_changes():
    class FakeGitHub(StubGitHubService):
        async def validate_repository(self, repository_url: str) -> bool:
            return repository_url.endswith("swapped")

    services.set_github_service(FakeGitHub())
    assert await services.github.validate_repository("https://github.com/acme/swapped")


@pytest.mark.asyncio
async def test_stub_timeline_service():
    from app.services.timeline import StubTimelineService

    timeline = StubTimelineService()
    event = await timeline.add_event(
        TimelineEvent(
            project_id="proj-1",
            event_type="project_created",
            title="Project Created",
        )
    )
    assert event.id
    items = await timeline.list_events("proj-1")
    assert len(items) == 1
