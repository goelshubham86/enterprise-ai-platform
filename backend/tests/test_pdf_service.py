"""Tests for PDFService — validation and text extraction.

No GCP credentials required. Uses:
    - pypdf PdfWriter to generate valid blank-page PDFs (session-scoped fixture)
    - Raw bytes to simulate non-PDF and malformed inputs

Note on blank-page PDFs:
    PdfWriter.add_blank_page() creates pages with no content stream (no text).
    This is intentional — it lets us verify page count, page-number ordering,
    and is_empty behaviour without needing a real document with embedded text.
    The IngestionService tests separately verify the full pipeline with chunking.
"""

import pytest

from app.core.exceptions import InvalidPDFError
from app.models.document import ExtractedDocument, ExtractedPage
from app.services.pdf_service import PDFService


@pytest.fixture(scope="module")
def pdf_service() -> PDFService:
    """Module-scoped: PDFService is stateless, one instance is fine."""
    return PDFService()


# ─── validate() ───────────────────────────────────────────────────────────────


class TestValidate:
    def test_rejects_empty_bytes(self, pdf_service, empty_bytes):
        with pytest.raises(InvalidPDFError, match="too small"):
            pdf_service.validate(empty_bytes, "empty.pdf")

    def test_rejects_non_pdf_bytes(self, pdf_service, not_a_pdf_bytes):
        with pytest.raises(InvalidPDFError, match="valid PDF header"):
            pdf_service.validate(not_a_pdf_bytes, "fake.pdf")

    def test_rejects_bytes_without_pdf_magic(self, pdf_service):
        with pytest.raises(InvalidPDFError):
            pdf_service.validate(b"PK\x03\x04notapdf", "renamed.pdf")

    def test_accepts_valid_single_page_pdf(self, pdf_service, single_page_pdf_bytes):
        # Must not raise
        pdf_service.validate(single_page_pdf_bytes, "single.pdf")

    def test_accepts_valid_two_page_pdf(self, pdf_service, two_page_pdf_bytes):
        pdf_service.validate(two_page_pdf_bytes, "two_page.pdf")

    def test_error_message_contains_filename(self, pdf_service):
        with pytest.raises(InvalidPDFError) as exc_info:
            pdf_service.validate(b"notapdf", "my_report_Q4.pdf")
        assert "my_report_Q4.pdf" in str(exc_info.value)

    def test_invalid_pdf_error_is_our_type(self, pdf_service, not_a_pdf_bytes):
        with pytest.raises(InvalidPDFError):
            pdf_service.validate(not_a_pdf_bytes, "test.pdf")


# ─── extract() ────────────────────────────────────────────────────────────────


class TestExtract:
    def test_returns_extracted_document_instance(
        self, pdf_service, two_page_pdf_bytes, document_id
    ):
        result = pdf_service.extract(two_page_pdf_bytes, document_id, "report.pdf")
        assert isinstance(result, ExtractedDocument)

    def test_total_pages_matches_pdf_page_count(
        self, pdf_service, two_page_pdf_bytes, document_id
    ):
        result = pdf_service.extract(two_page_pdf_bytes, document_id, "report.pdf")
        assert result.total_pages == 2

    def test_single_page_pdf_has_one_page(
        self, pdf_service, single_page_pdf_bytes, document_id
    ):
        result = pdf_service.extract(single_page_pdf_bytes, document_id, "single.pdf")
        assert result.total_pages == 1

    def test_pages_are_extracted_page_instances(
        self, pdf_service, two_page_pdf_bytes, document_id
    ):
        result = pdf_service.extract(two_page_pdf_bytes, document_id, "report.pdf")
        for page in result.pages:
            assert isinstance(page, ExtractedPage)

    def test_page_numbers_are_zero_indexed(
        self, pdf_service, two_page_pdf_bytes, document_id
    ):
        result = pdf_service.extract(two_page_pdf_bytes, document_id, "report.pdf")
        page_numbers = [p.page_number for p in result.pages]
        assert page_numbers == [0, 1]

    def test_document_id_propagated(
        self, pdf_service, single_page_pdf_bytes, document_id
    ):
        result = pdf_service.extract(single_page_pdf_bytes, document_id, "doc.pdf")
        assert result.document_id == document_id

    def test_document_name_propagated(
        self, pdf_service, single_page_pdf_bytes, document_id
    ):
        result = pdf_service.extract(single_page_pdf_bytes, document_id, "my_file.pdf")
        assert result.document_name == "my_file.pdf"

    def test_blank_pages_are_marked_empty(
        self, pdf_service, two_page_pdf_bytes, document_id
    ):
        result = pdf_service.extract(two_page_pdf_bytes, document_id, "blank.pdf")
        # PdfWriter blank pages have no text content stream → all pages empty
        for page in result.pages:
            assert page.is_empty

    def test_page_texts_list_length_equals_total_pages(
        self, pdf_service, two_page_pdf_bytes, document_id
    ):
        result = pdf_service.extract(two_page_pdf_bytes, document_id, "doc.pdf")
        assert len(result.page_texts()) == result.total_pages

    def test_extract_validates_before_parsing(
        self, pdf_service, not_a_pdf_bytes, document_id
    ):
        """extract() must call validate() internally — not require callers to do it."""
        with pytest.raises(InvalidPDFError):
            pdf_service.extract(not_a_pdf_bytes, document_id, "invalid.pdf")

    def test_extract_rejects_empty_bytes(self, pdf_service, empty_bytes, document_id):
        with pytest.raises(InvalidPDFError):
            pdf_service.extract(empty_bytes, document_id, "empty.pdf")
