"""
Abstract VectorStore interface and shared data types.

All application code — RAG chains, document services, LangGraph agents —
depends on this interface, never on a specific implementation.

Implementations:
  ChromaVectorStore  → chroma_store.py   (Phase 2, local dev + Cloud Run)
  VertexAIVectorStore → vertex_store.py  (Phase 5, production scale)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


# ─── Shared types ─────────────────────────────────────────────────────────────


@dataclass
class ChunkMetadata:
    """Metadata stored alongside every chunk in the vector store.

    Populated by DocumentChunker and persisted in ChromaDB / Vertex AI.
    Enables source citations, per-document deletion, and audit trails.

    source_uri holds the GCS URI (gs://bucket/documents/{id}/{file})
    for the original PDF. Used for audit trails and re-indexing.
    """

    document_id: str
    document_name: str
    source_uri: str
    page_number: int
    created_at: str

    # chunk_id and chunk_index are added by the chunker at split time
    chunk_id: str = ""
    chunk_index: int = 0


@dataclass
class DocumentChunk:
    """A single text chunk ready to be embedded and stored."""

    content: str
    chunk_id: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchResult:
    """A single result returned by similarity_search."""

    content: str
    metadata: dict[str, Any]
    score: float
    chunk_id: str


# ─── Abstract interface ───────────────────────────────────────────────────────


class VectorStore(ABC):
    """Contract for all vector store implementations.

    Implementations must be thread-safe. All methods are synchronous
    because ChromaDB's Python client is synchronous; async wrappers
    can be added at the service layer if needed.
    """

    @abstractmethod
    def add_documents(self, chunks: list[DocumentChunk]) -> None:
        """Embed and persist a list of chunks.

        Implementations should be idempotent: re-adding a chunk with the
        same chunk_id should upsert rather than duplicate.
        """

    @abstractmethod
    def similarity_search(
        self,
        query: str,
        k: int = 5,
        filter: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Return the top-k most semantically similar chunks.

        Args:
            query: Natural language query string.
            k: Number of results to return.
            filter: Optional metadata filter (e.g. {"document_id": "abc"}).
        """

    @abstractmethod
    def delete_document(self, document_id: str) -> None:
        """Delete all chunks belonging to a document.

        Uses the document_id metadata field to find and remove all chunks
        created from that document.
        """

    @abstractmethod
    def reset(self) -> None:
        """Wipe the entire collection.

        Intended for development and testing only.
        Never call this in production.
        """

    @abstractmethod
    def as_retriever(self, k: int = 5, filter: dict[str, Any] | None = None):
        """Return a LangChain BaseRetriever backed by this store.

        The returned retriever is compatible with:
          - RetrievalQA
          - ConversationalRetrievalChain
          - LangGraph nodes that call .invoke() on a retriever
        """

    @abstractmethod
    def document_count(self) -> int:
        """Return the total number of chunks currently stored."""
