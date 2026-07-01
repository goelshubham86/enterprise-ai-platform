"""
FastAPI dependency providers.

All shared application resources are provided through FastAPI's Depends()
system. Endpoints receive abstract types (VectorStore, not ChromaVectorStore),
which makes it trivial to:
    - Swap ChromaDB for Vertex AI Vector Search (change one line in main.py)
    - Replace GCS with a mock StorageService in tests
    - Override any dependency in tests via app.dependency_overrides

Lifetime strategy:
    - Singletons (created once in lifespan, stored in app.state):
        VectorStore, StorageService, PDFService
    - Per-request (new instance each call, stateless):
        DocumentChunker, IngestionService

Usage in an endpoint:
    from fastapi import Depends
    from app.core.dependencies import get_ingestion_service
    from app.services.ingestion_service import IngestionService

    @router.post("/upload")
    async def upload_document(
        service: IngestionService = Depends(get_ingestion_service),
    ) -> DocumentUploadResponse:
        ...
"""

from __future__ import annotations

from fastapi import Request

from app.core.config import settings
from app.core.exceptions import ServiceNotReadyError
from app.rag.chunker import DocumentChunker
from app.rag.vector_store import VectorStore
from app.services.ingestion_service import IngestionService
from app.services.pdf_service import PDFService
from app.services.storage_service import StorageService


# ─── Singleton providers (read from app.state) ────────────────────────────────
#
# All three singleton providers guard against None — app.state is populated by
# a background asyncio task that starts after the lifespan yields.  If a request
# arrives before init completes, ServiceNotReadyError → HTTP 503 with Retry-After.


def get_vector_store(request: Request) -> VectorStore:
    """Return the application-scoped VectorStore singleton.

    Initialised once in main.py lifespan and stored in app.state.
    All requests share a single ChromaDB PersistentClient connection.

    To swap ChromaDB → Vertex AI Vector Search (Phase 5):
        1. Implement VertexAIVectorStore in app/rag/vertex_store.py
        2. Change the assignment in main.py lifespan
        3. Nothing here changes
    """
    store = request.app.state.vector_store
    if store is None:
        raise ServiceNotReadyError(
            "Vector store is not yet initialised. Services start in the background — "
            "please retry in a moment."
        )
    return store


def get_storage_service(request: Request) -> StorageService:
    """Return the application-scoped StorageService singleton.

    The GCS client is expensive to create — one instance per application
    lifetime is the correct pattern.
    """
    svc = request.app.state.storage_service
    if svc is None:
        raise ServiceNotReadyError(
            "Storage service is not yet initialised. Services start in the background — "
            "please retry in a moment."
        )
    return svc


def get_pdf_service(request: Request) -> PDFService:
    """Return the application-scoped PDFService singleton.

    PDFService is stateless between calls — shared safely across requests.
    """
    svc = request.app.state.pdf_service
    if svc is None:
        raise ServiceNotReadyError(
            "PDF service is not yet initialised. Services start in the background — "
            "please retry in a moment."
        )
    return svc


# ─── Per-request providers ────────────────────────────────────────────────────


def get_chunker() -> DocumentChunker:
    """Return a DocumentChunker configured from application settings.

    A new instance per request is acceptable — DocumentChunker holds only
    the RecursiveCharacterTextSplitter configuration, not request state.
    """
    return DocumentChunker(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )


def get_ingestion_service(request: Request) -> IngestionService:
    """Assemble and return an IngestionService for the current request.

    Pulls singletons from app.state and creates a fresh DocumentChunker.
    All wiring is explicit — no sub-dependency magic needed here.
    """
    return IngestionService(
        storage=get_storage_service(request),
        pdf=get_pdf_service(request),
        chunker=get_chunker(),
        vector_store=get_vector_store(request),
    )
