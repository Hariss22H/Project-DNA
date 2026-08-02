# Project DNA ? Backend (Hackathon MVP)

FastAPI backend for the AI Knowledge Twin.

## Setup
1. Create a virtual environment: `python -m venv venv`
2. Activate the virtual environment.
3. Install dependencies: `pip install -r requirements.txt`
4. Copy `.env.example` to `.env`
5. Run the server: `uvicorn app.main:app --reload`

## Demo Video

Watch the complete demonstration of *Project DNA* here:

🔗 Demo Video: https://youtu.be/your-demo-video-link

## Current status

### Phase 0
- Runnable FastAPI scaffold
- Environment-based configuration
- MongoDB (Motor) connection lifecycle
- Swagger at `/docs`
- Modular folder structure from `task.md`
- Pluggable service interfaces for Member 3

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

### Phase 3
- Index knowledge: `POST /api/projects/{id}/index`
- Embeddings: OpenAI `text-embedding-3-small` only
- Vector DB: Qdrant Cloud (in-memory fallback if `QDRANT_URL` is empty)

### Phase 4
- Chat: `POST /api/chat`
- OpenAI primary ? retry ? Gemini fallback
- Grounded answers with citations

### Phase 5
- Timeline / risks / dashboard APIs
- Heuristic health + knowledge coverage scores

### Phase 6
- Knowledge graph JSON for React Flow
- Graph preview on dashboard

## Hackathon demo flow

1. Register / login
2. Create project
3. `POST /projects/{id}/github` with a public repo URL
4. Upload a PDF/MD doc (optional)
5. `POST /projects/{id}/index`
6. `POST /chat` with a project question
7. Open dashboard, timeline, risks, graph

## Quick start

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

pip install -r requirements.txt
copy .env.example .env
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

## Member 3 integration routes

Member 3 utility connectors are mounted alongside the core APIs:

| Area | Endpoints |
|------|-----------|
| GitHub connector | `/api/github/*` |
| Local repository scanner | `/api/repository/*` |
| Upload / PDF / DOCX / metadata | `/api/documents/upload`, `/api/documents/pdf/parse`, ... |
| Timeline generate | `/api/timeline/generate` |
| Graph generate / enrich | `/api/graph/generate`, `/api/graph/enrich` |

Core product routes (auth, projects, RAG chat, dashboard, project graph/timeline) remain owned by Member 1.

Local filesystem scanner lives in `app/services/local_repository_service.py` so it does not collide with Member 1 `repository_service.py` orchestration.
