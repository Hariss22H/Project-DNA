"""Application configuration loaded from environment variables."""

from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central settings for the Project DNA API."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Project DNA API"
    app_env: str = "development"
    debug: bool = True
    api_v1_prefix: str = "/api"

    jwt_secret: str = "dev-only-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "project_dna"

    qdrant_url: str = ""
    qdrant_api_key: str = ""
    qdrant_collection: str = "project_dna_chunks"

    openai_api_key: str = ""
    gemini_api_key: str = ""
    openai_chat_model: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-3-small"
    gemini_fallback_model: str = "gemini-2.5-flash"
    embedding_dimensions: int = 1536
    chunk_size_tokens: int = 800
    chunk_overlap_tokens: int = 120
    rag_top_k: int = 8
    rag_min_score: float = 0.05

    github_token: str = ""

    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @field_validator("api_v1_prefix")
    @classmethod
    def normalize_prefix(cls, value: str) -> str:
        value = value.strip() or "/api"
        if not value.startswith("/"):
            value = f"/{value}"
        return value.rstrip("/") or "/api"

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_development(self) -> bool:
        return self.app_env.lower() in {"development", "dev", "local", "test"}


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
