# Project DNA

**The living memory of every project.**

Project DNA is an AI Knowledge Twin that turns a GitHub repository and project documents into searchable, grounded organizational memory — with citations, knowledge risks, timeline, and a knowledge graph.

---

## 🚀 Live Demo

### 🌐 Application

- **Frontend (Vercel):** https://project-dna-five.vercel.app

> **Backend:** Render (FastAPI)  
> **Vector Database:** Qdrant Cloud  
> **Database:** MongoDB Atlas

### 🎥 Demo Video

Watch the complete walkthrough of **Project DNA** here:

**Loom Recording:**  
https://www.loom.com/share/1c4085203d844fbfb9720a7b4d5e0eea

---

## What it does

| Feature | Description |
|---|---|
| **Auth & projects** | JWT register/login and per-user project workspaces |
| **GitHub connect** | Ingest public repo metadata, README, structure, commits |
| **Document upload** | PDF / DOCX / MD / TXT extraction into project memory |
| **Indexing (RAG)** | Chunk → OpenAI embeddings → **Qdrant Cloud** |
| **AI chat** | Grounded answers with sources (OpenAI primary, Gemini fallback) |
| **Dashboard** | Health, coverage, activity, insights |
| **Risks** | Knowledge-risk analysis (undocumented areas, ownership gaps, stale decisions) |
| **Timeline** | Project activity / story timeline |
| **Knowledge graph** | Entity/relationship view for React-style exploration |
| **Onboarding briefing** | Fast “what is this project?” style briefing for new teammates |

---

## Architecture

```text
Vercel (React / Vite)
        │
        ▼
Render (FastAPI)
   ├── MongoDB Atlas   → users, projects, docs, chat history
   ├── Qdrant Cloud    → vector embeddings for RAG
   ├── OpenAI          → embeddings + primary chat
   └── Gemini          → chat fallback
```

You do **not** self-host the vector database — **Qdrant Cloud** is already the production vector store when `QDRANT_URL` and `QDRANT_API_KEY` are set.

---

## Tech stack

**Frontend:** React, Vite, Lucide icons · deployed on [Vercel](https://project-dna-five.vercel.app)  
**Backend:** FastAPI, MongoDB, Qdrant, LangChain/OpenAI/Gemini · deployed on Render  
**Auth:** JWT (python-jose + passlib/bcrypt)

---

## Quick start (local)

### Backend

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

pip install -r requirements.txt
copy .env.example .env
# Fill MongoDB, Qdrant, OpenAI, Gemini, JWT_SECRET
uvicorn app.main:app --reload --port 8000
```

- API: http://localhost:8000  
- Health: http://localhost:8000/api/health  
- Swagger: http://localhost:8000/docs  

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173  

For local API via Vite proxy, leave `VITE_API_BASE_URL` empty.  
For a deployed API, set:

```env
VITE_API_BASE_URL=https://YOUR-RENDER-SERVICE.onrender.com
```

---

## Demo flow (judges / testers)

1. Open the live app: [https://project-dna-five.vercel.app](https://project-dna-five.vercel.app)
2. Create an account (password ≥ 6 characters)
3. Create a project
4. Connect a **public** GitHub repo
5. Upload a short PDF/MD doc (optional)
6. Run **Index knowledge**
7. Ask chat: *“What is this project about?”*
8. Check Dashboard, Risks, Timeline, and Knowledge Graph

---

## Environment variables (backend)

See [`backend/.env.example`](backend/.env.example) for the full list. Minimum for a working demo:

| Variable | Purpose |
|---|---|
| `MONGODB_URI` | MongoDB Atlas connection string |
| `JWT_SECRET` | JWT signing secret |
| `OPENAI_API_KEY` | Embeddings + primary LLM |
| `QDRANT_URL` / `QDRANT_API_KEY` | Vector search (Qdrant Cloud) |
| `GEMINI_API_KEY` | Fallback LLM |
| `CORS_ORIGINS` | Must include `https://project-dna-five.vercel.app` in production |

---

## Deploy notes

| Service | Platform | Notes |
|---|---|---|
| Frontend | [Vercel](https://project-dna-five.vercel.app) | Root: `frontend`, env: `VITE_API_BASE_URL` |
| Backend | Render | Root: `backend`, start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`, Python **3.12** |
| Database | MongoDB Atlas | Allow Render IPs (`0.0.0.0/0` for demo) |
| Vectors | Qdrant Cloud | No self-hosting required |

Render free tier may cold-start (30–60s) after idle — open the API once before a live demo.

---

## Project layout

```text
Project-DNA/
├── frontend/          # React + Vite UI
├── backend/           # FastAPI API + RAG services
├── docs/              # Extra docs
├── sample-data/       # Sample inputs for demos
├── spec.md            # Product specification
├── task.md            # Team task breakdown
└── README.md
```

---

## Team

Built as a hackathon MVP for an AI Knowledge Twin experience — ingestion, grounded chat, and knowledge intelligence in one workspace.

---

## License

See [LICENSE](LICENSE).
