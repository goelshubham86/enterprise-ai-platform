"""Tests for Pydantic v2 API schemas (app/schemas/document.py).

Verifies:
    - DocumentUploadResponse.from_result() maps all fields correctly
    - DocumentListResponse defaults produce a valid empty list response
    - ErrorDetail carries both detail and error_code
    - Schemas serialise correctly to dicts (for JSON response assertions)
"""

import pytest

from app.models.document import IngestionStatus, ProcessingResult
from app.schemas.document import (
    DocumentListResponse,
    DocumentUploadResponse,
    ErrorDetail,
)


# ─── DocumentUploadResponse ───────────────────────────────────────────────────


class TestDocumentUploadResponse:
    def test_from_result_maps_document_id(self, processing_result):
        response = DocumentUploadResponse.from_result(processing_result)
        assert response.document_id == processing_result.document_id

    def test_from_result_maps_document_name(self, processing_result):
        response = DocumentUploadResponse.from_result(processing_result)
        assert response.document_name == processing_result.document_name

    def test_from_result_maps_source_uri(self, processing_result):
        response = DocumentUploadResponse.from_result(processing_result)
        assert response.source_uri == processing_result.source_uri

    def test_from_result_maps_total_pages(self, processing_result):
        response = DocumentUploadResponse.from_result(processing_result)
        assert response.total_pages == processing_result.total_pages

    def test_from_result_maps_non_empty_pages(self, processing_result):
        response = DocumentUploadResponse.from_result(processing_result)
        assert response.non_empty_pages == processing_result.non_empty_pages

    def test_from_result_maps_total_chunks(self, processing_result):
        response = DocumentUploadResponse.from_result(processing_result)
        assert response.total_chunks == processing_result.total_chunks

    def test_from_result_rounds_processing_time(self, processing_result):
        response = DocumentUploadResponse.from_result(processing_result)
        # from_result() rounds to 2 decimal places
        assert response.processing_time_ms == round(processing_result.processing_time_ms, 2)

    def test_from_result_maps_status(self, processing_result):
        response = DocumentUploadResponse.from_result(processing_result)
        assert response.status == IngestionStatus.INDEXED

    def test_from_result_maps_created_at(self, processing_result):
        response = DocumentUploadResponse.from_result(processing_result)
        assert response.created_at == processing_result.created_at

    def test_serialises_to_dict(self, processing_result):
        response = DocumentUploadResponse.from_result(processing_result)
        data = response.model_dump()
        assert isinstance(data, dict)
        assert "document_id" in data
        assert "status" in data

    def test_status_serialises_as_string_value(self, processing_result):
        response = DocumentUploadResponse.from_result(processing_result)
        data = response.model_dump()
        # IngestionStatus is a str Enum — serialised value should be "indexed"
        assert data["status"] == "indexed"


# ─── DocumentListResponse ─────────────────────────────────────────────────────


class TestDocumentListResponse:
    def test_default_items_is_empty_list(self):
        response = DocumentListResponse()
        assert response.items == []

    def test_default_total_is_zero(self):
        assert DocumentListResponse().total == 0

    def test_default_page_is_one(self):
        assert DocumentListResponse().page == 1

    def test_default_page_size_is_twenty(self):
        assert DocumentListResponse().page_size == 20

    def test_default_has_next_is_false(self):
        assert DocumentListResponse().has_next is False

    def test_custom_pagination_stored(self):
        response = DocumentListResponse(page=3, page_size=10)
        assert response.page == 3
        assert response.page_size == 10

    def test_serialises_to_dict_with_snake_case(self):
        data = DocumentListResponse().model_dump()
        assert "has_next" in data
        assert "page_size" in data


# ─── ErrorDetail ──────────────────────────────────────────────────────────────


class TestErrorDetail:
    def test_detail_stored(self):
        err = ErrorDetail(detail="Something went wrong", error_code="STORAGE_ERROR")
        assert err.detail == "Something went wrong"

    def test_error_code_stored(self):
        err = ErrorDetail(detail="msg", error_code="INVALID_PDF")
        assert err.error_code == "INVALID_PDF"

    def test_document_id_optional_defaults_none(self):
        err = ErrorDetail(detail="msg", error_code="INTERNAL_ERROR")
        assert err.document_id is None

    def test_document_id_can_be_set(self):
        err = ErrorDetail(detail="msg", error_code="STORAGE_ERROR", document_id="doc-123")
        assert err.document_id == "doc-123"
