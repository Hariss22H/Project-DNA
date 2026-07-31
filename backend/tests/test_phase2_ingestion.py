"""Phase 2 GitHub + document ingestion API tests (uses stub connectors)."""

from __future__ import annotations

import io

import pytest
from httpx import AsyncClient

from app.services.container import services
from app.services.ingestion import CompositeDocumentExtractor, DocumentType


async def _auth_and_project(client: AsyncClient) -> tuple[dict[str, str], str]:
    register = await client.post(
        "/api/auth/register",
        json={
            "full_name": "Phase Two",
            "email": "phase2@company.com",
            "password": "secret123",
        },
    )
    token = register.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    project = await client.post(
        "/api/projects",
        headers=headers,
        json={"project_name": "Ingest Demo", "description": "Phase 2"},
    )
    return headers, project.json()["data"]["id"]


@pytest.mark.asyncio
async def test_connect_github_via_stub(app_client: AsyncClient):
    headers, project_id = await _auth_and_project(app_client)

    response = await app_client.post(
        f"/api/projects/{project_id}/github",
        headers=headers,
        json={"repository_url": "https://github.com/acme/nova-web"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["full_name"] == "acme/nova-web"
    assert data["readme_content"]

    fetched = await app_client.get(f"/api/projects/{project_id}/github", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["data"]["full_name"] == "acme/nova-web"

    project = await app_client.get(f"/api/projects/{project_id}", headers=headers)
    assert project.json()["data"]["github_repository"] == "https://github.com/acme/nova-web"

    status = await app_client.get(f"/api/projects/{project_id}/status", headers=headers)
    assert status.status_code == 200
    body = status.json()["data"]
    assert body["github_connected"] is True
    assert body["has_readme"] is True
    assert body["ready_for_indexing"] is True


@pytest.mark.asyncio
async def test_connect_github_rejects_invalid_url(app_client: AsyncClient):
    headers, project_id = await _auth_and_project(app_client)
    response = await app_client.post(
        f"/api/projects/{project_id}/github",
        headers=headers,
        json={"repository_url": "https://gitlab.com/acme/nova"},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_github_url"


@pytest.mark.asyncio
async def test_upload_list_get_delete_document(app_client: AsyncClient, tmp_path):
    headers, project_id = await _auth_and_project(app_client)

    # Point uploads at a temp directory for this test.
    from app.services import document_service as document_service_module

    original_init = document_service_module.DocumentService.__init__

    def _init(self, db, *, extractor=None, upload_root=None):
        original_init(self, db, extractor=extractor, upload_root=upload_root or tmp_path)

    document_service_module.DocumentService.__init__ = _init
    try:
        files = {
            "file": ("notes.md", b"# Auth\n\nJWT based login flow.\n", "text/markdown"),
        }
        uploaded = await app_client.post(
            f"/api/projects/{project_id}/documents",
            headers=headers,
            files=files,
        )
        assert uploaded.status_code == 201
        doc = uploaded.json()["data"]
        assert doc["file_name"] == "notes.md"
        assert doc["file_type"] == "md"
        assert doc["char_count"] > 0
        document_id = doc["id"]

        listed = await app_client.get(f"/api/projects/{project_id}/documents", headers=headers)
        assert listed.status_code == 200
        assert len(listed.json()["data"]) == 1

        detail = await app_client.get(
            f"/api/projects/{project_id}/documents/{document_id}",
            headers=headers,
        )
        assert detail.status_code == 200
        assert "JWT" in detail.json()["data"]["extracted_text"]

        status = await app_client.get(f"/api/projects/{project_id}/status", headers=headers)
        assert status.json()["data"]["documents_count"] == 1

        deleted = await app_client.delete(
            f"/api/projects/{project_id}/documents/{document_id}",
            headers=headers,
        )
        assert deleted.status_code == 200
        listed_after = await app_client.get(
            f"/api/projects/{project_id}/documents",
            headers=headers,
        )
        assert listed_after.json()["data"] == []
    finally:
        document_service_module.DocumentService.__init__ = original_init


@pytest.mark.asyncio
async def test_upload_rejects_unsupported_extension(app_client: AsyncClient, tmp_path):
    headers, project_id = await _auth_and_project(app_client)
    from app.services import document_service as document_service_module

    original_init = document_service_module.DocumentService.__init__

    def _init(self, db, *, extractor=None, upload_root=None):
        original_init(self, db, extractor=extractor, upload_root=upload_root or tmp_path)

    document_service_module.DocumentService.__init__ = _init
    try:
        response = await app_client.post(
            f"/api/projects/{project_id}/documents",
            headers=headers,
            files={"file": ("data.csv", b"a,b\n1,2\n", "text/csv")},
        )
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "unsupported_file_type"
    finally:
        document_service_module.DocumentService.__init__ = original_init


@pytest.mark.asyncio
async def test_timeline_events_emitted_for_ingestion(app_client: AsyncClient):
    headers, project_id = await _auth_and_project(app_client)
    await app_client.post(
        f"/api/projects/{project_id}/github",
        headers=headers,
        json={"repository_url": "https://github.com/acme/nova-web"},
    )
    events = await services.timeline.list_events(project_id)
    types = {event.event_type for event in events}
    assert "project_created" in types
    assert "repository_connected" in types
    assert "readme_indexed" in types


@pytest.mark.asyncio
async def test_composite_extractor_txt_and_pdf():
    extractor = CompositeDocumentExtractor()

    txt = await extractor.extract(
        file_name="a.txt",
        file_type=DocumentType.TXT,
        content=b"Hello knowledge twin",
    )
    assert "Hello knowledge twin" in txt.text

    import fitz

    buffer = io.BytesIO()
    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text((72, 72), "Architecture overview")
    pdf.save(buffer)
    pdf.close()

    pdf_doc = await extractor.extract(
        file_name="architecture.pdf",
        file_type=DocumentType.PDF,
        content=buffer.getvalue(),
    )
    assert "Architecture" in pdf_doc.text
    assert pdf_doc.page_count == 1


@pytest.mark.asyncio
async def test_openapi_includes_phase2_paths(app_client: AsyncClient):
    paths = (await app_client.get("/openapi.json")).json()["paths"]
    assert "/api/projects/{project_id}/github" in paths
    assert "/api/projects/{project_id}/documents" in paths
    assert "/api/projects/{project_id}/status" in paths
