"""
Structured exception hierarchy for the Enterprise AI Platform.

All domain exceptions inherit from PlatformError so the API layer can
catch PlatformError as a safety net while still handling known subtypes
individually for precise HTTP status codes and user-facing messages.

Hierarchy:
    PlatformError                   ← base for all platform exceptions
    ├── ValidationError             ← bad input from the caller (4xx)
    │   ├── InvalidPDFError         ← file is not a valid/readable PDF
    │   └── FileTooLargeError       ← upload exceeds size limit
    └── InfrastructureError         ← downstream service failure (5xx)
        ├── StorageError            ← GCS upload/read/delete failed
        ├── PDFExtractionError      ← text could not be extracted
        ├── EmbeddingError          ← Vertex AI embedding call failed
        └── VectorStoreError        ← ChromaDB read/write failed
"""

from __future__ import annotations


# ─── Base ─────────────────────────────────────────────────────────────────────


class PlatformError(Exception):
    """Base class for all application-specific exceptions.

    Always carry a human-readable message suitable for logging.
    Never include raw upstream error messages in responses returned to clients.
    """

    def __init__(self, message: str, *, cause: BaseException | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.cause = cause

    def __str__(self) -> str:
        if self.cause:
            return f"{self.message} (caused by: {self.cause!r})"
        return self.message


# ─── Validation errors (caller is at fault, 4xx) ──────────────────────────────


class ValidationError(PlatformError):
    """Raised when the caller provides invalid input.

    Maps to HTTP 422 Unprocessable Entity at the API boundary.
    """


class InvalidPDFError(ValidationError):
    """The uploaded file is not a valid, readable PDF.

    Possible causes:
        - File has wrong MIME type or extension
        - PDF is password-protected
        - PDF header is malformed (not a real PDF)
        - PDF has zero extractable pages
    """


class FileTooLargeError(ValidationError):
    """The uploaded file exceeds the configured size limit.

    Maps to HTTP 413 Request Entity Too Large.
    """

    def __init__(self, size_bytes: int, limit_bytes: int) -> None:
        super().__init__(
            f"File size {size_bytes:,} bytes exceeds limit of {limit_bytes:,} bytes "
            f"({limit_bytes // (1024 * 1024)} MB)"
        )
        self.size_bytes = size_bytes
        self.limit_bytes = limit_bytes


# ─── Infrastructure errors (downstream service is at fault, 5xx) ──────────────


class InfrastructureError(PlatformError):
    """Raised when a downstream service fails.

    Maps to HTTP 502 Bad Gateway or 503 Service Unavailable at the API boundary.
    Log the full cause server-side; return a safe, generic message to the client.
    """


class StorageError(InfrastructureError):
    """GCS operation failed (upload, metadata read, or delete).

    Possible causes:
        - Network timeout
        - Insufficient IAM permissions (missing storage.objects.create)
        - Bucket does not exist
        - GCS quota exceeded
    """


class PDFExtractionError(InfrastructureError):
    """PDF text extraction failed after successful validation.

    Possible causes:
        - PDF contains only scanned images (no embedded text layer)
        - pypdf encountered an internal parsing error on a valid-looking PDF
        - Encoding issues in embedded fonts
    """


class EmbeddingError(InfrastructureError):
    """Vertex AI embedding generation failed.

    Possible causes:
        - API quota exceeded
        - Authentication failure (ADC not configured)
        - Model is temporarily unavailable
        - Input text exceeds model token limit
    """


class VectorStoreError(InfrastructureError):
    """ChromaDB (or future Vertex AI Vector Search) operation failed.

    Possible causes:
        - Corrupt SQLite database file (ChromaDB)
        - Disk quota exceeded on the persist directory
        - Collection was deleted externally while the service was running
    """


class ServiceNotReadyError(InfrastructureError):
    """A request arrived before background service initialization completed.

    Returned when vector store, storage service, or PDF service is still
    being initialized. Maps to HTTP 503 Service Unavailable with a
    Retry-After header so clients know to back off and retry.
    """
