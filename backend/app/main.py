from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import github, repository, upload, pdf, docx, metadata, timeline, graph

app = FastAPI(title="Project-DNA API")

# Setup CORS for frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Update this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(github.router)
app.include_router(repository.router)
app.include_router(upload.router)
app.include_router(pdf.router)
app.include_router(docx.router)
app.include_router(metadata.router)
app.include_router(timeline.router)
app.include_router(graph.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to Project-DNA Backend"}
