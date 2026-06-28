"""
FastAPI dependency providers.

All shared application resources (vector store, chunker, retriever)
are provided through FastAPI's Depends() system. Endpoints receive
the abstract VectorStore type, never a concrete implementation class.

This makes it trivial to:
  - Swap ChromaDB for Vertex AI (change one line here, nowhere else)
  - Override dependencies in tests with mock implementations
  - Add middleware or caching around any resource

Usage in an endpoint:
    from fastapi import Depends
    from app.core.dependencies import get_vector_store, get_chunker
    from app.rag.vector_store import VectorStore

    @router.post("/upload")
    async def upload(
        vector_store: VectorStore = Depends(get_vector_store),
        chunker: DocumentChunker = Depends(get_chunker),
    ) -> dict:
        ...
"""

from fastapi import Request

from app.rag.chunker import DocumentChunker
from app.rag.vector_store import VectorStore
from app.core.config import settings


def get_vector_store(request: Request) -> VectorStore:
    """Return the application-scoped VectorStore singleton.

    Initialised once in main.py lifespan and stored in app.state.
    All endpoints share the same instance — ChromaDB's PersistentClient
    is safe for concurrent reads from a single process.
    """
    return request.app.state.vector_store


def get_chunker() -> DocumentChunker:
    """Return a DocumentChunker configured from application settings.

    A new instance per request is fine — DocumentChunker holds no state
    between calls, only the splitter configuration.
    """
    return DocumentChunker(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
