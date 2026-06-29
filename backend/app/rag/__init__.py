"""RAG package — vector store abstraction and document processing pipeline.

Only abstract types and stateless utilities are exported from the package
init. Concrete implementations (ChromaVectorStore, VertexAIEmbeddingService)
import heavy dependencies (chromadb, langchain_google_vertexai) and must be
imported lazily — only in main.py lifespan where those packages are guaranteed
to be available. Importing them here would force chromadb and Vertex AI SDK
to load at process start, failing immediately if the packages are missing.
"""

from app.rag.vector_store import (
    ChunkMetadata,
    DocumentChunk,
    SearchResult,
    VectorStore,
)
from app.rag.chunker import DocumentChunker, generate_document_id

__all__ = [
    "VectorStore",
    "DocumentChunk",
    "ChunkMetadata",
    "SearchResult",
    "DocumentChunker",
    "generate_document_id",
]
