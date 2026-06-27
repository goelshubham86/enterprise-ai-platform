# ADR-001: RAG Architecture with Vertex AI

**Date:** 2026-06-27  
**Status:** Accepted

## Context

We need to enable natural language Q&A over enterprise documents. The system must cite sources, be grounded in actual documents, and not hallucinate.

## Decision

Use Retrieval-Augmented Generation (RAG) with:
- **Vertex AI text-embedding-004** for dense vector embeddings
- **Vertex AI Vector Search** (or in-process FAISS for dev) as the vector store
- **Vertex AI Gemini** as the generative model

## Rationale

- Keeps all data within GCP (compliance boundary)
- Vertex AI provides managed embeddings with no external API calls
- Gemini natively supports grounding instructions via system prompts
- LangChain abstracts the retrieval chain, making swap-outs easy

## Consequences

- Requires Vertex AI API enabled and IAM roles configured
- Embedding latency adds ~200-400ms per query (acceptable)
- FAISS (dev) → Vertex AI Vector Search (prod) migration is planned for Phase 2
