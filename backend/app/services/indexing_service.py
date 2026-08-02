"""Knowledge indexing orchestration: chunk → embed → Qdrant."""

from __future__ import annotations

import logging
from typing import Any, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.exceptions import AppError
from app.schemas.project import ProjectStatus
from app.services.chunking.service import ChunkingService
from app.services.container import services
from app.services.embeddings.base import EmbeddingService
from app.services.project_service import ProjectService
from app.services.timeline.base import TimelineEvent
from app.services.vectorstore.base import VectorPoint, VectorStore
from app.utils.time import utc_now

logger = logging.getLogger(__name__)

INDEX_META_COLLECTION = "index_meta"
BATCH_SIZE = 32


class IndexingService:
    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        *,
        chunker: Optional[ChunkingService] = None,
        embeddings: Optional[EmbeddingService] = None,
        vector_store: Optional[VectorStore] = None,
    ) -> None:
        self.db = db
        self.projects = ProjectService(db)
        self.repositories = db["repositories"]
        self.documents = db["documents"]
        self.index_meta = db[INDEX_META_COLLECTION]
        self.chunker = chunker or ChunkingService()
        self.embeddings = embeddings or services.embeddings
        self.vector_store = vector_store or services.vector_store

    async def index_project(self, *, user_id: str, project_id: str) -> dict[str, Any]:
        project = await self.projects.get_project(user_id=user_id, project_id=project_id)
        sources = await self._collect_sources(project_id)
        if not sources:
            raise AppError(
                "No indexable content found. Connect GitHub or upload documents first.",
                status_code=400,
                code="nothing_to_index",
            )

        await self.projects.update_project(
            user_id=user_id,
            project_id=project_id,
            updates={"project_status": ProjectStatus.INDEXING},
        )

        try:
            await self.vector_store.ensure_collection(vector_size=self.embeddings.dimensions)
            await self.vector_store.delete_by_project(project_id)

            points: list[VectorPoint] = []
            total_chunks = 0
            for source in sources:
                chunks = self.chunker.chunk_text(source["text"])
                if not chunks:
                    continue
                texts = [chunk.text for chunk in chunks]
                vectors = await self._embed_batched(texts)
                for chunk, vector in zip(chunks, vectors):
                    point_id = f"{project_id}:{source['source_type']}:{source['source_id']}:{chunk.index}"
                    points.append(
                        VectorPoint(
                            id=point_id,
                            vector=vector,
                            payload={
                                "project_id": project_id,
                                "source_type": source["source_type"],
                                "source_id": source["source_id"],
                                "file_name": source["file_name"],
                                "chunk_index": chunk.index,
                                "token_count": chunk.token_count,
                                "text": chunk.text,
                                "title": source.get("title") or source["file_name"],
                            },
                        )
                    )
                total_chunks += len(chunks)

            upserted = 0
            for start in range(0, len(points), BATCH_SIZE):
                batch = points[start : start + BATCH_SIZE]
                upserted += await self.vector_store.upsert(batch)

            now = utc_now()
            meta = {
                "project_id": project_id,
                "user_id": user_id,
                "chunks_indexed": upserted,
                "sources_indexed": len(sources),
                "embedding_model": self.embeddings.model_name,
                "vector_size": self.embeddings.dimensions,
                "last_indexed_at": now,
                "updated_at": now,
            }
            existing = await self.index_meta.find_one({"project_id": project_id})
            if existing:
                await self.index_meta.update_one({"_id": existing["_id"]}, {"$set": meta})
            else:
                meta["created_at"] = now
                await self.index_meta.insert_one(meta)

            await self.projects.update_project(
                user_id=user_id,
                project_id=project_id,
                updates={"project_status": ProjectStatus.READY},
            )

            await services.timeline.add_event(
                TimelineEvent(
                    project_id=project_id,
                    event_type="knowledge_indexed",
                    title="Knowledge Base Indexed",
                    description=f"Indexed {upserted} chunks from {len(sources)} sources into the Knowledge Twin.",
                    metadata={
                        "chunks_indexed": upserted,
                        "sources_indexed": len(sources),
                        "embedding_model": self.embeddings.model_name,
                        "source": "AI",
                    },
                )
            )

            # Best-effort graph refresh for demo dashboards (non-blocking on failure).
            try:
                from app.services.knowledge_graph_service import KnowledgeGraphService

                await KnowledgeGraphService(self.db).build_and_store(
                    user_id=user_id,
                    project_id=project_id,
                    project_name=project.get("project_name"),
                )
            except Exception as graph_exc:  # noqa: BLE001
                logger.warning("Knowledge graph refresh skipped: %s", graph_exc)

            return {
                "project_id": project_id,
                "project_status": ProjectStatus.READY.value,
                "chunks_indexed": upserted,
                "sources_indexed": len(sources),
                "embedding_model": self.embeddings.model_name,
                "vector_size": self.embeddings.dimensions,
                "last_indexed_at": now,
                "message": "Project knowledge base indexed successfully",
            }
        except Exception as exc:
            logger.exception("Indexing failed for project %s", project_id)
            await self.projects.update_project(
                user_id=user_id,
                project_id=project_id,
                updates={"project_status": ProjectStatus.ERROR},
            )
            if isinstance(exc, AppError):
                raise
            raise AppError(
                "Indexing failed",
                status_code=500,
                code="indexing_failed",
                details=str(exc),
            ) from exc

    async def get_index_status(self, *, user_id: str, project_id: str) -> dict[str, Any]:
        project = await self.projects.get_project(user_id=user_id, project_id=project_id)
        meta = await self.index_meta.find_one({"project_id": project_id})
        vector_count = await self.vector_store.count_by_project(project_id)
        return {
            "project_id": project_id,
            "project_status": project["project_status"],
            "chunks_indexed": int((meta or {}).get("chunks_indexed") or vector_count or 0),
            "sources_indexed": int((meta or {}).get("sources_indexed") or 0),
            "embedding_model": (meta or {}).get("embedding_model") or self.embeddings.model_name,
            "vector_size": (meta or {}).get("vector_size") or self.embeddings.dimensions,
            "last_indexed_at": (meta or {}).get("last_indexed_at"),
            "is_indexed": vector_count > 0 or project["project_status"] == ProjectStatus.READY.value,
        }

    async def delete_project_vectors(self, project_id: str) -> None:
        await self.vector_store.delete_by_project(project_id)
        await self.index_meta.delete_many({"project_id": project_id})

    async def _collect_sources(self, project_id: str) -> list[dict[str, Any]]:
        sources: list[dict[str, Any]] = []

        repo = await self.repositories.find_one({"project_id": project_id})
        if repo:
            if repo.get("readme_content"):
                sources.append(
                    {
                        "source_type": "readme",
                        "source_id": str(repo["_id"]),
                        "file_name": "README.md",
                        "title": f"{repo.get('full_name', 'repository')} README",
                        "text": repo["readme_content"],
                    }
                )

            documentation_files = await self._ensure_documentation_files(repo)
            for index, item in enumerate(documentation_files):
                text = (item.get("content") or "").strip()
                path = (item.get("path") or f"repo-doc-{index}").strip()
                if not text:
                    continue
                sources.append(
                    {
                        "source_type": "repo_document",
                        "source_id": f"{repo['_id']}:{path}",
                        "file_name": path.split("/")[-1],
                        "title": path,
                        "text": text,
                    }
                )

            meta_bits = [
                f"Repository: {repo.get('full_name')}",
                f"Description: {repo.get('description') or 'N/A'}",
                f"Default branch: {repo.get('default_branch')}",
                f"Languages: {', '.join((repo.get('languages') or {}).keys()) or 'N/A'}",
                f"Important files: {', '.join(repo.get('important_files') or []) or 'N/A'}",
                (
                    "Documentation files: "
                    + (", ".join(item.get("path") or "" for item in documentation_files) or "N/A")
                ),
                f"Structure sample: {', '.join((repo.get('structure') or [])[:40])}",
            ]
            sources.append(
                {
                    "source_type": "repository_meta",
                    "source_id": str(repo["_id"]),
                    "file_name": "repository_metadata.txt",
                    "title": f"{repo.get('full_name', 'repository')} metadata",
                    "text": "\n".join(meta_bits),
                }
            )

        cursor = self.documents.find({"project_id": project_id})
        async for doc in cursor:
            text = (doc.get("extracted_text") or "").strip()
            if not text:
                continue
            sources.append(
                {
                    "source_type": "document",
                    "source_id": str(doc["_id"]),
                    "file_name": doc.get("file_name") or "document",
                    "title": doc.get("file_name") or "document",
                    "text": text,
                }
            )

        logger.info(
            "Indexing sources project_id=%s count=%s files=%s",
            project_id,
            len(sources),
            [source.get("file_name") for source in sources],
        )
        return sources

    async def _ensure_documentation_files(self, repo: dict[str, Any]) -> list[dict[str, Any]]:
        existing = [
            item
            for item in (repo.get("documentation_files") or [])
            if isinstance(item, dict) and (item.get("content") or "").strip()
        ]
        if existing:
            return existing

        repository_url = repo.get("repository_url")
        if not repository_url:
            return []

        github = services.github
        fetch = getattr(github, "fetch_documentation_files", None)
        if fetch is None:
            return []

        try:
            fetched = await fetch(repository_url, repo.get("structure") or [])
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not fetch repository documentation files: %s", exc)
            return []

        cleaned = [
            {"path": item.get("path"), "content": item.get("content")}
            for item in (fetched or [])
            if isinstance(item, dict) and (item.get("content") or "").strip()
        ]
        if cleaned:
            await self.repositories.update_one(
                {"_id": repo["_id"]},
                {"$set": {"documentation_files": cleaned, "updated_at": utc_now()}},
            )
            logger.info(
                "Fetched %s repository documentation files for %s",
                len(cleaned),
                repository_url,
            )
        return cleaned

    async def _embed_batched(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for start in range(0, len(texts), BATCH_SIZE):
            batch = texts[start : start + BATCH_SIZE]
            vectors.extend(await self.embeddings.embed_texts(batch))
        return vectors
