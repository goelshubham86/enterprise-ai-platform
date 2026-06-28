"""
ChromaDB implementation of the VectorStore interface.

Uses chromadb.PersistentClient for local storage and the official
langchain-chroma integration so retrievers work with LangChain chains
and LangGraph agents out of the box.

Storage layout:
    {persist_dir}/          ← configurable via CHROMA_PERSIST_DIR
        <uuid>/             ← ChromaDB's internal segment files
        chroma.sqlite3      ← metadata + embedding index

Replacing this with VertexAIVectorStore in Phase 5 requires:
    1. Implement VertexAIVectorStore in vertex_store.py
    2. Change one import in app/core/dependencies.py
    Nothing else in the application needs to change.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import chromadb
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from app.rag.vector_store import DocumentChunk, SearchResult, VectorStore

logger = logging.getLogger(__name__)


class ChromaVectorStore(VectorStore):
    """Persistent ChromaDB-backed vector store.

    Thread-safety: ChromaDB's PersistentClient is process-local and
    not thread-safe for concurrent writes. For a single Cloud Run instance
    this is fine. For multi-instance deployments, switch to ChromaDB's
    HTTP server mode or migrate to Vertex AI Vector Search (Phase 5).
    """

    def __init__(
        self,
        persist_dir: str,
        collection_name: str,
        embeddings: Embeddings,
    ) -> None:
        Path(persist_dir).mkdir(parents=True, exist_ok=True)

        self._persist_dir = persist_dir
        self._collection_name = collection_name
        self._embeddings = embeddings

        self._client = chromadb.PersistentClient(path=persist_dir)

        # LangChain wrapper — used for add_documents, similarity_search,
        # and as_retriever so all chain integrations work automatically.
        self._store = Chroma(
            client=self._client,
            collection_name=collection_name,
            embedding_function=embeddings,
        )

        logger.info(
            "ChromaVectorStore initialised",
            extra={
                "persist_dir": persist_dir,
                "collection": collection_name,
                "chunks": self.document_count(),
            },
        )

    # ─── VectorStore interface ─────────────────────────────────────────────

    def add_documents(self, chunks: list[DocumentChunk]) -> None:
        """Upsert chunks into the collection.

        Passes chunk_id as the ChromaDB document ID so re-indexing a
        document is idempotent — duplicates are replaced, not appended.
        """
        if not chunks:
            return

        docs = [
            Document(page_content=chunk.content, metadata=chunk.metadata)
            for chunk in chunks
        ]
        ids = [chunk.chunk_id for chunk in chunks]

        self._store.add_documents(documents=docs, ids=ids)
        logger.info("Added %d chunks to collection '%s'", len(chunks), self._collection_name)

    def similarity_search(
        self,
        query: str,
        k: int = 5,
        filter: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Return top-k chunks ranked by cosine similarity.

        Scores are cosine distances (0 = identical, 2 = opposite).
        Lower score = more relevant.
        """
        results = self._store.similarity_search_with_relevance_scores(
            query=query,
            k=k,
            filter=filter,
        )

        return [
            SearchResult(
                content=doc.page_content,
                metadata=doc.metadata,
                score=score,
                chunk_id=doc.metadata.get("chunk_id", ""),
            )
            for doc, score in results
        ]

    def delete_document(self, document_id: str) -> None:
        """Delete all chunks belonging to document_id.

        ChromaDB supports server-side metadata filtering so this never
        fetches chunk content into memory.
        """
        collection = self._client.get_collection(self._collection_name)
        collection.delete(where={"document_id": document_id})
        logger.info("Deleted all chunks for document_id='%s'", document_id)

    def reset(self) -> None:
        """Wipe and recreate the collection.

        Use for local development and test teardown only.
        """
        self._client.delete_collection(self._collection_name)
        self._store = Chroma(
            client=self._client,
            collection_name=self._collection_name,
            embedding_function=self._embeddings,
        )
        logger.warning("Collection '%s' has been reset (all data deleted)", self._collection_name)

    def as_retriever(self, k: int = 5, filter: dict[str, Any] | None = None):
        """Return a LangChain VectorStoreRetriever.

        Compatible with RetrievalQA, ConversationalRetrievalChain,
        and LangGraph retriever nodes.

        Example:
            retriever = store.as_retriever(k=4)
            chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever)
        """
        search_kwargs: dict[str, Any] = {"k": k}
        if filter:
            search_kwargs["filter"] = filter

        return self._store.as_retriever(
            search_type="similarity",
            search_kwargs=search_kwargs,
        )

    def document_count(self) -> int:
        """Return total number of chunks currently stored."""
        try:
            collection = self._client.get_collection(self._collection_name)
            return collection.count()
        except Exception:
            return 0
