"""Validated settings loaded from environment variables or a local .env file."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "local"
    data_dir: Path = Path("./data")
    max_upload_mb: int = Field(default=20, ge=1, le=100)
    chunk_size: int = Field(default=900, ge=100, le=5000)
    chunk_overlap: int = Field(default=150, ge=0, le=1000)
    top_k: int = Field(default=5, ge=1, le=20)
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    qdrant_url: str | None = None
    qdrant_api_key: str | None = None
    qdrant_collection: str = "research_notes"
    llm_base_url: str | None = None
    llm_api_key: str | None = None
    llm_model: str | None = None

    @model_validator(mode="after")
    def validate_chunking(self) -> "Settings":
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
