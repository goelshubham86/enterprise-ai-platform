"""RAG package — vector store abstraction and document processing pipeline."""

from app.rag.vector_store import (
    ChunkMetadata,
    DocumentChunk,
    SearchResult,
    VectorStore,
)
from app.rag.chroma_store import ChromaVectorStore
from app.rag.chunker import DocumentChunker, generate_document_id
from app.rag.embedding_service import EmbeddingService, VertexAIEmbeddingService
from app.rag.retriever import build_retriever

__all__ = [
    "VectorStore",
    "ChromaVectorStore",
    "DocumentChunk",
    "ChunkMetadata",
    "SearchResult",
    "DocumentChunker",
    "generate_document_id",
    "EmbeddingService",
    "VertexAIEmbeddingService",
    "build_retriever",
]
