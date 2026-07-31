# Project DNA — Backend (Hackathon MVP)

FastAPI backend for the AI Knowledge Twin.

## Current status

### Phase 0
- Runnable FastAPI scaffold
- Environment-based configuration
- MongoDB (Motor) connection lifecycle
- Swagger at `/docs`
- Modular folder structure from `task.md`
- Pluggable service interfaces for Member 3 (GitHub, document extraction, knowledge graph, timeline)

### Phase 1
- JWT authentication (`/api/auth/register`, `/login`, `/me`)
- Project workspace CRUD (`/api/projects`)
- Per-user project isolation
- MongoDB indexes for users/projects

### Phase 2
- Connect public GitHub repo: `POST /api/projects/{id}/github`
- Upload/extract docs (PDF/DOCX/MD/TXT): `POST /api/projects/{id}/documents`
- Project status: `GET /api/projects/{id}/status`
- Default connectors: `HttpGitHubService`, `CompositeDocumentExtractor`
- Member 3 can replace connectors via `services.set_github_service()` / `set_document_extractor()` without API changes

### Phase 3
- Index knowledge: `POST /api/projects/{id}/index`
- Index status: `GET /api/projects/{id}/index`
- Chunking (~800 tokens, 120 overlap)
- Embeddings: OpenAI `text-embedding-3-small` only
- Vector DB: Qdrant Cloud (in-memory fallback if `QDRANT_URL` is empty)
- Project-isolated vectors + re-index support

### Phase 4
- Chat: `POST /api/chat` `{ project_id, question }`
- History: `GET /api/projects/{id}/chat`
- RAG grounded answers with source citations
- OpenAI primary → retry → Gemini 2.5 Flash fallback
- Response metadata: answer, sources, confidence, model_used, response_time_ms

### Phase 5
- Timeline: `GET /api/projects/{id}/timeline` (alias `/api/timeline/{id}`)
- Risks analyze/list: `POST/GET /api/projects/{id}/risks...`
- Dashboard: `GET /api/projects/{id}/dashboard` (alias `/api/dashboard/{id}`)
- Heuristic health + knowledge coverage scores
- Rule-based risks with optional LLM summary

### Phase 6
- Knowledge graph JSON: `GET /api/projects/{id}/graph`
- Rebuild: `POST /api/projects/{id}/graph/rebuild`
- Spec alias: `GET /api/knowledge-graph/{id}`
- React Flow payload: `{ nodes: [], edges: [] }`
- Member 3 can replace `EntityExtractor` / graph builder via service container
- Graph preview included in dashboard

## Hackathon demo flow

1. Register / login  
2. Create project  
3. `POST /projects/{id}/github` with a public repo URL  
4. Upload a PDF/MD doc (optional)  
5. `POST /projects/{id}/index`  
6. `POST /chat` with a project question  
7. Open `/projects/{id}/dashboard`, `/timeline`, `/risks`, `/graph`

## Quick start

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
# source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env   # then edit MongoDB Atlas URI
uvicorn app.main:app --reload --port 8000
```

- API root: http://localhost:8000/
- Health: http://localhost:8000/api/health
- Swagger: http://localhost:8000/docs

## Tests

```bash
cd backend
pytest -v
```

Tests use `mongomock-motor` — no live Atlas cluster required.

## Member 3 integration

Implement these interfaces and register them on the service container:

| Interface | Module | Default |
|-----------|--------|---------|
| `GitHubService` | `app/services/github/base.py` | `StubGitHubService` |
| `DocumentExtractor` | `app/services/ingestion/base.py` | `StubDocumentExtractor` |
| `KnowledgeGraphBuilder` | `app/services/knowledge/base.py` | `StubKnowledgeGraphBuilder` |
| `TimelineService` | `app/services/timeline/base.py` | `StubTimelineService` |

```python
from app.services.container import services
services.set_github_service(MyGitHubService())
```

API routes depend only on the container — no route changes needed when swapping implementations.

## Phases

| Phase | Focus |
|-------|--------|
| 0 | Scaffold, config, MongoDB, Swagger, interfaces |
| 1 | Auth + Projects CRUD |
| 2 | GitHub + document upload/extract |
| 3 | Chunking, embeddings, Qdrant |
| 4 | RAG chat + LLM fallback |
| 5 | Risks, timeline, dashboard APIs |
| 6 | Knowledge graph JSON + polish |
