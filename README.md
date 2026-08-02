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

The current MVP primarily indexes repository documentation such as README files and uploaded project documents. In the next iteration, we plan to extend the indexing pipeline to include source code, dependency manifests (package.json, requirements.txt, pom.xml, etc.), and repository structure, enabling Project DNA to understand projects even when documentation is minimal.

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
### 1) Create an account
1. Open the live app link above.
2. Click **Create account** (or the signup switch).
3. Enter:
   - Full name
   - Email
   - Password (**at least 6 characters**)
   - Role (optional)
4. Click **Create account and continue**.
5. You should land inside the Project DNA workspace.

### 2) Create a project
1. In the left sidebar, open **Projects**.
2. In the **Create project** card:
   - Enter a project name (e.g. `Nova Demo`)
   - Add a short description (optional)
3. Click **Create**.
4. Confirm the new project appears under **Your projects** and becomes the active project (top project selector).

### 3) Connect a public GitHub repository
1. Stay on the **Projects** page.
2. In the **Connect GitHub** section (below create/list):
   - Paste a **public** repository URL  
     Example: `https://github.com/facebook/react`
3. Click **Connect**.
4. Wait for the success toast. The project should now show the connected GitHub URL.

### 4) Index knowledge
1. Still on **Projects**, click **Index knowledge**.
2. Wait until indexing finishes (success toast).
3. This chunks the repo/docs, creates embeddings, and stores vectors in **Qdrant Cloud**.

### 5) Upload documents (optional but recommended)
1. Open **Documents** in the sidebar.
2. Click the upload area and choose a short **PDF / MD / DOCX / TXT** file.
3. Wait for upload + extraction success.
4. (Recommended) Go back to **Projects** and click **Index knowledge** again so the new document is included in RAG.

### 6) Explore Knowledge Graph
1. Open **Knowledge Graph** in the sidebar.
2. Review nodes (entities/files/concepts) and edges (relationships).
3. This shows the structural/AI knowledge map of the connected project.

### 7) Explore Timeline
1. Open **Timeline** in the sidebar.
2. Review project activity events (repo connected, docs uploaded, indexing/story events, etc.).

### 8) Ask questions in AI Chat
1. Open **AI Chat** in the sidebar (or the floating chat button).
2. Ask grounded questions, for example:
   - `What is this project about?`
   - `Explain the authentication flow.`
   - `What are the main risks or undocumented areas?`
3. Check that answers include context/sources and confidence when available.

### 9) Generate onboarding briefing (WOW feature)
1. Open **Dashboard** (or the onboarding briefing section in the UI).
2. Click **Generate Briefing**.
3. Wait for the AI briefing to generate.
4. Review the structured briefing sections about the project (great for a new teammate joining).
5. Optionally download/print the briefing if those actions are shown.

### 10) Check Dashboard + Risks
1. Open **Dashboard** and click **Refresh data** if needed.
2. Confirm health score, docs indexed, sources, and activity look populated.
3. Open **Risk Dashboard** → click **Analyze**.
4. Review knowledge-risk alerts (ownership gaps, missing docs, stale decisions, etc.).

### Suggested 3-minute judge script
1. Sign up → create project  
2. Paste public GitHub URL → **Connect** → **Index knowledge**  
3. Upload one short doc → re-index  
4. Show **Knowledge Graph** + **Timeline**  
5. Ask one chat question with sources  
6. Click **Generate Briefing** and walk through the onboarding report  
7. End on **Risk Dashboard → Analyze**

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
