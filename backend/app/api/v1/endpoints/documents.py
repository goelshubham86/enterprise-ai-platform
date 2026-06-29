"""
Document management API endpoints.

Implements:
    POST /documents/upload   — ingest a PDF into the platform
    GET  /documents          — list indexed documents (Phase 2 stub)
    DELETE /documents/{id}   — remove a document (Phase 2 stub)
    POST /documents/{id}/reindex — re-index a document (Phase 2 stub)

Design rules enforced here:
    - All business logic lives in IngestionService (app/services/).
    - This file handles only HTTP concerns: file reading, input validation,
      dependency injection, exception → HTTP status translation, and
      schema serialisation.
    - The endpoint runs the blocking IngestionService call in a thread
      pool via asyncio.to_thread() to avoid stalling the event loop.
    - Domain exceptions bubble up to the registered exception handlers
      in main.py. We only catch exceptions we need to handle locally
      (e.g. FileTooLargeError, which must be checked before reading bytes).
"""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Depends, File, Request, UploadFile

from app.core.config import settings
from app.core.dependencies import get_ingestion_service
from app.core.exceptions import FileTooLargeError, InvalidPDFError
from app.rag.chunker import generate_document_id
from app.schemas.document import DocumentListResponse, DocumentUploadResponse
from app.services.ingestion_service import IngestionService

router = APIRouter()
logger = logging.getLogger(__name__)

_ALLOWED_CONTENT_TYPES = {"application/pdf"}
_ALLOWED_EXTENSIONS = {".pdf"}


# ─── POST /documents/upload ───────────────────────────────────────────────────


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=200,
    summary="Upload and index a PDF document",
    description=(
        "Accepts a single PDF file. Uploads it to Google Cloud Storage, "
        "extracts text page-by-page, splits into chunks, generates Vertex AI "
        "embeddings, and stores everything in ChromaDB. "
        "Returns indexing metrics on success."
    ),
    responses={
        200: {"description": "Document successfully indexed"},
        413: {"description": "File exceeds size limit"},
        422: {"description": "Invalid or unreadable PDF"},
        502: {"description": "Downstream service failure (GCS, Vertex AI, or ChromaDB)"},
    },
)
async def upload_document(
    request: Request,
    file: UploadFile = File(..., description="PDF file to ingest (max 50 MB by default)"),
    ingestion_service: IngestionService = Depends(get_ingestion_service),
) -> DocumentUploadResponse:
    """Ingest a PDF document into the platform.

    Pipeline:
        1. Validate content-type and file extension (fast, no I/O)
        2. Read bytes and enforce size limit (before GCS upload)
        3. Generate a stable document_id
        4. Run IngestionService.ingest_document() in a thread pool
        5. Return DocumentUploadResponse

    All domain exceptions propagate to the exception handlers in main.py.
    """
    document_id = generate_document_id()
    filename = file.filename or "upload.pdf"

    logger.info(
        "Upload request received",
        extra={
            "document_id": document_id,
            "file_name": filename,
            "content_type": file.content_type,
        },
    )

    # ── Step 1: Fast validation (no I/O) ─────────────────────────────────────
    _validate_file_type(filename, file.content_type)

    # ── Step 2: Read bytes and enforce size limit ─────────────────────────────
    content = await file.read()
    _validate_file_size(content, filename)

    logger.debug(
        "File read complete",
        extra={"document_id": document_id, "size_bytes": len(content)},
    )

    # ── Step 3: Run ingestion pipeline in thread pool ─────────────────────────
    # IngestionService is synchronous (ChromaDB is sync). We run it in
    # asyncio.to_thread() so the event loop stays free during I/O.
    result = await asyncio.to_thread(
        ingestion_service.ingest_document,
        document_id=document_id,
        filename=filename,
        content=content,
    )

    # ── Step 4: Translate domain result → API schema ──────────────────────────
    return DocumentUploadResponse.from_result(result)


# ─── GET /documents ───────────────────────────────────────────────────────────


@router.get(
    "",
    response_model=DocumentListResponse,
    summary="List indexed documents",
    description=(
        "Returns a paginated list of documents that have been indexed. "
        "Phase 1 stub — returns an empty list. "
        "Phase 2 will add a document registry (Firestore or Cloud SQL)."
    ),
)
async def list_documents(
    page: int = 1,
    page_size: int = 20,
) -> DocumentListResponse:
    """List all indexed documents.

    Phase 1: returns empty list.
    Phase 2: query document registry, return paginated results.
    """
    return DocumentListResponse(page=page, page_size=page_size)


# ─── DELETE /documents/{document_id} ──────────────────────────────────────────


@router.delete(
    "/{document_id}",
    status_code=204,
    response_model=None,
    summary="Delete a document and its index entries",
    description=(
        "Removes all chunks for the document from ChromaDB and optionally "
        "deletes the source PDF from GCS. Phase 2 implementation."
    ),
)
async def delete_document(document_id: str) -> None:
    """Delete a document from the platform.

    Phase 1: not implemented.
    Phase 2: call vector_store.delete_document() + storage_service.delete_document().
    """
    from fastapi import HTTPException, status

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Document deletion will be implemented in Phase 2.",
    )


# ─── POST /documents/{document_id}/reindex ────────────────────────────────────


@router.post(
    "/{document_id}/reindex",
    summary="Re-index an existing document",
    description=(
        "Re-fetches the PDF from GCS, re-extracts text, re-chunks, and "
        "re-embeds. Useful after chunking configuration changes. Phase 2."
    ),
)
async def reindex_document(document_id: str) -> None:
    """Re-index an existing document.

    Phase 1: not implemented.
    Phase 2: fetch GCS URI from registry → ingest_document() with same document_id.
    """
    from fastapi import HTTPException, status

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Re-indexing will be implemented in Phase 2.",
    )


# ─── Validation helpers ────────────────────────────────────────────────────────


def _validate_file_type(filename: str, content_type: str | None) -> None:
    """Reject non-PDF files before reading any bytes.

    Checks both the declared content-type header and the file extension.
    Neither alone is sufficient — browsers may send wrong content-types,
    and extensions can be renamed.
    """
    import os

    extension = os.path.splitext(filename)[1].lower()

    if extension not in _ALLOWED_EXTENSIONS:
        raise InvalidPDFError(
            f"'{filename}' has an unsupported file extension '{extension}'. "
            f"Only PDF files are accepted."
        )

    if content_type and content_type not in _ALLOWED_CONTENT_TYPES:
        logger.warning(
            "Unexpected content-type for PDF upload, proceeding with extension check",
            extra={"file_name": filename, "content_type": content_type},
        )


def _validate_file_size(content: bytes, filename: str) -> None:
    """Reject files that exceed the configured size limit.

    Runs after bytes are read so we have the real size, not the declared
    Content-Length (which can be spoofed).
    """
    if len(content) > settings.max_file_size_bytes:
        raise FileTooLargeError(
            size_bytes=len(content),
            limit_bytes=settings.max_file_size_bytes,
        )

    if len(content) == 0:
        raise InvalidPDFError(f"'{filename}' is empty (0 bytes).")
