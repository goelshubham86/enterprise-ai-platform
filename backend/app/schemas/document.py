"""
Pydantic v2 schemas for the Documents API.

These are the shapes the HTTP API sends and receives — completely separate
from the internal domain models (app/models/document.py).

Separation rationale:
    Internal domain models can evolve independently of the API contract.
    For example, ProcessingResult might gain a `warnings` field for monitoring
    without that field appearing in the client response. The translation step
    (in the endpoint) is explicit and intentional.

Naming convention:
    *Request  → what the client sends
    *Response → what the server returns
    *Item     → a single element inside a list response
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.models.document import IngestionStatus, ProcessingResult


# ─── Upload ───────────────────────────────────────────────────────────────────


class DocumentUploadResponse(BaseModel):
    """Returned by POST /documents/upload on success.

    Provides enough information for the frontend to:
        - Display a success notification with document details
        - Poll for status if async processing is added later
        - Link back to the document in a document list view
    """

    model_config = ConfigDict(populate_by_name=True)

    document_id: str = Field(description="Stable UUID assigned to this document")
    document_name: str = Field(description="Original filename as uploaded")
    source_uri: str = Field(description="GCS URI where the original PDF is stored")
    total_pages: int = Field(description="Number of pages in the PDF")
    non_empty_pages: int = Field(description="Pages that contained extractable text")
    total_chunks: int = Field(description="Number of chunks indexed in the vector store")
    processing_time_ms: float = Field(description="End-to-end ingestion time in milliseconds")
    status: IngestionStatus = Field(description="Final ingestion status")
    created_at: str = Field(description="ISO 8601 timestamp of ingestion completion (UTC)")

    @classmethod
    def from_result(cls, result: ProcessingResult) -> "DocumentUploadResponse":
        """Translate a domain ProcessingResult into an API response schema.

        This is the only place where domain → schema translation occurs.
        All field mappings are explicit and immediately visible.
        """
        return cls(
            document_id=result.document_id,
            document_name=result.document_name,
            source_uri=result.source_uri,
            total_pages=result.total_pages,
            non_empty_pages=result.non_empty_pages,
            total_chunks=result.total_chunks,
            processing_time_ms=round(result.processing_time_ms, 2),
            status=result.status,
            created_at=result.created_at,
        )


# ─── List documents ───────────────────────────────────────────────────────────


class DocumentListItem(BaseModel):
    """A single document entry in the document list response.

    Phase 1 stub — will be populated from a document registry in Phase 2.
    """

    model_config = ConfigDict(populate_by_name=True)

    document_id: str
    document_name: str
    source_uri: str
    total_chunks: int
    created_at: str


class DocumentListResponse(BaseModel):
    """Paginated list of indexed documents.

    Phase 1 returns an empty list. Phase 2 will add a document registry
    (e.g. Firestore or Cloud SQL) to track ingested documents.
    """

    items: list[DocumentListItem] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20
    has_next: bool = False


# ─── Error response ───────────────────────────────────────────────────────────


class ErrorDetail(BaseModel):
    """Structured error body for all 4xx/5xx responses.

    Provides a machine-readable `error_code` alongside the human-readable
    `detail` message so clients can branch on error type.
    """

    detail: str
    error_code: str
    document_id: str | None = None
