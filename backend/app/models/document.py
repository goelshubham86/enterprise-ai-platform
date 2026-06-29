"""
Domain models for document ingestion.

These are pure Python dataclasses — no FastAPI, no Pydantic, no ChromaDB.
They represent the data as it flows through the business logic layer.

Design rule: services accept and return these types. The API layer
translates between domain models and Pydantic schemas (app/schemas/).

Future LangChain/LangGraph note:
    LangGraph state objects will wrap or extend these models.
    Because they are plain dataclasses, they serialize trivially to dicts
    for LangGraph's state checkpointing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


# ─── Enums ────────────────────────────────────────────────────────────────────


class IngestionStatus(str, Enum):
    """Lifecycle states for a document ingestion run."""

    PENDING = "pending"
    UPLOADING = "uploading"
    EXTRACTING = "extracting"
    CHUNKING = "chunking"
    INDEXING = "indexing"
    INDEXED = "indexed"
    FAILED = "failed"


# ─── Extraction models ────────────────────────────────────────────────────────


@dataclass
class ExtractedPage:
    """Text and metadata for a single PDF page.

    Produced by PDFService. Consumed by DocumentChunker.
    page_number is 0-indexed (matches pypdf's internal representation).
    """

    page_number: int
    text: str
    char_count: int = field(init=False)

    def __post_init__(self) -> None:
        self.char_count = len(self.text)

    @property
    def is_empty(self) -> bool:
        """True if the page has no extractable text (e.g. scanned image page)."""
        return not self.text.strip()


@dataclass
class ExtractedDocument:
    """All pages extracted from a single PDF.

    Produced by PDFService. Consumed by IngestionService (orchestrator).
    The orchestrator passes page texts to DocumentChunker.
    """

    document_id: str
    document_name: str
    pages: list[ExtractedPage]

    @property
    def total_pages(self) -> int:
        return len(self.pages)

    @property
    def total_chars(self) -> int:
        return sum(p.char_count for p in self.pages)

    @property
    def non_empty_pages(self) -> list[ExtractedPage]:
        """Pages that contain at least one non-whitespace character."""
        return [p for p in self.pages if not p.is_empty]

    def page_texts(self) -> list[str]:
        """Ordered list of page text strings, preserving page index.

        Empty pages are included as empty strings so page_number in chunk
        metadata correctly reflects position in the original document.
        """
        return [p.text for p in self.pages]


# ─── Processing result ────────────────────────────────────────────────────────


@dataclass
class ProcessingResult:
    """The outcome of a successful ingestion run.

    Returned by IngestionService. Translated to DocumentUploadResponse
    (Pydantic) at the API boundary before being sent to the client.

    All timing values are in milliseconds.
    """

    document_id: str
    document_name: str
    source_uri: str
    total_pages: int
    non_empty_pages: int
    total_chunks: int
    processing_time_ms: float
    status: IngestionStatus = IngestionStatus.INDEXED
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @property
    def chunks_per_page(self) -> float:
        """Average chunks produced per non-empty page (useful for monitoring)."""
        if self.non_empty_pages == 0:
            return 0.0
        return self.total_chunks / self.non_empty_pages
