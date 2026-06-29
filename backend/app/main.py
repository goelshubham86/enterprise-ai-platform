"""Application entry point."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import (
    EmbeddingError,
    FileTooLargeError,
    InfrastructureError,
    InvalidPDFError,
    PlatformError,
    StorageError,
    VectorStoreError,
)
from app.core.logging import configure_logging
from app.api.v1.router import api_router

logger = logging.getLogger(__name__)


# ─── Application lifespan ─────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Initialise and tear down application-scoped resources.

    Resources created here are stored in app.state and accessed via
    FastAPI's dependency injection system (app/core/dependencies.py).

    Startup order matters:
        1. Logging (must be first — all other initialisations log to it)
        2. EmbeddingService (passed into VectorStore constructor)
        3. VectorStore (depends on EmbeddingService)
        4. StorageService (independent of VectorStore)
        5. PDFService (stateless, no external dependencies)

    To swap implementations (e.g. Phase 5 migration to Vertex AI):
        - VectorStore: replace ChromaVectorStore with VertexAIVectorStore here
        - EmbeddingService: replace VertexAIEmbeddingService with any Embeddings impl
        - StorageService: no changes expected (GCS stays in Phase 5)
    """
    # 1. Configure structured logging before anything else logs
    configure_logging(level=settings.log_level)

    logger.info(
        "Application starting",
        extra={"env": settings.app_env, "log_level": settings.log_level},
    )

    # 2. Embedding service
    from app.rag.embedding_service import VertexAIEmbeddingService

    logger.info(
        "Initialising embedding service",
        extra={"model": settings.vertex_embedding_model, "project": settings.gcp_project_id},
    )
    embedding_service = VertexAIEmbeddingService(
        model=settings.vertex_embedding_model,
        project=settings.gcp_project_id,
    )

    # 3. Vector store
    from app.rag.chroma_store import ChromaVectorStore

    logger.info(
        "Initialising vector store",
        extra={
            "backend": "ChromaDB",
            "persist_dir": settings.chroma_persist_dir,
            "collection": settings.chroma_collection_name,
        },
    )
    _app.state.vector_store = ChromaVectorStore(
        persist_dir=settings.chroma_persist_dir,
        collection_name=settings.chroma_collection_name,
        embeddings=embedding_service.get_embeddings(),
    )

    # 4. Storage service
    from app.services.storage_service import StorageService

    logger.info(
        "Initialising storage service",
        extra={"bucket": settings.gcs_bucket_name, "prefix": settings.gcs_upload_prefix},
    )
    _app.state.storage_service = StorageService(
        bucket_name=settings.gcs_bucket_name,
        project=settings.gcp_project_id,
        upload_prefix=settings.gcs_upload_prefix,
    )

    # 5. PDF service (stateless, no I/O on init)
    from app.services.pdf_service import PDFService

    _app.state.pdf_service = PDFService()

    logger.info("Application startup complete")
    yield

    logger.info("Application shutdown")


# ─── FastAPI application ───────────────────────────────────────────────────────


app = FastAPI(
    title="Enterprise AI Knowledge Assistant API",
    description=(
        "Production-grade RAG platform built on Vertex AI, ChromaDB, "
        "and Google Cloud Storage. Document ingestion pipeline: Phase 1."
    ),
    version="0.2.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# ─── Middleware ────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Exception handlers ────────────────────────────────────────────────────────
#
# Translate domain exceptions → HTTP responses at the application boundary.
# Each handler:
#   - Returns a safe, client-readable message (no internal details)
#   - Logs the full error server-side with exc_info for stack traces
#   - Uses a machine-readable error_code for client-side branching


@app.exception_handler(InvalidPDFError)
async def handle_invalid_pdf(request: Request, exc: InvalidPDFError) -> JSONResponse:
    logger.warning("Invalid PDF upload rejected", extra={"detail": exc.message})
    return JSONResponse(
        status_code=422,
        content={"detail": exc.message, "error_code": "INVALID_PDF"},
    )


@app.exception_handler(FileTooLargeError)
async def handle_file_too_large(request: Request, exc: FileTooLargeError) -> JSONResponse:
    logger.warning(
        "File upload rejected: too large",
        extra={"size_bytes": exc.size_bytes, "limit_bytes": exc.limit_bytes},
    )
    return JSONResponse(
        status_code=413,
        content={"detail": exc.message, "error_code": "FILE_TOO_LARGE"},
    )


@app.exception_handler(StorageError)
async def handle_storage_error(request: Request, exc: StorageError) -> JSONResponse:
    logger.error("GCS storage failure", exc_info=exc.cause)
    return JSONResponse(
        status_code=502,
        content={
            "detail": "Failed to store document. Please try again.",
            "error_code": "STORAGE_ERROR",
        },
    )


@app.exception_handler(EmbeddingError)
async def handle_embedding_error(request: Request, exc: EmbeddingError) -> JSONResponse:
    logger.error("Vertex AI embedding failure", exc_info=exc.cause)
    return JSONResponse(
        status_code=502,
        content={
            "detail": "Failed to generate embeddings. Please try again.",
            "error_code": "EMBEDDING_ERROR",
        },
    )


@app.exception_handler(VectorStoreError)
async def handle_vector_store_error(request: Request, exc: VectorStoreError) -> JSONResponse:
    logger.error("Vector store failure", exc_info=exc.cause)
    return JSONResponse(
        status_code=502,
        content={
            "detail": "Failed to index document. Please try again.",
            "error_code": "VECTOR_STORE_ERROR",
        },
    )


@app.exception_handler(InfrastructureError)
async def handle_infrastructure_error(
    request: Request, exc: InfrastructureError
) -> JSONResponse:
    logger.error("Infrastructure failure (unhandled subtype)", exc_info=exc.cause)
    return JSONResponse(
        status_code=502,
        content={"detail": "A downstream service failed. Please try again.", "error_code": "INFRASTRUCTURE_ERROR"},
    )


@app.exception_handler(PlatformError)
async def handle_platform_error(request: Request, exc: PlatformError) -> JSONResponse:
    logger.error("Unhandled platform error", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred.", "error_code": "INTERNAL_ERROR"},
    )


# ─── Routes ───────────────────────────────────────────────────────────────────

app.include_router(api_router, prefix="/api/v1")
