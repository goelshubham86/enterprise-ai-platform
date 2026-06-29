"""
Ingestion orchestrator — coordinates the full document ingestion pipeline.

This is the ONLY component that knows the complete ingestion sequence.
Individual services (StorageService, PDFService, DocumentChunker, VectorStore)
know nothing about the pipeline — they only know their own responsibility.

Pipeline sequence:
    1. Upload PDF bytes to GCS → get source_uri
    2. Extract text from PDF → get ExtractedDocument (pages + text)
    3. Chunk pages → get list[DocumentChunk] with metadata
    4. Store chunks in VectorStore → embeddings generated internally by ChromaDB
    5. Return ProcessingResult

Design decisions:
    - IngestionService is synchronous. ChromaDB's Python client is synchronous,
      and GCS upload is I/O bound. The FastAPI endpoint wraps the call in
      asyncio.to_thread() to avoid blocking the event loop.
    - Each pipeline stage is timed individually so slow stages are visible
      in structured logs (Cloud Logging → Metrics → Alerting).
    - The orchestrator catches PlatformError subtypes only. Unknown exceptions
      propagate to the API layer, which catches them as a safety net.
    - IngestionService has no knowledge of HTTP, FastAPI, or Pydantic.
      It accepts and returns pure Python types.

LangGraph migration path (Phase 4):
    Each private _stage_* method maps directly to a LangGraph node.
    The orchestrator can be replaced by a LangGraph StateGraph where:
        upload_node → extract_node → chunk_node → index_node
    Each node calls the same service methods. Zero changes to services needed.
"""

from __future__ import annotations

import logging
import time

from app.core.exceptions import (
    EmbeddingError,
    PDFExtractionError,
    PlatformError,
    StorageError,
    VectorStoreError,
)
from app.models.document import ExtractedDocument, IngestionStatus, ProcessingResult
from app.rag.chunker import DocumentChunker
from app.rag.vector_store import DocumentChunk, VectorStore
from app.services.pdf_service import PDFService
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)


class IngestionService:
    """Orchestrates the document ingestion pipeline.

    Injected with all required services via constructor. This makes the
    orchestrator trivially testable — replace any service with a mock.

    Usage (via FastAPI DI):
        service = IngestionService(
            storage=StorageService(...),
            pdf=PDFService(),
            chunker=DocumentChunker(...),
            vector_store=ChromaVectorStore(...),
        )
        result = service.ingest_document(document_id, filename, content)
    """

    def __init__(
        self,
        storage: StorageService,
        pdf: PDFService,
        chunker: DocumentChunker,
        vector_store: VectorStore,
    ) -> None:
        self._storage = storage
        self._pdf = pdf
        self._chunker = chunker
        self._vector_store = vector_store

    # ─── Public interface ──────────────────────────────────────────────────────

    def ingest_document(
        self,
        document_id: str,
        filename: str,
        content: bytes,
    ) -> ProcessingResult:
        """Run the full ingestion pipeline for a single document.

        This is a synchronous, blocking call. The FastAPI endpoint must
        run it in a thread pool via asyncio.to_thread().

        Args:
            document_id: Pre-generated UUID (created in the API layer).
            filename: Original filename (used for GCS path and metadata).
            content: Raw PDF bytes from the uploaded file.

        Returns:
            ProcessingResult with all pipeline metrics and the final status.

        Raises:
            InvalidPDFError: The file is not a valid PDF (caller error).
            StorageError: GCS upload failed (infrastructure error).
            PDFExtractionError: Text extraction failed (infrastructure error).
            EmbeddingError: Vertex AI embedding call failed (infrastructure error).
            VectorStoreError: ChromaDB write failed (infrastructure error).
        """
        pipeline_start = time.perf_counter()

        logger.info(
            "Ingestion pipeline started",
            extra={"document_id": document_id, "file_name": filename, "size_bytes": len(content)},
        )

        # Stage 1: Upload to GCS
        source_uri = self._stage_upload(document_id, filename, content)

        # Stage 2: Extract PDF text
        extracted = self._stage_extract(document_id, filename, content)

        # Stage 3: Chunk pages
        chunks = self._stage_chunk(document_id, filename, source_uri, extracted)

        # Stage 4: Index into vector store (embeddings generated here)
        self._stage_index(document_id, chunks)

        # Build result
        elapsed_ms = (time.perf_counter() - pipeline_start) * 1000
        result = ProcessingResult(
            document_id=document_id,
            document_name=filename,
            source_uri=source_uri,
            total_pages=extracted.total_pages,
            non_empty_pages=len(extracted.non_empty_pages),
            total_chunks=len(chunks),
            processing_time_ms=elapsed_ms,
            status=IngestionStatus.INDEXED,
        )

        logger.info(
            "Ingestion pipeline complete",
            extra={
                "document_id": document_id,
                "file_name": filename,
                "total_pages": result.total_pages,
                "non_empty_pages": result.non_empty_pages,
                "total_chunks": result.total_chunks,
                "elapsed_ms": round(elapsed_ms, 2),
                "status": result.status.value,
            },
        )

        return result

    # ─── Pipeline stages ───────────────────────────────────────────────────────

    def _stage_upload(self, document_id: str, filename: str, content: bytes) -> str:
        """Stage 1: Upload PDF to GCS.

        Returns:
            GCS URI (gs://bucket/documents/{document_id}/{filename})
        """
        stage_start = time.perf_counter()
        logger.debug(
            "Stage 1/4: uploading to GCS",
            extra={"document_id": document_id, "stage": "upload"},
        )

        try:
            source_uri = self._storage.upload_document(
                document_id=document_id,
                filename=filename,
                content=content,
            )
        except StorageError:
            raise  # Already wrapped with context by StorageService
        except Exception as exc:
            raise StorageError(
                f"Unexpected error during GCS upload (document_id={document_id})",
                cause=exc,
            ) from exc

        elapsed_ms = (time.perf_counter() - stage_start) * 1000
        logger.info(
            "Stage 1/4 complete: GCS upload",
            extra={
                "document_id": document_id,
                "stage": "upload",
                "source_uri": source_uri,
                "elapsed_ms": round(elapsed_ms, 2),
            },
        )
        return source_uri

    def _stage_extract(
        self, document_id: str, filename: str, content: bytes
    ) -> ExtractedDocument:
        """Stage 2: Extract text from PDF.

        Returns:
            ExtractedDocument with one ExtractedPage per PDF page.
        """
        stage_start = time.perf_counter()
        logger.debug(
            "Stage 2/4: extracting PDF text",
            extra={"document_id": document_id, "stage": "extract"},
        )

        try:
            extracted = self._pdf.extract(
                content=content,
                document_id=document_id,
                document_name=filename,
            )
        except PDFExtractionError:
            raise
        except Exception as exc:
            raise PDFExtractionError(
                f"Unexpected error during PDF extraction (document_id={document_id})",
                cause=exc,
            ) from exc

        elapsed_ms = (time.perf_counter() - stage_start) * 1000
        logger.info(
            "Stage 2/4 complete: PDF extraction",
            extra={
                "document_id": document_id,
                "stage": "extract",
                "total_pages": extracted.total_pages,
                "total_chars": extracted.total_chars,
                "elapsed_ms": round(elapsed_ms, 2),
            },
        )
        return extracted

    def _stage_chunk(
        self,
        document_id: str,
        filename: str,
        source_uri: str,
        extracted: ExtractedDocument,
    ) -> list[DocumentChunk]:
        """Stage 3: Split extracted pages into chunks.

        Returns:
            Flat list of DocumentChunk objects with full metadata.
        """
        stage_start = time.perf_counter()
        logger.debug(
            "Stage 3/4: chunking document",
            extra={"document_id": document_id, "stage": "chunk"},
        )

        chunks = self._chunker.chunk_pages(
            pages=extracted.page_texts(),
            document_id=document_id,
            document_name=filename,
            source_uri=source_uri,
        )

        elapsed_ms = (time.perf_counter() - stage_start) * 1000
        logger.info(
            "Stage 3/4 complete: chunking",
            extra={
                "document_id": document_id,
                "stage": "chunk",
                "chunk_count": len(chunks),
                "elapsed_ms": round(elapsed_ms, 2),
            },
        )

        if not chunks:
            logger.warning(
                "Document produced zero chunks — likely all pages are image-only",
                extra={"document_id": document_id, "file_name": filename},
            )

        return chunks

    def _stage_index(self, document_id: str, chunks: list[DocumentChunk]) -> None:
        """Stage 4: Embed and index chunks in the vector store.

        ChromaVectorStore.add_documents() triggers Vertex AI embedding
        generation internally via the LangChain integration. The orchestrator
        does not call Vertex AI directly.

        Empty chunk lists are handled gracefully — no-op with a warning.
        """
        if not chunks:
            logger.warning(
                "Stage 4/4 skipped: no chunks to index",
                extra={"document_id": document_id, "stage": "index"},
            )
            return

        stage_start = time.perf_counter()
        logger.debug(
            "Stage 4/4: indexing chunks",
            extra={"document_id": document_id, "stage": "index", "chunk_count": len(chunks)},
        )

        try:
            self._vector_store.add_documents(chunks)
        except Exception as exc:
            raise VectorStoreError(
                f"Failed to index {len(chunks)} chunks for document_id={document_id}",
                cause=exc,
            ) from exc

        elapsed_ms = (time.perf_counter() - stage_start) * 1000
        logger.info(
            "Stage 4/4 complete: indexing",
            extra={
                "document_id": document_id,
                "stage": "index",
                "chunk_count": len(chunks),
                "elapsed_ms": round(elapsed_ms, 2),
            },
        )
