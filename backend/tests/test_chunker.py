"""Tests for DocumentChunker (app/rag/chunker.py).

Pure Python — no GCP, no FastAPI. DocumentChunker wraps
LangChain's RecursiveCharacterTextSplitter, which is pure Python.

Tests verify:
    - Empty/whitespace text produces zero chunks
    - Short text that fits in one chunk produces exactly one chunk
    - Long text is split into multiple chunks
    - chunk_id format matches "{document_id}-p{page}-c{index}"
    - All required metadata fields are present on every chunk
    - chunk_pages() correctly aggregates chunks across pages
    - Per-page page_number is set correctly on each chunk
    - generate_document_id() returns unique UUIDs
"""

import re
import uuid

import pytest

from app.rag.chunker import DocumentChunker, generate_document_id
from app.rag.vector_store import DocumentChunk


CHUNK_SIZE = 128
CHUNK_OVERLAP = 16

SHORT_TEXT = "This is a short sentence."
# Long enough text to force at least two chunks with CHUNK_SIZE=128
LONG_TEXT = (
    "Artificial intelligence is transforming the enterprise. "
    "Machine learning models can now process vast amounts of unstructured data. "
    "Natural language processing enables computers to understand human language. "
    "These technologies are being applied across finance, healthcare, and logistics. "
    "The key challenge is building systems that are reliable, safe, and explainable."
)

DOCUMENT_ID = "doc-test-001"
DOCUMENT_NAME = "test_report.pdf"
SOURCE_URI = "gs://bucket/documents/doc-test-001/test_report.pdf"


@pytest.fixture(scope="module")
def chunker() -> DocumentChunker:
    """Module-scoped chunker with small chunk_size to force splitting in tests."""
    return DocumentChunker(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)


# ─── chunk_text() ─────────────────────────────────────────────────────────────


class TestChunkText:
    def test_empty_string_returns_empty_list(self, chunker):
        result = chunker.chunk_text("", DOCUMENT_ID, DOCUMENT_NAME, SOURCE_URI)
        assert result == []

    def test_whitespace_only_returns_empty_list(self, chunker):
        result = chunker.chunk_text("   \n\t  ", DOCUMENT_ID, DOCUMENT_NAME, SOURCE_URI)
        assert result == []

    def test_short_text_returns_single_chunk(self, chunker):
        result = chunker.chunk_text(SHORT_TEXT, DOCUMENT_ID, DOCUMENT_NAME, SOURCE_URI)
        assert len(result) == 1

    def test_long_text_returns_multiple_chunks(self, chunker):
        result = chunker.chunk_text(LONG_TEXT, DOCUMENT_ID, DOCUMENT_NAME, SOURCE_URI)
        assert len(result) > 1

    def test_returns_list_of_document_chunks(self, chunker):
        result = chunker.chunk_text(SHORT_TEXT, DOCUMENT_ID, DOCUMENT_NAME, SOURCE_URI)
        for chunk in result:
            assert isinstance(chunk, DocumentChunk)

    def test_chunk_content_is_non_empty_string(self, chunker):
        result = chunker.chunk_text(LONG_TEXT, DOCUMENT_ID, DOCUMENT_NAME, SOURCE_URI)
        for chunk in result:
            assert isinstance(chunk.content, str)
            assert len(chunk.content) > 0

    def test_chunk_id_format(self, chunker):
        result = chunker.chunk_text(
            SHORT_TEXT, DOCUMENT_ID, DOCUMENT_NAME, SOURCE_URI, page_number=3
        )
        # Expected: "{document_id}-p3-c0" for first chunk
        assert result[0].chunk_id == f"{DOCUMENT_ID}-p3-c0"

    def test_chunk_id_matches_metadata_chunk_id(self, chunker):
        result = chunker.chunk_text(LONG_TEXT, DOCUMENT_ID, DOCUMENT_NAME, SOURCE_URI)
        for chunk in result:
            assert chunk.chunk_id == chunk.metadata["chunk_id"]

    def test_chunk_index_increments(self, chunker):
        result = chunker.chunk_text(LONG_TEXT, DOCUMENT_ID, DOCUMENT_NAME, SOURCE_URI)
        indices = [chunk.metadata["chunk_index"] for chunk in result]
        assert indices == list(range(len(result)))

    def test_metadata_contains_all_required_fields(self, chunker):
        required_fields = {
            "document_id", "document_name", "source_uri",
            "page_number", "created_at", "chunk_id", "chunk_index",
        }
        result = chunker.chunk_text(SHORT_TEXT, DOCUMENT_ID, DOCUMENT_NAME, SOURCE_URI)
        for chunk in result:
            assert required_fields.issubset(chunk.metadata.keys())

    def test_metadata_document_id_correct(self, chunker):
        result = chunker.chunk_text(SHORT_TEXT, DOCUMENT_ID, DOCUMENT_NAME, SOURCE_URI)
        for chunk in result:
            assert chunk.metadata["document_id"] == DOCUMENT_ID

    def test_metadata_document_name_correct(self, chunker):
        result = chunker.chunk_text(SHORT_TEXT, DOCUMENT_ID, DOCUMENT_NAME, SOURCE_URI)
        for chunk in result:
            assert chunk.metadata["document_name"] == DOCUMENT_NAME

    def test_metadata_source_uri_correct(self, chunker):
        result = chunker.chunk_text(SHORT_TEXT, DOCUMENT_ID, DOCUMENT_NAME, SOURCE_URI)
        for chunk in result:
            assert chunk.metadata["source_uri"] == SOURCE_URI

    def test_metadata_page_number_default_zero(self, chunker):
        result = chunker.chunk_text(SHORT_TEXT, DOCUMENT_ID, DOCUMENT_NAME, SOURCE_URI)
        assert result[0].metadata["page_number"] == 0

    def test_metadata_page_number_custom(self, chunker):
        result = chunker.chunk_text(
            SHORT_TEXT, DOCUMENT_ID, DOCUMENT_NAME, SOURCE_URI, page_number=5
        )
        assert result[0].metadata["page_number"] == 5

    def test_chunk_id_is_deterministic_for_same_inputs(self, chunker):
        """The chunk_id depends only on document_id, page, and chunk index — not time."""
        result1 = chunker.chunk_text(SHORT_TEXT, DOCUMENT_ID, DOCUMENT_NAME, SOURCE_URI, page_number=2)
        result2 = chunker.chunk_text(SHORT_TEXT, DOCUMENT_ID, DOCUMENT_NAME, SOURCE_URI, page_number=2)
        assert [c.chunk_id for c in result1] == [c.chunk_id for c in result2]


# ─── chunk_pages() ────────────────────────────────────────────────────────────


class TestChunkPages:
    def test_empty_page_list_returns_empty(self, chunker):
        result = chunker.chunk_pages([], DOCUMENT_ID, DOCUMENT_NAME, SOURCE_URI)
        assert result == []

    def test_blank_pages_return_empty(self, chunker):
        result = chunker.chunk_pages(["", "  ", "\n"], DOCUMENT_ID, DOCUMENT_NAME, SOURCE_URI)
        assert result == []

    def test_single_non_empty_page_returns_chunks(self, chunker):
        result = chunker.chunk_pages([SHORT_TEXT], DOCUMENT_ID, DOCUMENT_NAME, SOURCE_URI)
        assert len(result) >= 1

    def test_multiple_pages_aggregated(self, chunker):
        pages = [SHORT_TEXT, SHORT_TEXT, SHORT_TEXT]
        result = chunker.chunk_pages(pages, DOCUMENT_ID, DOCUMENT_NAME, SOURCE_URI)
        assert len(result) == 3  # one chunk per short-text page

    def test_page_numbers_are_zero_indexed_per_page(self, chunker):
        pages = [SHORT_TEXT, SHORT_TEXT]
        result = chunker.chunk_pages(pages, DOCUMENT_ID, DOCUMENT_NAME, SOURCE_URI)
        page_numbers = {chunk.metadata["page_number"] for chunk in result}
        assert 0 in page_numbers
        assert 1 in page_numbers

    def test_blank_pages_skipped_silently(self, chunker):
        pages = ["", SHORT_TEXT, ""]
        result = chunker.chunk_pages(pages, DOCUMENT_ID, DOCUMENT_NAME, SOURCE_URI)
        # Only page 1 (index 1) has content
        assert all(c.metadata["page_number"] == 1 for c in result)

    def test_source_uri_on_all_chunks(self, chunker):
        result = chunker.chunk_pages([SHORT_TEXT, SHORT_TEXT], DOCUMENT_ID, DOCUMENT_NAME, SOURCE_URI)
        for chunk in result:
            assert chunk.metadata["source_uri"] == SOURCE_URI


# ─── generate_document_id() ───────────────────────────────────────────────────


class TestGenerateDocumentId:
    def test_returns_string(self):
        assert isinstance(generate_document_id(), str)

    def test_is_valid_uuid(self):
        doc_id = generate_document_id()
        parsed = uuid.UUID(doc_id)  # raises if invalid
        assert str(parsed) == doc_id

    def test_generates_unique_ids(self):
        ids = [generate_document_id() for _ in range(100)]
        assert len(set(ids)) == 100
