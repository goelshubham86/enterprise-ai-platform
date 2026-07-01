"""Tests for the /api/v1/documents endpoints.

Test groups:
    TestListDocuments      → GET /documents (Phase 1 stub, always empty)
    TestDeleteDocument     → DELETE /documents/{id} (501 stub)
    TestReindexDocument    → POST /documents/{id}/reindex (501 stub)
    TestUploadDocument     → POST /documents/upload (real pipeline, fake services)
    TestUploadValidation   → file-type and file-size validation before pipeline
    TestExceptionHandlers  → exception → HTTP status code mapping

No GCP credentials required:
    - `client` fixture uses null lifespan (from conftest)
    - `client_with_ingestion` fixture overrides get_ingestion_service with
      a real IngestionService backed by FakeStorageService + InMemoryVectorStore
"""

from __future__ import annotations

import io

import pytest
from fastapi.testclient import TestClient

from tests.helpers import make_blank_pdf


# ─── GET /documents ───────────────────────────────────────────────────────────


class TestListDocuments:
    def test_returns_200(self, client: TestClient):
        assert client.get("/api/v1/documents").status_code == 200

    def test_items_is_empty_list(self, client: TestClient):
        assert client.get("/api/v1/documents").json()["items"] == []

    def test_total_is_zero(self, client: TestClient):
        assert client.get("/api/v1/documents").json()["total"] == 0

    def test_has_next_is_false(self, client: TestClient):
        assert client.get("/api/v1/documents").json()["has_next"] is False

    def test_default_page_is_one(self, client: TestClient):
        assert client.get("/api/v1/documents").json()["page"] == 1

    def test_default_page_size_is_twenty(self, client: TestClient):
        assert client.get("/api/v1/documents").json()["page_size"] == 20

    def test_custom_pagination_params_reflected(self, client: TestClient):
        data = client.get("/api/v1/documents?page=3&page_size=5").json()
        assert data["page"] == 3
        assert data["page_size"] == 5


# ─── DELETE /documents/{document_id} ──────────────────────────────────────────


class TestDeleteDocument:
    def test_returns_501(self, client: TestClient):
        assert client.delete("/api/v1/documents/some-id").status_code == 501

    def test_response_has_detail_field(self, client: TestClient):
        assert "detail" in client.delete("/api/v1/documents/some-id").json()


# ─── POST /documents/{document_id}/reindex ────────────────────────────────────


class TestReindexDocument:
    def test_returns_501(self, client: TestClient):
        assert client.post("/api/v1/documents/some-id/reindex").status_code == 501


# ─── POST /documents/upload — validation (before pipeline runs) ───────────────


class TestUploadValidation:
    """Verifies checks that happen BEFORE the pipeline runs.

    FastAPI resolves ALL Depends() before calling the function body, so even
    though validation raises before the service is called, `get_ingestion_service`
    must already be resolved. We use `client_with_ingestion` here — the override
    returns our fake service, and the endpoint raises before calling it.
    """

    def test_rejects_non_pdf_extension(self, client_with_ingestion: TestClient):
        response = client_with_ingestion.post(
            "/api/v1/documents/upload",
            files={"file": ("report.txt", b"some text content", "text/plain")},
        )
        assert response.status_code == 422

    def test_rejects_docx_extension(self, client_with_ingestion: TestClient):
        response = client_with_ingestion.post(
            "/api/v1/documents/upload",
            files={"file": ("report.docx", b"PK\x03\x04...", "application/vnd.openxmlformats")},
        )
        assert response.status_code == 422

    def test_rejects_empty_file(self, client_with_ingestion: TestClient):
        response = client_with_ingestion.post(
            "/api/v1/documents/upload",
            files={"file": ("empty.pdf", b"", "application/pdf")},
        )
        assert response.status_code == 422

    def test_rejection_response_has_error_code(self, client_with_ingestion: TestClient):
        response = client_with_ingestion.post(
            "/api/v1/documents/upload",
            files={"file": ("report.txt", b"text", "text/plain")},
        )
        data = response.json()
        assert "error_code" in data
        assert data["error_code"] == "INVALID_PDF"

    def test_rejects_oversized_file(self, client_with_ingestion: TestClient, monkeypatch):
        """Patch max_file_size_bytes to 10 so we can test with a small payload."""
        from app.core import config

        monkeypatch.setattr(
            type(config.settings),
            "max_file_size_bytes",
            property(lambda self: 10),
        )

        response = client_with_ingestion.post(
            "/api/v1/documents/upload",
            files={"file": ("large.pdf", b"%PDF-" + b"x" * 100, "application/pdf")},
        )
        assert response.status_code == 413
        assert response.json()["error_code"] == "FILE_TOO_LARGE"


# ─── POST /documents/upload — full pipeline (blank-page PDF) ─────────────────


class TestUploadDocument:
    """Uses client_with_ingestion: real pipeline, fake GCS + ChromaDB."""

    def test_returns_200_for_valid_pdf(
        self, client_with_ingestion: TestClient, single_page_pdf_bytes: bytes
    ):
        response = client_with_ingestion.post(
            "/api/v1/documents/upload",
            files={"file": ("report.pdf", single_page_pdf_bytes, "application/pdf")},
        )
        assert response.status_code == 200

    def test_response_has_document_id(
        self, client_with_ingestion: TestClient, single_page_pdf_bytes: bytes
    ):
        data = client_with_ingestion.post(
            "/api/v1/documents/upload",
            files={"file": ("report.pdf", single_page_pdf_bytes, "application/pdf")},
        ).json()
        assert "document_id" in data
        assert len(data["document_id"]) > 0

    def test_response_has_source_uri(
        self, client_with_ingestion: TestClient, single_page_pdf_bytes: bytes
    ):
        data = client_with_ingestion.post(
            "/api/v1/documents/upload",
            files={"file": ("report.pdf", single_page_pdf_bytes, "application/pdf")},
        ).json()
        assert data["source_uri"].startswith("gs://")

    def test_response_total_pages_is_one(
        self, client_with_ingestion: TestClient, single_page_pdf_bytes: bytes
    ):
        data = client_with_ingestion.post(
            "/api/v1/documents/upload",
            files={"file": ("report.pdf", single_page_pdf_bytes, "application/pdf")},
        ).json()
        assert data["total_pages"] == 1

    def test_response_status_is_indexed(
        self, client_with_ingestion: TestClient, single_page_pdf_bytes: bytes
    ):
        data = client_with_ingestion.post(
            "/api/v1/documents/upload",
            files={"file": ("report.pdf", single_page_pdf_bytes, "application/pdf")},
        ).json()
        assert data["status"] == "indexed"

    def test_response_document_name_matches_upload_filename(
        self, client_with_ingestion: TestClient, single_page_pdf_bytes: bytes
    ):
        data = client_with_ingestion.post(
            "/api/v1/documents/upload",
            files={"file": ("my_report.pdf", single_page_pdf_bytes, "application/pdf")},
        ).json()
        assert data["document_name"] == "my_report.pdf"

    def test_response_processing_time_is_positive(
        self, client_with_ingestion: TestClient, single_page_pdf_bytes: bytes
    ):
        data = client_with_ingestion.post(
            "/api/v1/documents/upload",
            files={"file": ("report.pdf", single_page_pdf_bytes, "application/pdf")},
        ).json()
        assert data["processing_time_ms"] > 0

    def test_two_page_pdf_returns_two_total_pages(
        self, client_with_ingestion: TestClient, two_page_pdf_bytes: bytes
    ):
        data = client_with_ingestion.post(
            "/api/v1/documents/upload",
            files={"file": ("two_page.pdf", two_page_pdf_bytes, "application/pdf")},
        ).json()
        assert data["total_pages"] == 2

    def test_upload_without_file_returns_422(self, client_with_ingestion: TestClient):
        response = client_with_ingestion.post("/api/v1/documents/upload")
        assert response.status_code == 422
