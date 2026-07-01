"""Application entry point."""

from __future__ import annotations

import asyncio
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
    ServiceNotReadyError,
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

    Cloud Run startup probe strategy
    ---------------------------------
    uvicorn binds port 8080 only AFTER the lifespan coroutine yields.
    If the yield is placed after blocking GCP initialisation, the startup
    probe receives CONNECTION_REFUSED for the full init duration and the
    deployment fails.

    Fix: schedule all service initialisation in a background asyncio task,
    then yield immediately.  uvicorn binds the socket and answers the probe
    within milliseconds.  Services become available as the background task
    completes (typically 5–30 s).

    Request handling during background init
    ----------------------------------------
    Endpoints that depend on a service (upload, etc.) call dependency
    providers (get_vector_store, get_storage_service, get_pdf_service) which
    raise ServiceNotReadyError → HTTP 503 if app.state is still None.
    The health endpoint returns status="starting" during this window.

    To swap implementations (e.g. Phase 5 → Vertex AI Vector Search):
        - Change the concrete type constructed inside _init_services()
        - Nothing in dependencies.py or the endpoints changes
    """
    configure_logging(level=settings.log_level)

    # Initialise state with None / False defaults before yielding.
    # Background task fills these in; dependency guards check them.
    _app.state.vector_store = None
    _app.state.storage_service = None
    _app.state.pdf_service = None
    _app.state._services_ready = False
    _app.state._init_error = None

    async def _init_services() -> None:
        """Blocking GCP service setup, run in background after yield.

        Each blocking call is wrapped in asyncio.to_thread() so the event
        loop stays free to handle health probes while init is in progress.
        Startup order:
            1. EmbeddingService  (passed to VectorStore)
            2. VectorStore       (depends on EmbeddingService)
            3. StorageService    (independent)
            4. PDFService        (stateless, no I/O)
        """
        try:
            from app.rag.embedding_service import VertexAIEmbeddingService

            logger.info(
                "Initialising embedding service",
                extra={"model": settings.vertex_embedding_model, "project": settings.gcp_project_id},
            )
            embedding_service = await asyncio.to_thread(
                lambda: VertexAIEmbeddingService(
                    model=settings.vertex_embedding_model,
                    project=settings.gcp_project_id,
                )
            )
            logger.info("Embedding service ready")

            from app.rag.chroma_store import ChromaVectorStore

            logger.info(
                "Initialising vector store",
                extra={
                    "backend": "ChromaDB",
                    "persist_dir": settings.chroma_persist_dir,
                    "collection": settings.chroma_collection_name,
                },
            )
            _app.state.vector_store = await asyncio.to_thread(
                lambda: ChromaVectorStore(
                    persist_dir=settings.chroma_persist_dir,
                    collection_name=settings.chroma_collection_name,
                    embeddings=embedding_service.get_embeddings(),
                )
            )
            logger.info("Vector store ready")

            from app.services.storage_service import StorageService

            logger.info(
                "Initialising storage service",
                extra={"bucket": settings.gcs_bucket_name, "prefix": settings.gcs_upload_prefix},
            )
            _app.state.storage_service = await asyncio.to_thread(
                lambda: StorageService(
                    bucket_name=settings.gcs_bucket_name,
                    project=settings.gcp_project_id,
                    upload_prefix=settings.gcs_upload_prefix,
                )
            )
            logger.info("Storage service ready")

            from app.services.pdf_service import PDFService

            _app.state.pdf_service = PDFService()

            _app.state._services_ready = True
            logger.info("All services initialised — application fully ready")

        except Exception as exc:
            _app.state._init_error = str(exc)
            logger.error(
                "Service initialisation failed",
                extra={"error": str(exc)},
                exc_info=True,
            )

    # Yield BEFORE init completes → uvicorn binds 8080 → probe gets 200.
    init_task = asyncio.create_task(_init_services())
    logger.info(
        "Application starting — services initialising in background",
        extra={"env": settings.app_env, "log_level": settings.log_level},
    )

    yield

    # Graceful shutdown: cancel the init task if it is still running.
    if not init_task.done():
        init_task.cancel()
        try:
            await init_task
        except asyncio.CancelledError:
            pass

    logger.info("Application shutdown complete")


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


@app.exception_handler(ServiceNotReadyError)
async def handle_service_not_ready(request: Request, exc: ServiceNotReadyError) -> JSONResponse:
    logger.warning("Request rejected — services still initialising")
    return JSONResponse(
        status_code=503,
        content={"detail": exc.message, "error_code": "SERVICE_NOT_READY"},
        headers={"Retry-After": "10"},
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


# ─── Root health probe ────────────────────────────────────────────────────────
#
# Cloud Run's default HTTP startup probe hits GET /. If the app returns 4xx
# on that path the container is considered unhealthy and the deployment fails.
# This minimal endpoint always returns 200 so the probe succeeds even while
# the full /api/v1/health logic is being evaluated.


@app.get("/", include_in_schema=False)
async def root_health_probe() -> dict:
    return {"status": "ok"}
