"""
Centralised application configuration via environment variables.

All configuration values are defined here and accessed as:
    from app.core.config import settings
    settings.gcs_bucket_name

Never import os.getenv() directly in services or endpoints.
All env var reading happens in this file only.

Local development:
    Copy backend/.env.example → backend/.env and fill in values.
    Pydantic-settings reads .env automatically.

Cloud Run:
    Set environment variables in the Cloud Run service definition
    (Terraform or Cloud Build substitutions). Do not commit .env files.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ─── GCP ──────────────────────────────────────────────────────────────────
    gcp_project_id: str = "your-gcp-project-id"
    gcp_region: str = "us-central1"

    # ─── Cloud Storage ────────────────────────────────────────────────────────
    gcs_bucket_name: str = "enterprise-ai-documents"
    # Prefix (folder) under which all uploaded PDFs are stored.
    # Final GCS path: {gcs_upload_prefix}/{document_id}/{filename}
    gcs_upload_prefix: str = "documents"

    # ─── Vertex AI ────────────────────────────────────────────────────────────
    vertex_model_id: str = "gemini-1.5-pro-002"
    vertex_embedding_model: str = "text-embedding-004"
    # How many chunks to embed per Vertex AI API call.
    # text-embedding-004 supports up to 250 inputs per request.
    embedding_batch_size: int = Field(default=100, ge=1, le=250)

    # ─── Application ──────────────────────────────────────────────────────────
    app_env: str = "development"
    # Allowed CORS origins for the frontend.
    # The Cloud Run backend must be deployed with --allow-unauthenticated
    # so that browser OPTIONS preflight requests reach FastAPI before Cloud
    # Run IAM can reject them. Default includes the production frontend URL
    # so no CORS_ORIGINS env var is needed in dev deployments.
    # Override via CORS_ORIGINS env var (JSON array) for staging/prod.
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "https://enterprise-ai-frontend-611331021574.us-central1.run.app",
    ]
    log_level: str = "INFO"

    # ─── Ingestion: file validation ────────────────────────────────────────────
    # Maximum file size accepted by the upload endpoint.
    # Enforced before any GCS or Vertex AI calls are made.
    max_file_size_mb: int = Field(default=50, ge=1, le=500)

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024

    # ─── RAG: chunking ────────────────────────────────────────────────────────
    chunk_size: int = Field(default=512, ge=64, le=4096)
    chunk_overlap: int = Field(default=64, ge=0, le=512)
    top_k: int = Field(default=5, ge=1, le=50)

    # ─── ChromaDB ─────────────────────────────────────────────────────────────
    # Persistent storage directory for the embedded ChromaDB database.
    # Override with CHROMA_PERSIST_DIR env var in Cloud Run.
    # In Phase 5, replaced by Vertex AI Vector Search.
    chroma_persist_dir: str = "data/chroma"
    chroma_collection_name: str = "documents"


settings = Settings()
