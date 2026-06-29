"""
PDF processing service — validation and text extraction.

Responsibilities:
    - Validate that uploaded bytes are a readable PDF
    - Extract per-page text with page number preservation
    - Handle common PDF failure modes gracefully
    - Return a structured ExtractedDocument (no chunking here)

Design decisions:
    - pypdf is used for extraction. It handles most standard PDFs well
      and is pure Python (no native binaries required).
    - This service does NOT chunk. Chunking is the responsibility of
      DocumentChunker (app/rag/chunker.py).
    - Image-only PDFs (scanned documents without a text layer) produce
      empty page text. PDFService logs a warning per empty page rather
      than failing outright — the orchestrator will produce zero chunks
      for those pages, which is correct behaviour.
    - Swapping pypdf for pdfplumber or apache-tika requires only changing
      this file. No other service is affected.

Future enhancements:
    - OCR fallback via Google Cloud Vision API for image-only PDFs
    - Structured extraction for tables (pdfplumber)
    - Password-protected PDF handling (pypdf supports this with a password)
"""

from __future__ import annotations

import io
import logging
import time

from app.core.exceptions import InvalidPDFError, PDFExtractionError
from app.models.document import ExtractedDocument, ExtractedPage

logger = logging.getLogger(__name__)

# Minimum bytes for a syntactically valid PDF (starts with %PDF-)
_MIN_PDF_SIZE_BYTES = 5


class PDFService:
    """Validates and extracts text from PDF files.

    Stateless — a single instance is safe to share across all requests.
    Instantiated once in main.py lifespan and stored in app.state.
    """

    # ─── Public interface ──────────────────────────────────────────────────────

    def validate(self, content: bytes, filename: str) -> None:
        """Validate that content is a readable PDF before extraction.

        Performs fast checks first (magic bytes) to fail early without
        spinning up a full PDF reader.

        Args:
            content: Raw file bytes from the upload.
            filename: Original filename (used in error messages only).

        Raises:
            InvalidPDFError: If the file is not a valid, readable PDF.
        """
        if len(content) < _MIN_PDF_SIZE_BYTES:
            raise InvalidPDFError(
                f"'{filename}' is too small to be a valid PDF ({len(content)} bytes)"
            )

        if not content.startswith(b"%PDF-"):
            raise InvalidPDFError(
                f"'{filename}' does not have a valid PDF header. "
                "Ensure the file is a PDF and not renamed from another format."
            )

        # Full parse check — catches corrupt PDFs that pass the header check
        try:
            from pypdf import PdfReader
            from pypdf.errors import PdfReadError

            reader = PdfReader(io.BytesIO(content))

            if reader.is_encrypted:
                raise InvalidPDFError(
                    f"'{filename}' is password-protected. "
                    "Please provide an unencrypted PDF."
                )

            if len(reader.pages) == 0:
                raise InvalidPDFError(
                    f"'{filename}' has no pages. The PDF appears to be empty."
                )

        except InvalidPDFError:
            raise  # Re-raise our own exceptions unchanged
        except Exception as exc:
            raise InvalidPDFError(
                f"'{filename}' could not be parsed. It may be corrupt.",
                cause=exc,
            ) from exc

    def extract(
        self,
        content: bytes,
        document_id: str,
        document_name: str,
    ) -> ExtractedDocument:
        """Extract text from all pages of a PDF.

        Validates the PDF before extraction. Call validate() first only if
        you want validation results before the extraction cost.

        Args:
            content: Raw PDF bytes.
            document_id: The document UUID (included in log context).
            document_name: Original filename (for error messages and logging).

        Returns:
            ExtractedDocument with one ExtractedPage per PDF page.
            Pages with no extractable text are included with empty text
            (image-only/scanned pages). The orchestrator handles them.

        Raises:
            InvalidPDFError: If the PDF fails validation.
            PDFExtractionError: If extraction fails on a structurally valid PDF.
        """
        self.validate(content, document_name)

        start = time.perf_counter()

        try:
            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(content))
            total_pages = len(reader.pages)
            pages: list[ExtractedPage] = []
            empty_page_count = 0

            for page_number, page in enumerate(reader.pages):
                try:
                    text = page.extract_text() or ""
                except Exception as exc:
                    logger.warning(
                        "Failed to extract text from page, skipping",
                        extra={
                            "document_id": document_id,
                            "page_number": page_number,
                            "error": str(exc),
                        },
                    )
                    text = ""

                extracted_page = ExtractedPage(page_number=page_number, text=text)
                pages.append(extracted_page)

                if extracted_page.is_empty:
                    empty_page_count += 1

            elapsed_ms = (time.perf_counter() - start) * 1000

            if empty_page_count > 0:
                logger.warning(
                    "PDF contains pages with no extractable text",
                    extra={
                        "document_id": document_id,
                        "document_name": document_name,
                        "total_pages": total_pages,
                        "empty_pages": empty_page_count,
                        "note": "These may be scanned/image pages. OCR not yet implemented.",
                    },
                )

            logger.info(
                "PDF extraction complete",
                extra={
                    "document_id": document_id,
                    "document_name": document_name,
                    "total_pages": total_pages,
                    "non_empty_pages": total_pages - empty_page_count,
                    "total_chars": sum(p.char_count for p in pages),
                    "elapsed_ms": round(elapsed_ms, 2),
                },
            )

            return ExtractedDocument(
                document_id=document_id,
                document_name=document_name,
                pages=pages,
            )

        except InvalidPDFError:
            raise
        except Exception as exc:
            raise PDFExtractionError(
                f"Text extraction failed for '{document_name}' "
                f"(document_id={document_id})",
                cause=exc,
            ) from exc
