"""
Google Cloud Storage service for document ingestion.

Responsibilities:
    - Upload PDF bytes to GCS and return the gs:// URI
    - Read blob metadata (size, content-type, custom metadata)
    - Future: generate signed URLs for direct browser downloads
    - Future: support document versioning via GCS object generations

Design decisions:
    - The GCS client is created once per application lifetime and stored
      in app.state (see main.py lifespan). Do not instantiate StorageService
      per request.
    - All GCS-specific types (Blob, Bucket, Client) are confined to this
      file. No other service or endpoint imports google.cloud.storage.
    - StorageError wraps all GCS exceptions so callers handle one type.

GCS blob naming convention:
    {gcs_upload_prefix}/{document_id}/{original_filename}
    e.g. documents/3f4a1b.../Annual_Report_2024.pdf

Local development without GCS:
    Set GCS_BUCKET_NAME to a real bucket and run:
        gcloud auth application-default login
    Or use the GCS emulator (fake-gcs-server) via Docker.
"""

from __future__ import annotations

import logging
from typing import Any

from app.core.exceptions import StorageError

logger = logging.getLogger(__name__)


class StorageService:
    """GCS-backed document storage.

    All public methods translate GCS exceptions into StorageError so
    callers do not need to import google.cloud.storage.
    """

    def __init__(self, bucket_name: str, project: str, upload_prefix: str = "documents") -> None:
        """Initialise the GCS client and resolve the target bucket.

        Args:
            bucket_name: Name of the GCS bucket (without gs://).
            project: GCP project ID used for billing and quota.
            upload_prefix: Folder prefix inside the bucket (default: "documents").

        Raises:
            StorageError: If the GCS client cannot be initialised (e.g. missing
                          credentials or the bucket does not exist).
        """
        try:
            from google.cloud import storage as gcs

            self._client = gcs.Client(project=project)
            self._bucket = self._client.bucket(bucket_name)
            self._bucket_name = bucket_name
            self._upload_prefix = upload_prefix.strip("/")

            logger.info(
                "StorageService initialised",
                extra={"bucket": bucket_name, "prefix": upload_prefix},
            )
        except Exception as exc:
            raise StorageError(
                f"Failed to initialise GCS client for bucket '{bucket_name}'",
                cause=exc,
            ) from exc

    # ─── Public interface ──────────────────────────────────────────────────────

    def upload_document(
        self,
        document_id: str,
        filename: str,
        content: bytes,
        content_type: str = "application/pdf",
    ) -> str:
        """Upload PDF bytes to GCS and return the gs:// URI.

        The blob path is deterministic:
            {prefix}/{document_id}/{filename}

        This makes re-uploads idempotent for the same document_id — the
        blob is overwritten, not duplicated. Useful for future re-indexing.

        Args:
            document_id: Stable UUID for this document (used in the blob path).
            filename: Original filename (preserved for human readability).
            content: Raw PDF bytes.
            content_type: MIME type (default: application/pdf).

        Returns:
            GCS URI string, e.g. "gs://bucket/documents/abc-123/report.pdf".

        Raises:
            StorageError: If the upload fails for any reason.
        """
        blob_name = self._blob_name(document_id, filename)

        try:
            blob = self._bucket.blob(blob_name)
            blob.metadata = {"document_id": document_id, "original_filename": filename}
            blob.upload_from_string(content, content_type=content_type)

            uri = f"gs://{self._bucket_name}/{blob_name}"

            logger.info(
                "Document uploaded to GCS",
                extra={
                    "document_id": document_id,
                    "blob_name": blob_name,
                    "size_bytes": len(content),
                    "uri": uri,
                },
            )
            return uri

        except Exception as exc:
            raise StorageError(
                f"Failed to upload document '{filename}' (document_id={document_id}) to GCS",
                cause=exc,
            ) from exc

    def get_blob_metadata(self, gcs_uri: str) -> dict[str, Any]:
        """Fetch GCS object metadata for a stored document.

        Args:
            gcs_uri: Full GCS URI returned by upload_document().

        Returns:
            Dict containing: name, size, content_type, time_created,
            updated, custom_metadata, generation.

        Raises:
            StorageError: If the blob does not exist or metadata cannot be read.
        """
        blob_name = self._blob_name_from_uri(gcs_uri)

        try:
            blob = self._bucket.blob(blob_name)
            blob.reload()  # Fetch server-side metadata

            return {
                "name": blob.name,
                "size": blob.size,
                "content_type": blob.content_type,
                "time_created": blob.time_created.isoformat() if blob.time_created else None,
                "updated": blob.updated.isoformat() if blob.updated else None,
                "custom_metadata": blob.metadata or {},
                "generation": blob.generation,
            }

        except Exception as exc:
            raise StorageError(
                f"Failed to read metadata for GCS object '{gcs_uri}'",
                cause=exc,
            ) from exc

    def delete_document(self, document_id: str, filename: str) -> None:
        """Delete a stored document from GCS.

        Future-ready interface — called when a document is removed from
        the platform (delete_document endpoint, Phase 2).

        Args:
            document_id: The UUID used when uploading.
            filename: The original filename used when uploading.

        Raises:
            StorageError: If the deletion fails.
        """
        blob_name = self._blob_name(document_id, filename)

        try:
            blob = self._bucket.blob(blob_name)
            blob.delete()

            logger.info(
                "Document deleted from GCS",
                extra={"document_id": document_id, "blob_name": blob_name},
            )

        except Exception as exc:
            raise StorageError(
                f"Failed to delete GCS object '{blob_name}'",
                cause=exc,
            ) from exc

    # ─── Private helpers ───────────────────────────────────────────────────────

    def _blob_name(self, document_id: str, filename: str) -> str:
        """Build the GCS blob name from document_id and filename."""
        safe_filename = filename.replace(" ", "_")
        return f"{self._upload_prefix}/{document_id}/{safe_filename}"

    def _blob_name_from_uri(self, gcs_uri: str) -> str:
        """Extract the blob name from a gs:// URI.

        Example: "gs://my-bucket/documents/abc/report.pdf" → "documents/abc/report.pdf"
        """
        prefix = f"gs://{self._bucket_name}/"
        if not gcs_uri.startswith(prefix):
            raise StorageError(
                f"URI '{gcs_uri}' does not belong to bucket '{self._bucket_name}'"
            )
        return gcs_uri[len(prefix):]
