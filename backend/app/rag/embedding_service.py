"""
Embedding service abstraction.

All vector store implementations receive a LangChain Embeddings object,
not a vendor-specific client. This means the embedding model can be
swapped independently of the vector store.

Current implementation: Vertex AI text-embedding-004
Future options:
  - text-embedding-005 or later Vertex AI models
  - sentence-transformers for fully local dev (no GCP credentials needed)
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod

from langchain_core.embeddings import Embeddings

logger = logging.getLogger(__name__)


# ─── Abstract interface ───────────────────────────────────────────────────────


class EmbeddingService(ABC):
    """Contract for embedding service implementations.

    Returns a LangChain Embeddings object so it works directly with
    ChromaDB, Vertex AI Vector Search, and any other LangChain-compatible store.
    """

    @abstractmethod
    def get_embeddings(self) -> Embeddings:
        """Return the configured LangChain Embeddings instance."""


# ─── Vertex AI implementation ─────────────────────────────────────────────────


class VertexAIEmbeddingService(EmbeddingService):
    """Google Vertex AI embeddings via langchain-google-vertexai.

    Model: text-embedding-004
      - 768-dimensional dense embeddings
      - Optimised for semantic similarity and retrieval tasks
      - Supports task_type: RETRIEVAL_DOCUMENT / RETRIEVAL_QUERY

    Credentials: uses Application Default Credentials (ADC).
    Run `gcloud auth application-default login` for local development.
    Cloud Run uses the service account attached to the instance automatically.
    """

    def __init__(self, model: str, project: str) -> None:
        from langchain_google_vertexai import VertexAIEmbeddings

        self._embeddings = VertexAIEmbeddings(
            model_name=model,
            project=project,
        )
        logger.info("VertexAIEmbeddingService initialised with model='%s'", model)

    def get_embeddings(self) -> Embeddings:
        return self._embeddings


# ─── Future: local embeddings for offline dev ─────────────────────────────────
#
# class SentenceTransformerEmbeddingService(EmbeddingService):
#     """Fully local embeddings — no GCP credentials required.
#
#     Useful for running the full RAG pipeline in CI or on laptops without
#     access to Vertex AI. Swap in via EMBEDDING_BACKEND=local in .env.
#
#     pip install sentence-transformers
#     """
#
#     def __init__(self, model: str = "all-MiniLM-L6-v2") -> None:
#         from langchain_community.embeddings import HuggingFaceEmbeddings
#         self._embeddings = HuggingFaceEmbeddings(model_name=model)
#
#     def get_embeddings(self) -> Embeddings:
#         return self._embeddings
