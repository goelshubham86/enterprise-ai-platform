from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # GCP
    gcp_project_id: str = "your-gcp-project-id"
    gcp_region: str = "us-central1"
    gcs_bucket_name: str = "enterprise-ai-documents"

    # Vertex AI
    vertex_model_id: str = "gemini-1.5-pro-002"
    vertex_embedding_model: str = "text-embedding-004"

    # Application
    app_env: str = "development"
    cors_origins: List[str] = ["http://localhost:3000"]
    log_level: str = "INFO"

    # RAG
    chunk_size: int = 512
    chunk_overlap: int = 64
    top_k: int = 5


settings = Settings()
