"""
Retriever bridge — creates LangChain-compatible retrievers from a VectorStore.

Centralising retriever construction here means:
  - RAG chains always get a properly configured retriever
  - Retrieval parameters (k, score threshold, filters) are set once
  - Swapping ChromaDB for Vertex AI Vector Search in Phase 5 doesn't
    require changing any chain or agent code

LangChain compatibility:
  The returned retriever implements BaseRetriever and works with:
    - RetrievalQA.from_chain_type(retriever=...)
    - ConversationalRetrievalChain(retriever=...)
    - LangGraph nodes: retriever.invoke(query)
    - Agentic tools: create_retriever_tool(retriever, ...)
"""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.retrievers import BaseRetriever

from app.rag.vector_store import VectorStore

logger = logging.getLogger(__name__)


def build_retriever(
    vector_store: VectorStore,
    k: int = 5,
    document_id: str | None = None,
    score_threshold: float | None = None,
) -> BaseRetriever:
    """Build a LangChain retriever from any VectorStore implementation.

    Args:
        vector_store: Any VectorStore implementation (ChromaDB, Vertex AI, etc.)
        k: Number of chunks to retrieve per query.
        document_id: Optional — restrict retrieval to a single document.
            Useful for "chat with this document" features.
        score_threshold: Optional minimum relevance score (0.0–1.0).
            Chunks below this threshold are filtered out.

    Returns:
        A LangChain BaseRetriever ready to use in chains and agents.

    Example — unrestricted retrieval across all documents:
        retriever = build_retriever(vector_store, k=5)

    Example — retrieve only from a specific document:
        retriever = build_retriever(vector_store, k=4, document_id="doc-abc")

    Example — high-precision retrieval (only confident matches):
        retriever = build_retriever(vector_store, k=3, score_threshold=0.75)
    """
    metadata_filter: dict[str, Any] | None = None
    if document_id:
        metadata_filter = {"document_id": document_id}
        logger.debug("Building retriever scoped to document_id='%s'", document_id)

    retriever = vector_store.as_retriever(k=k, filter=metadata_filter)

    # Apply score threshold if requested.
    # Note: not all vector stores support this — ChromaDB does via
    # similarity_search_with_relevance_scores.
    if score_threshold is not None:
        retriever.search_kwargs["score_threshold"] = score_threshold
        retriever.search_type = "similarity_score_threshold"

    return retriever
