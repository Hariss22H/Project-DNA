# Task Assignment - Member 1 (Team Lead)
# AI Backend & Intelligence

## Role

You are responsible for building the entire AI backend and intelligence layer of Project DNA.

Your work powers every AI feature in the platform.

You own:

- Backend Architecture
- REST APIs
- AI Pipeline
- Document Intelligence
- GitHub Intelligence
- RAG Pipeline
- Vector Database
- AI Knowledge Twin
- Risk Analysis Engine

Your implementation should prioritize:

- Accuracy
- Reliability
- Scalability
- Performance
- Clean Architecture
- Production Readiness

---

# Primary Objective

Build an intelligent backend capable of understanding software projects from repositories and technical documents.

The backend should transform scattered project artifacts into an AI Knowledge Twin that answers contextual questions with high accuracy.

---

# AI Model Strategy

## Primary LLM

OpenAI GPT-4.1 (or GPT-4o)

Reason

- Highest reasoning capability
- Better code understanding
- Better architectural reasoning
- Better RAG responses
- High accuracy

---

## Fallback LLM

Google Gemini 2.5 Pro (or Gemini Flash)

Purpose

Automatically handle

- OpenAI downtime
- API failures
- Rate limits
- Timeout
- Temporary service outages

The user should never notice the fallback.

Implement an automatic retry strategy.

Example

Try OpenAI

↓

If failure

↓

Retry OpenAI

↓

If failure

↓

Switch to Gemini

↓

Return response

---

# Responsibilities

You are responsible for the following modules.

---

## 1. FastAPI Backend

Build the backend using FastAPI.

Responsibilities

- Project APIs
- Repository APIs
- Upload APIs
- AI APIs
- Dashboard APIs

Suggested Folder

backend/

---

## 2. Authentication APIs

Implement

- Register
- Login
- JWT Authentication
- Protected Routes

Endpoints

POST /api/auth/register

POST /api/auth/login

GET /api/auth/me

---

## 3. Project Management APIs

Implement

Create Project

Update Project

Delete Project

List Projects

Retrieve Project

Endpoints

POST /api/projects

GET /api/projects

GET /api/projects/{id}

PUT /api/projects/{id}

DELETE /api/projects/{id}

---

## 4. GitHub Repository Intelligence

The backend should connect to public GitHub repositories.

Responsibilities

Validate Repository

Fetch

- README
- Metadata
- Default Branch
- Folder Structure
- Important Files
- Commit Summary

Store metadata in database.

Expected Output

Repository becomes AI-readable.

---

## 5. Document Intelligence Pipeline

Supported Formats

- PDF
- DOCX
- Markdown
- TXT

Responsibilities

Upload

↓

Extract Text

↓

Clean Text

↓

Metadata Extraction

↓

Chunking

↓

Embeddings

↓

Vector Storage

Recommended Libraries

PyMuPDF

python-docx

Markdown Parser

---

## 6. Text Chunking

Split documents intelligently.

Requirements

Semantic chunking.

Avoid breaking paragraphs unnecessarily.

Recommended Chunk Size

700–1000 tokens

Overlap

100–150 tokens

Goal

Improve retrieval quality.

---

## 7. Embedding Generation

Generate embeddings for

- README
- Documents
- Repository Metadata

Primary

OpenAI Embeddings

Fallback

Gemini Embeddings

Store vectors in Qdrant.

---

## 8. Vector Database

Recommended

Qdrant

Development

FAISS allowed locally.

Responsibilities

Insert vectors

Search vectors

Delete vectors

Project isolation

Similarity search

Metadata filtering

---

## 9. Retrieval-Augmented Generation (RAG)

Implement the complete RAG pipeline.

Pipeline

User Question

↓

Embedding

↓

Vector Search

↓

Retrieve Top-K Context

↓

Prompt Construction

↓

OpenAI

↓

Gemini Fallback

↓

AI Response

Requirements

Always retrieve project context before generation.

Never answer without retrieval.

---

## 10. AI Knowledge Twin

This is the most important module.

The AI should understand

- Architecture
- Technologies
- APIs
- Features
- Documentation
- Relationships
- Repository Context

Capabilities

Explain architecture.

Answer technical questions.

Summarize modules.

Explain APIs.

Understand documentation.

Reference uploaded sources.

Reject unrelated questions politely.

---

## 11. AI Chat APIs

Endpoints

POST /api/chat

Request

Project ID

Question

Response

Answer

Confidence Score

Retrieved Sources

Model Used

Response Time

---

## 12. Prompt Engineering

The prompt should enforce the following rules.

Always answer only using retrieved project knowledge.

Never hallucinate.

If information is unavailable,

say

"I couldn't find enough project information to answer this."

Mention supporting documents whenever possible.

Remain concise.

Remain technical.

---

## 13. LLM Fallback Manager

Implement a dedicated service.

Responsibilities

Try OpenAI.

Retry.

Switch to Gemini.

Log failures.

Return response.

This service should be reusable across the backend.

---

## 14. Risk Prediction Engine

Generate AI insights.

Examples

Missing Documentation

Architecture Gaps

Knowledge Concentration

Weak Documentation

High Dependency Modules

Possible Duplicate Components

Large Undocumented Features

Store results in database.

---

## 15. AI Confidence Score

Every AI response should include

Confidence

Example

96%

Confidence should depend on

Retrieved Context

Similarity Score

Context Coverage

LLM Response Quality

---

## 16. Processing Pipeline

Project Created

↓

Repository Connected

↓

Documents Uploaded

↓

Extract Text

↓

Chunk

↓

Generate Embeddings

↓

Store in Qdrant

↓

Generate Knowledge Graph Metadata

↓

Project Ready

---

# Suggested Backend Structure

backend/

app/

├── api/

├── auth/

├── core/

├── database/

├── models/

├── schemas/

├── services/

│

├── github/

├── ingestion/

├── chunking/

├── embeddings/

├── vectorstore/

├── rag/

├── llm/

├── prompts/

├── risk_engine/

├── knowledge/

│

├── utils/

├── middleware/

└── main.py

---

# Recommended Tech Stack

Backend

FastAPI

Python

Pydantic

SQLAlchemy

JWT

PostgreSQL

AI

LangChain

OpenAI

Gemini

OpenAI Embeddings

Qdrant

Vector DB

Qdrant

(Local)

FAISS

Document Processing

PyMuPDF

python-docx

markdown-it

GitHub

GitHub REST API

Database

PostgreSQL

---

# Environment Variables

DATABASE_URL

JWT_SECRET

OPENAI_API_KEY

GEMINI_API_KEY

QDRANT_URL

QDRANT_API_KEY

GITHUB_TOKEN

---

# Coding Standards

Follow

- SOLID Principles
- Clean Architecture
- Modular Design
- Async FastAPI
- Type Hints
- Dependency Injection
- Pydantic Validation
- Reusable Services
- Proper Logging
- Exception Handling

Avoid

Business logic inside routes.

Large functions.

Duplicate code.

Hardcoded values.

---

# Deliverables

By the end of development, the backend should provide:

✅ Authentication APIs

✅ Project APIs

✅ GitHub Integration

✅ Document Upload APIs

✅ Document Processing Pipeline

✅ Semantic Chunking

✅ OpenAI Embeddings

✅ Gemini Embeddings (Fallback)

✅ Qdrant Integration

✅ Retrieval-Augmented Generation (RAG)

✅ AI Knowledge Twin

✅ AI Chat APIs

✅ LLM Fallback Manager

✅ Risk Prediction Engine

✅ Confidence Score Generation

✅ Production-ready FastAPI Backend

---

# Definition of Done

The task is considered complete when:

- Users can create and manage projects.
- Public GitHub repositories can be connected.
- Documents can be uploaded and processed.
- Embeddings are generated and stored in Qdrant.
- AI answers questions using only indexed project knowledge.
- OpenAI is used as the primary LLM.
- Gemini automatically serves as the fallback LLM.
- AI responses include confidence scores and supporting sources.
- Risk analysis is generated successfully.
- All APIs are documented using FastAPI Swagger.
- The backend is modular, scalable, and production-ready.