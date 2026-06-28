"""
Document chunker — splits raw text into overlapping chunks with full metadata.

Uses LangChain's RecursiveCharacterTextSplitter which tries paragraph → sentence
→ word → character boundaries in order, producing semantically coherent chunks
rather than blindly cutting at a fixed character count.

Every chunk carries the full ChunkMetadata so the vector store can:
  - Filter by document_id for targeted retrieval
  - Surface source citations (document_name, page_number, chunk_index)
  - Support per-document deletion without a separate lookup table
"""

from __future__ import annotations

import uuid
from dataclasses import asdict
from datetime import datetime, timezone

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.rag.vector_store import ChunkMetadata, DocumentChunk


class DocumentChunker:
    """Splits document text into metadata-rich chunks for the vector store.

    Usage:
        chunker = DocumentChunker(chunk_size=512, chunk_overlap=64)
        chunks = chunker.chunk_text(
            text=page_text,
            document_id="doc-123",
            document_name="Annual Report 2024.pdf",
            source_path="gs://my-bucket/Annual Report 2024.pdf",
            page_number=3,
        )
    """

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 64) -> None:
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            # Prefer splitting at paragraph / sentence / word boundaries
            separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""],
            length_function=len,
            is_separator_regex=False,
        )

    def chunk_text(
        self,
        text: str,
        document_id: str,
        document_name: str,
        source_path: str,
        page_number: int = 0,
    ) -> list[DocumentChunk]:
        """Split text and attach full provenance metadata to each chunk.

        Args:
            text: Raw extracted text from one page or the full document.
            document_id: UUID of the parent document.
            document_name: Human-readable filename (for citations).
            source_path: GCS URI or local path (for audit trail).
            page_number: 0-indexed page number from the PDF parser.

        Returns:
            List of DocumentChunk, each with a stable chunk_id and full metadata.
        """
        if not text or not text.strip():
            return []

        texts = self._splitter.split_text(text)
        created_at = datetime.now(timezone.utc).isoformat()

        chunks: list[DocumentChunk] = []
        for index, chunk_text in enumerate(texts):
            chunk_id = f"{document_id}-p{page_number}-c{index}"

            metadata = ChunkMetadata(
                document_id=document_id,
                document_name=document_name,
                source_path=source_path,
                page_number=page_number,
                created_at=created_at,
                chunk_id=chunk_id,
                chunk_index=index,
            )

            chunks.append(
                DocumentChunk(
                    content=chunk_text,
                    chunk_id=chunk_id,
                    metadata=asdict(metadata),
                )
            )

        return chunks

    def chunk_pages(
        self,
        pages: list[str],
        document_id: str,
        document_name: str,
        source_path: str,
    ) -> list[DocumentChunk]:
        """Convenience wrapper for multi-page documents.

        Args:
            pages: List of extracted page texts in page order.
            document_id: UUID of the parent document.
            document_name: Human-readable filename.
            source_path: GCS URI or local path.

        Returns:
            Flat list of all chunks across all pages, with correct page_number
            on each chunk.
        """
        all_chunks: list[DocumentChunk] = []
        for page_number, page_text in enumerate(pages):
            page_chunks = self.chunk_text(
                text=page_text,
                document_id=document_id,
                document_name=document_name,
                source_path=source_path,
                page_number=page_number,
            )
            all_chunks.extend(page_chunks)
        return all_chunks


def generate_document_id() -> str:
    """Generate a stable UUID for a new document."""
    return str(uuid.uuid4())
