# Project-DNA Backend

This is the FastAPI backend for Project-DNA.

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
