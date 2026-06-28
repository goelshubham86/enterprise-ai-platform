from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ─── GCP ──────────────────────────────────────────────────────────────────
    gcp_project_id: str = "your-gcp-project-id"
    gcp_region: str = "us-central1"
    gcs_bucket_name: str = "enterprise-ai-documents"

    # ─── Vertex AI ────────────────────────────────────────────────────────────
    vertex_model_id: str = "gemini-1.5-pro-002"
    vertex_embedding_model: str = "text-embedding-004"

    # ─── Application ──────────────────────────────────────────────────────────
    app_env: str = "development"
    cors_origins: List[str] = ["http://localhost:3000"]
    log_level: str = "INFO"

    # ─── RAG: chunking ────────────────────────────────────────────────────────
    chunk_size: int = 512
    chunk_overlap: int = 64
    top_k: int = 5

    # ─── ChromaDB ─────────────────────────────────────────────────────────────
    # Persistent storage directory for the embedded ChromaDB database.
    # Override with CHROMA_PERSIST_DIR env var in Cloud Run.
    # In production (Phase 5) this is replaced by Vertex AI Vector Search.
    chroma_persist_dir: str = "data/chroma"

    # Collection name inside ChromaDB. One collection holds all document chunks.
    # Change this to isolate datasets (e.g. per-tenant in future).
    chroma_collection_name: str = "documents"


settings = Settings()
