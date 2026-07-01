"""Tests for the custom exception hierarchy (app/core/exceptions.py).

Verifies:
    - The inheritance chain matches the documented hierarchy
    - PlatformError.message and .cause attributes are set correctly
    - FileTooLargeError carries typed size attributes
    - __str__ includes the cause repr when present
    - Subtypes can be caught by their parents (polymorphic catch)
"""

import pytest

from app.core.exceptions import (
    EmbeddingError,
    FileTooLargeError,
    InfrastructureError,
    InvalidPDFError,
    PDFExtractionError,
    PlatformError,
    StorageError,
    ValidationError,
    VectorStoreError,
)


# ─── Hierarchy ────────────────────────────────────────────────────────────────


class TestExceptionHierarchy:
    def test_platform_error_is_exception(self):
        assert issubclass(PlatformError, Exception)

    def test_validation_error_is_platform_error(self):
        assert issubclass(ValidationError, PlatformError)

    def test_infrastructure_error_is_platform_error(self):
        assert issubclass(InfrastructureError, PlatformError)

    def test_invalid_pdf_is_validation_error(self):
        assert issubclass(InvalidPDFError, ValidationError)
        assert issubclass(InvalidPDFError, PlatformError)

    def test_file_too_large_is_validation_error(self):
        assert issubclass(FileTooLargeError, ValidationError)
        assert issubclass(FileTooLargeError, PlatformError)

    def test_storage_error_is_infrastructure_error(self):
        assert issubclass(StorageError, InfrastructureError)
        assert issubclass(StorageError, PlatformError)

    def test_pdf_extraction_error_is_infrastructure_error(self):
        assert issubclass(PDFExtractionError, InfrastructureError)

    def test_embedding_error_is_infrastructure_error(self):
        assert issubclass(EmbeddingError, InfrastructureError)

    def test_vector_store_error_is_infrastructure_error(self):
        assert issubclass(VectorStoreError, InfrastructureError)


# ─── PlatformError base behaviour ─────────────────────────────────────────────


class TestPlatformError:
    def test_message_stored_as_attribute(self):
        exc = PlatformError("something went wrong")
        assert exc.message == "something went wrong"

    def test_str_without_cause(self):
        exc = PlatformError("base message")
        assert str(exc) == "base message"

    def test_str_with_cause_includes_cause_repr(self):
        cause = ValueError("root cause")
        exc = PlatformError("outer message", cause=cause)
        text = str(exc)
        assert "outer message" in text
        assert "root cause" in text

    def test_cause_none_by_default(self):
        exc = PlatformError("no cause")
        assert exc.cause is None

    def test_cause_stored_as_attribute(self):
        cause = RuntimeError("downstream")
        exc = StorageError("storage failed", cause=cause)
        assert exc.cause is cause

    def test_can_be_raised_and_caught(self):
        with pytest.raises(PlatformError):
            raise PlatformError("test")


# ─── Polymorphic catch ────────────────────────────────────────────────────────


class TestPolymorphicCatch:
    def test_invalid_pdf_caught_as_validation_error(self):
        with pytest.raises(ValidationError):
            raise InvalidPDFError("not a pdf")

    def test_invalid_pdf_caught_as_platform_error(self):
        with pytest.raises(PlatformError):
            raise InvalidPDFError("not a pdf")

    def test_storage_error_caught_as_infrastructure_error(self):
        with pytest.raises(InfrastructureError):
            raise StorageError("gcs down")

    def test_storage_error_caught_as_platform_error(self):
        with pytest.raises(PlatformError):
            raise StorageError("gcs down")

    def test_embedding_error_caught_as_infrastructure_error(self):
        with pytest.raises(InfrastructureError):
            raise EmbeddingError("vertex down")

    def test_vector_store_error_caught_as_infrastructure_error(self):
        with pytest.raises(InfrastructureError):
            raise VectorStoreError("chroma error")


# ─── FileTooLargeError specifics ──────────────────────────────────────────────


class TestFileTooLargeError:
    def test_size_bytes_stored(self):
        exc = FileTooLargeError(size_bytes=60_000_000, limit_bytes=50_000_000)
        assert exc.size_bytes == 60_000_000

    def test_limit_bytes_stored(self):
        exc = FileTooLargeError(size_bytes=60_000_000, limit_bytes=50_000_000)
        assert exc.limit_bytes == 50_000_000

    def test_message_contains_mb_limit(self):
        exc = FileTooLargeError(size_bytes=60_000_000, limit_bytes=50 * 1024 * 1024)
        assert "50 MB" in str(exc)

    def test_message_contains_actual_size(self):
        exc = FileTooLargeError(size_bytes=60_000_000, limit_bytes=50_000_000)
        assert "60,000,000" in str(exc)

    def test_is_caught_as_platform_error(self):
        with pytest.raises(PlatformError):
            raise FileTooLargeError(size_bytes=100, limit_bytes=50)
