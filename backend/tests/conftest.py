"""
Shared test fixtures and lightweight fakes.

Design principles:
    - Zero GCP credentials required. All GCS and Vertex AI calls are replaced
      by in-memory fakes.
    - Fakes implement the same abstract interface (VectorStore ABC) so they
      prove interface compatibility, not just call-count behaviour.
    - PDF bytes are generated using pypdf's PdfWriter — the same library
      used in production — so there is no external test-data dependency.
    - The FastAPI lifespan (which initialises GCP clients) is replaced with
      a null context manager so TestClient can start without credentials.

Fixtures summary:
    blank_pdf_bytes(n)      → valid n-page PDF with no text (blank pages)
    two_page_pdf_bytes      → convenience alias for blank_pdf_bytes(2)
    not_a_pdf_bytes         → bytes that are not a PDF
    empty_bytes             → b""
    document_id             → random UUID string
    document_name           → "test_report.pdf"
    vector_store            → InMemoryVectorStore instance
    storage_service         → FakeStorageService instance
    processing_result       → ProcessingResult with realistic values
    client                  → TestClient with GCP lifespan bypassed
    client_with_ingestion   → TestClient + mocked IngestionService (for upload tests)
"""

from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.models.document import ExtractedDocument, ExtractedPage, IngestionStatus, ProcessingResult
from app.rag.vector_store import DocumentChunk, SearchResult, VectorStore
from tests.helpers import make_blank_pdf


@pytest.fixture(scope="session")
def two_page_pdf_bytes() -> bytes:
    """Valid two-page PDF (blank pages). Session-scoped for speed."""
    return make_blank_pdf(num_pages=2)


@pytest.fixture(scope="session")
def single_page_pdf_bytes() -> bytes:
    """Valid single-page PDF (blank page). Session-scoped for speed."""
    return make_blank_pdf(num_pages=1)


@pytest.fixture
def not_a_pdf_bytes() -> bytes:
    return b"This is definitely not a PDF document."


@pytest.fixture
def empty_bytes() -> bytes:
    return b""


# ─── Document identity fixtures ───────────────────────────────────────────────


@pytest.fixture
def document_id() -> str:
    return str(uuid.uuid4())


@pytest.fixture
def document_name() -> str:
    return "test_report.pdf"


# ─── In-memory VectorStore ────────────────────────────────────────────────────


class InMemoryVectorStore(VectorStore):
    """Thread-safe in-memory VectorStore for unit tests.

    Implements the full VectorStore ABC. Records every add_documents call
    so tests can assert on what was stored. similarity_search always returns
    an empty list (retrieval is not under test in ingestion tests).
    """

    def __init__(self) -> None:
        self.stored_chunks: list[DocumentChunk] = []
        self.deleted_document_ids: list[str] = []
        self._reset_count = 0

    def add_documents(self, chunks: list[DocumentChunk]) -> None:
        self.stored_chunks.extend(chunks)

    def similarity_search(
        self,
        query: str,
        k: int = 5,
        filter: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        return []

    def delete_document(self, document_id: str) -> None:
        self.deleted_document_ids.append(document_id)
        self.stored_chunks = [
            c for c in self.stored_chunks
            if c.metadata.get("document_id") != document_id
        ]

    def reset(self) -> None:
        self._reset_count += 1
        self.stored_chunks.clear()
        self.deleted_document_ids.clear()

    def as_retriever(self, k: int = 5, filter: dict[str, Any] | None = None):
        return MagicMock()

    def document_count(self) -> int:
        return len(self.stored_chunks)


@pytest.fixture
def vector_store() -> InMemoryVectorStore:
    return InMemoryVectorStore()


# ─── Fake StorageService ───────────────────────────────────────────────────────


class FakeStorageService:
    """In-memory StorageService. Records uploads, returns deterministic GCS URIs.

    Does not import google.cloud.storage. No network calls.
    """

    BUCKET = "test-bucket"
    PREFIX = "documents"

    def __init__(self) -> None:
        self.uploads: list[dict] = []

    def upload_document(
        self,
        document_id: str,
        filename: str,
        content: bytes,
        content_type: str = "application/pdf",
    ) -> str:
        safe_filename = filename.replace(" ", "_")
        uri = f"gs://{self.BUCKET}/{self.PREFIX}/{document_id}/{safe_filename}"
        self.uploads.append({
            "document_id": document_id,
            "filename": filename,
            "uri": uri,
            "size": len(content),
        })
        return uri

    def get_blob_metadata(self, gcs_uri: str) -> dict:
        return {"name": gcs_uri, "size": 1024, "content_type": "application/pdf"}

    def delete_document(self, document_id: str, filename: str) -> None:
        self.uploads = [u for u in self.uploads if u["document_id"] != document_id]


@pytest.fixture
def storage_service() -> FakeStorageService:
    return FakeStorageService()


# ─── ProcessingResult fixture ──────────────────────────────────────────────────


@pytest.fixture
def processing_result(document_id: str, document_name: str) -> ProcessingResult:
    return ProcessingResult(
        document_id=document_id,
        document_name=document_name,
        source_uri=f"gs://test-bucket/documents/{document_id}/{document_name}",
        total_pages=2,
        non_empty_pages=2,
        total_chunks=8,
        processing_time_ms=1215.7,
        status=IngestionStatus.INDEXED,
    )


# ─── FastAPI test client ───────────────────────────────────────────────────────
#
# The main.py lifespan connects to Vertex AI, ChromaDB, and GCS on startup.
# For API tests, we replace the lifespan with a null context manager so that
# TestClient can start without any GCP credentials.
#
# For endpoints that depend on injected services (like the upload endpoint),
# we additionally override `get_ingestion_service` in `app.dependency_overrides`.


@asynccontextmanager
async def _null_lifespan(_app):
    """No-op lifespan that simulates a fully-initialised application.

    Sets the same app.state attributes that the real lifespan populates so
    that health checks and dependency guards see a consistent "ready" state.
    Service singletons are left as None because endpoints that need them
    either use dependency_overrides (upload tests) or don't touch services
    at all (health, list, delete stubs).
    """
    _app.state.vector_store = None
    _app.state.storage_service = None
    _app.state.pdf_service = None
    _app.state._services_ready = True
    _app.state._init_error = None
    yield


@pytest.fixture
def client():
    """TestClient with GCP lifespan replaced by a no-op.

    Use this fixture for endpoints that do not require injected services
    (health check, list documents, delete stub, etc.).
    """
    from app.main import app

    original_lifespan = app.router.lifespan_context
    app.router.lifespan_context = _null_lifespan
    try:
        with TestClient(app, raise_server_exceptions=True) as c:
            yield c
    finally:
        app.router.lifespan_context = original_lifespan
        app.dependency_overrides.clear()


@pytest.fixture
def fake_ingestion_service(storage_service, vector_store, two_page_pdf_bytes):
    """A real IngestionService wired with all-fake dependencies.

    Uses:
        FakeStorageService  → no GCS calls
        PDFService (real)   → real pypdf extraction on blank-page PDF
        DocumentChunker     → real splitter (LangChain, pure Python)
        InMemoryVectorStore → no ChromaDB / Vertex AI calls
    """
    from app.rag.chunker import DocumentChunker
    from app.services.ingestion_service import IngestionService
    from app.services.pdf_service import PDFService

    return IngestionService(
        storage=storage_service,
        pdf=PDFService(),
        chunker=DocumentChunker(chunk_size=128, chunk_overlap=16),
        vector_store=vector_store,
    )


@pytest.fixture
def client_with_ingestion(fake_ingestion_service):
    """TestClient with the ingestion pipeline fully mocked.

    The upload endpoint receives a real IngestionService backed by fakes
    so there are no GCP calls during the test.
    """
    from app.main import app
    from app.core.dependencies import get_ingestion_service

    original_lifespan = app.router.lifespan_context
    app.router.lifespan_context = _null_lifespan
    app.dependency_overrides[get_ingestion_service] = lambda: fake_ingestion_service
    try:
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c
    finally:
        app.router.lifespan_context = original_lifespan
        app.dependency_overrides.clear()
