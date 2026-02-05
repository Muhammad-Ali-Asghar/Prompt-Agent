"""
Configuration management for the Prompt RAG Agent.
Uses Pydantic Settings for environment variable handling.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Literal
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Configuration
    app_name: str = "Prompt RAG Agent"
    app_version: str = "1.0.0"
    debug: bool = False

    # Google Gemini API
    google_api_key: str = Field(..., env="GOOGLE_API_KEY")
    gemini_model: str = "gemini-2.5-flash"

    # Authentication
    api_key_header: str = "X-API-Key"
    api_keys: str = Field(default="dev-key-12345", env="API_KEYS")  # Comma-separated

    # Vector Store Configuration
    vector_store_type: Literal["chroma", "pinecone", "weaviate"] = "chroma"
    chroma_persist_dir: str = "./data/chroma_db"
    chroma_collection_name: str = "prompt_rag_docs"

    # Embedding Configuration
    embedding_model: str = "models/text-embedding-004"

    # Chunking Configuration
    chunk_size: int = 1000
    chunk_overlap: int = 200

    # Retrieval Configuration
    retrieval_top_k: int = 8
    retrieval_min_score: float = 0.5

    # Security Configuration
    max_request_size: int = 10240  # 10KB
    log_user_requests: bool = False  # Opt-in for debugging

    # CORS Configuration
    cors_origins: str = "http://localhost:3000,http://localhost:8000"

    @property
    def valid_api_keys(self) -> set[str]:
        """Parse comma-separated API keys into a set."""
        return set(key.strip() for key in self.api_keys.split(",") if key.strip())

    @property
    def cors_origin_list(self) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        return [
            origin.strip() for origin in self.cors_origins.split(",") if origin.strip()
        ]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()
