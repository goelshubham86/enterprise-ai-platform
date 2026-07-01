"""Tests for IngestionService (app/services/ingestion_service.py).

IngestionService is the pipeline orchestrator. Tests use:
    FakeStorageService      → in-memory, no GCS
    PDFService (real)       → real pypdf, blank-page test PDFs
    DocumentChunker (real)  → pure Python LangChain splitter
    InMemoryVectorStore     → in-memory, no ChromaDB / Vertex AI

Tests verify:
    - All 4 pipeline stages are called in the correct order
    - StorageError from stage 1 propagates unchanged
    - VectorStoreError from stage 4 propagates unchanged
    - Blank-page PDFs produce 0 chunks (correct silent behaviour)
    - ProcessingResult carries correct metrics (page count, chunk count, etc.)
    - The source_uri in the result came from StorageService.upload_document()
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.core.exceptions import StorageError, VectorStoreError
from app.models.document import IngestionStatus, ProcessingResult
from app.rag.chunker import DocumentChunker
from app.services.ingestion_service import IngestionService
from app.services.pdf_service import PDFService


@pytest.fixture
def service(storage_service, vector_store) -> IngestionService:
    """Real IngestionService with fake storage and vector store."""
    return IngestionService(
        storage=storage_service,
        pdf=PDFService(),
        chunker=DocumentChunker(chunk_size=64, chunk_overlap=8),
        vector_store=vector_store,
    )


# ─── Happy path ───────────────────────────────────────────────────────────────


class TestIngestionServiceHappyPath:
    def test_returns_processing_result(
        self, service, two_page_pdf_bytes, document_id, document_name
    ):
        result = service.ingest_document(document_id, document_name, two_page_pdf_bytes)
        assert isinstance(result, ProcessingResult)

    def test_result_status_is_indexed(
        self, service, two_page_pdf_bytes, document_id, document_name
    ):
        result = service.ingest_document(document_id, document_name, two_page_pdf_bytes)
        assert result.status == IngestionStatus.INDEXED

    def test_result_document_id_matches(
        self, service, two_page_pdf_bytes, document_id, document_name
    ):
        result = service.ingest_document(document_id, document_name, two_page_pdf_bytes)
        assert result.document_id == document_id

    def test_result_document_name_matches(
        self, service, two_page_pdf_bytes, document_id, document_name
    ):
        result = service.ingest_document(document_id, document_name, two_page_pdf_bytes)
        assert result.document_name == document_name

    def test_result_total_pages_is_two(
        self, service, two_page_pdf_bytes, document_id, document_name
    ):
        result = service.ingest_document(document_id, document_name, two_page_pdf_bytes)
        assert result.total_pages == 2

    def test_source_uri_came_from_storage_service(
        self, service, storage_service, two_page_pdf_bytes, document_id, document_name
    ):
        result = service.ingest_document(document_id, document_name, two_page_pdf_bytes)
        # FakeStorageService returns gs://test-bucket/documents/{id}/{name}
        assert result.source_uri.startswith("gs://test-bucket/")
        assert document_id in result.source_uri

    def test_file_uploaded_to_storage(
        self, service, storage_service, two_page_pdf_bytes, document_id, document_name
    ):
        service.ingest_document(document_id, document_name, two_page_pdf_bytes)
        assert len(storage_service.uploads) == 1
        assert storage_service.uploads[0]["document_id"] == document_id

    def test_processing_time_is_positive(
        self, service, two_page_pdf_bytes, document_id, document_name
    ):
        result = service.ingest_document(document_id, document_name, two_page_pdf_bytes)
        assert result.processing_time_ms > 0

    def test_blank_pdf_produces_zero_chunks(
        self, service, vector_store, two_page_pdf_bytes, document_id, document_name
    ):
        """Blank-page PDFs have no extractable text → no chunks → vector store empty."""
        result = service.ingest_document(document_id, document_name, two_page_pdf_bytes)
        assert result.total_chunks == 0
        assert vector_store.document_count() == 0


# ─── Stage 1 — StorageError propagation ──────────────────────────────────────


class TestIngestionServiceStage1Failure:
    def test_storage_error_propagates(
        self, storage_service, vector_store, two_page_pdf_bytes, document_id, document_name
    ):
        failing_storage = MagicMock()
        failing_storage.upload_document.side_effect = StorageError("GCS unreachable")

        svc = IngestionService(
            storage=failing_storage,
            pdf=PDFService(),
            chunker=DocumentChunker(),
            vector_store=vector_store,
        )

        with pytest.raises(StorageError, match="GCS unreachable"):
            svc.ingest_document(document_id, document_name, two_page_pdf_bytes)

    def test_storage_failure_means_no_chunks_stored(
        self, vector_store, two_page_pdf_bytes, document_id, document_name
    ):
        failing_storage = MagicMock()
        failing_storage.upload_document.side_effect = StorageError("upload failed")

        svc = IngestionService(
            storage=failing_storage,
            pdf=PDFService(),
            chunker=DocumentChunker(),
            vector_store=vector_store,
        )

        with pytest.raises(StorageError):
            svc.ingest_document(document_id, document_name, two_page_pdf_bytes)

        assert vector_store.document_count() == 0


# ─── Stage 4 — VectorStoreError propagation ───────────────────────────────────


class TestIngestionServiceStage4Failure:
    def test_vector_store_error_is_wrapped(
        self, storage_service, document_id, document_name
    ):
        """If VectorStore.add_documents() raises, a VectorStoreError is raised."""
        failing_store = MagicMock()
        failing_store.add_documents.side_effect = Exception("ChromaDB disk full")

        # Use text PDF bytes so chunking actually produces chunks to index
        # For this test we need a PDF that produces chunks. Since blank PDFs
        # have no text, we mock the PDFService to return a page with real text.
        from app.models.document import ExtractedDocument, ExtractedPage
        from app.services.pdf_service import PDFService

        fake_pdf = MagicMock(spec=PDFService)
        fake_pdf.extract.return_value = ExtractedDocument(
            document_id=document_id,
            document_name=document_name,
            pages=[
                ExtractedPage(
                    page_number=0,
                    text="This is enough text to produce at least one chunk for indexing.",
                )
            ],
        )

        svc = IngestionService(
            storage=storage_service,
            pdf=fake_pdf,
            chunker=DocumentChunker(chunk_size=64, chunk_overlap=8),
            vector_store=failing_store,
        )

        with pytest.raises(VectorStoreError, match="Failed to index"):
            svc.ingest_document(document_id, document_name, b"%PDF-fake")


# ─── Stage order — verify stages run in sequence ─────────────────────────────


class TestIngestionServiceStageOrder:
    def test_storage_called_before_pdf_extract(
        self, two_page_pdf_bytes, document_id, document_name, vector_store
    ):
        """If storage raises, PDFService.extract() is never called."""
        failing_storage = MagicMock()
        failing_storage.upload_document.side_effect = StorageError("fail early")

        mock_pdf = MagicMock(spec=PDFService)

        svc = IngestionService(
            storage=failing_storage,
            pdf=mock_pdf,
            chunker=DocumentChunker(),
            vector_store=vector_store,
        )

        with pytest.raises(StorageError):
            svc.ingest_document(document_id, document_name, two_page_pdf_bytes)

        mock_pdf.extract.assert_not_called()
