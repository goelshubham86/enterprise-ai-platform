"""Tests for domain models (app/models/document.py).

These are pure Python dataclasses — no FastAPI, no Pydantic, no GCP.
Tests verify computed properties and business invariants.
"""

import pytest

from app.models.document import (
    ExtractedDocument,
    ExtractedPage,
    IngestionStatus,
    ProcessingResult,
)


# ─── IngestionStatus ──────────────────────────────────────────────────────────


class TestIngestionStatus:
    def test_indexed_is_terminal_success_state(self):
        assert IngestionStatus.INDEXED == "indexed"

    def test_failed_is_terminal_failure_state(self):
        assert IngestionStatus.FAILED == "failed"

    def test_all_expected_states_exist(self):
        expected = {"pending", "uploading", "extracting", "chunking", "indexing", "indexed", "failed"}
        actual = {s.value for s in IngestionStatus}
        assert expected == actual


# ─── ExtractedPage ────────────────────────────────────────────────────────────


class TestExtractedPage:
    def test_char_count_computed_on_init(self):
        page = ExtractedPage(page_number=0, text="hello world")
        assert page.char_count == 11

    def test_char_count_zero_for_empty_text(self):
        page = ExtractedPage(page_number=0, text="")
        assert page.char_count == 0

    def test_is_empty_true_for_empty_string(self):
        page = ExtractedPage(page_number=0, text="")
        assert page.is_empty is True

    def test_is_empty_true_for_whitespace_only(self):
        page = ExtractedPage(page_number=0, text="   \n\t  ")
        assert page.is_empty is True

    def test_is_empty_false_for_actual_text(self):
        page = ExtractedPage(page_number=0, text="some content here")
        assert page.is_empty is False

    def test_is_empty_false_for_text_with_surrounding_whitespace(self):
        page = ExtractedPage(page_number=0, text="  content  ")
        assert page.is_empty is False

    def test_page_number_stored(self):
        page = ExtractedPage(page_number=3, text="text")
        assert page.page_number == 3

    def test_text_stored(self):
        page = ExtractedPage(page_number=0, text="my text")
        assert page.text == "my text"


# ─── ExtractedDocument ────────────────────────────────────────────────────────


class TestExtractedDocument:
    @pytest.fixture
    def doc_with_two_pages(self) -> ExtractedDocument:
        return ExtractedDocument(
            document_id="doc-001",
            document_name="report.pdf",
            pages=[
                ExtractedPage(page_number=0, text="Page one content."),
                ExtractedPage(page_number=1, text="Page two content."),
            ],
        )

    @pytest.fixture
    def doc_with_blank_page(self) -> ExtractedDocument:
        return ExtractedDocument(
            document_id="doc-002",
            document_name="mixed.pdf",
            pages=[
                ExtractedPage(page_number=0, text="Readable text here."),
                ExtractedPage(page_number=1, text=""),  # blank / image-only page
            ],
        )

    def test_total_pages_equals_list_length(self, doc_with_two_pages):
        assert doc_with_two_pages.total_pages == 2

    def test_total_chars_sums_all_pages(self, doc_with_two_pages):
        expected = len("Page one content.") + len("Page two content.")
        assert doc_with_two_pages.total_chars == expected

    def test_non_empty_pages_excludes_blank_pages(self, doc_with_blank_page):
        non_empty = doc_with_blank_page.non_empty_pages
        assert len(non_empty) == 1
        assert non_empty[0].page_number == 0

    def test_non_empty_pages_returns_all_when_no_blank_pages(self, doc_with_two_pages):
        assert len(doc_with_two_pages.non_empty_pages) == 2

    def test_page_texts_preserves_order(self, doc_with_two_pages):
        texts = doc_with_two_pages.page_texts()
        assert texts == ["Page one content.", "Page two content."]

    def test_page_texts_includes_empty_strings_for_blank_pages(self, doc_with_blank_page):
        texts = doc_with_blank_page.page_texts()
        assert texts[1] == ""

    def test_page_texts_length_matches_total_pages(self, doc_with_two_pages):
        assert len(doc_with_two_pages.page_texts()) == doc_with_two_pages.total_pages

    def test_document_id_stored(self, doc_with_two_pages):
        assert doc_with_two_pages.document_id == "doc-001"

    def test_document_name_stored(self, doc_with_two_pages):
        assert doc_with_two_pages.document_name == "report.pdf"


# ─── ProcessingResult ─────────────────────────────────────────────────────────


class TestProcessingResult:
    @pytest.fixture
    def result(self) -> ProcessingResult:
        return ProcessingResult(
            document_id="doc-xyz",
            document_name="annual_report.pdf",
            source_uri="gs://bucket/documents/doc-xyz/annual_report.pdf",
            total_pages=4,
            non_empty_pages=3,
            total_chunks=12,
            processing_time_ms=980.5,
            status=IngestionStatus.INDEXED,
        )

    def test_chunks_per_page_correct(self, result):
        assert result.chunks_per_page == pytest.approx(12 / 3)

    def test_chunks_per_page_zero_when_no_non_empty_pages(self):
        r = ProcessingResult(
            document_id="x",
            document_name="blank.pdf",
            source_uri="gs://b/blank.pdf",
            total_pages=1,
            non_empty_pages=0,
            total_chunks=0,
            processing_time_ms=50.0,
        )
        assert r.chunks_per_page == 0.0

    def test_default_status_is_indexed(self):
        r = ProcessingResult(
            document_id="x",
            document_name="f.pdf",
            source_uri="gs://b/f.pdf",
            total_pages=1,
            non_empty_pages=1,
            total_chunks=2,
            processing_time_ms=100.0,
        )
        assert r.status == IngestionStatus.INDEXED

    def test_created_at_is_iso8601_utc(self, result):
        from datetime import datetime
        # Should parse without errors and contain 'T' as date/time separator
        dt = datetime.fromisoformat(result.created_at.replace("Z", "+00:00"))
        assert dt is not None
        assert "T" in result.created_at

    def test_all_fields_accessible(self, result):
        assert result.document_id == "doc-xyz"
        assert result.document_name == "annual_report.pdf"
        assert result.source_uri == "gs://bucket/documents/doc-xyz/annual_report.pdf"
        assert result.total_pages == 4
        assert result.non_empty_pages == 3
        assert result.total_chunks == 12
        assert result.processing_time_ms == pytest.approx(980.5)
