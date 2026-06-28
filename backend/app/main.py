"""Application entry point."""
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.router import api_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Initialise and tear down application-scoped resources.

    The vector store is created once here and stored in app.state so all
    requests share a single ChromaDB connection. FastAPI's Depends()
    retrieves it via app/core/dependencies.py:get_vector_store().

    To swap ChromaDB for Vertex AI Vector Search in Phase 5:
      1. Implement VertexAIVectorStore in app/rag/vertex_store.py
      2. Replace ChromaVectorStore(...) with VertexAIVectorStore(...) below
      3. Nothing else in the application needs to change
    """
    from app.rag.chroma_store import ChromaVectorStore
    from app.rag.embedding_service import VertexAIEmbeddingService

    logger.info("Initialising embedding service (model=%s)", settings.vertex_embedding_model)
    embedding_service = VertexAIEmbeddingService(
        model=settings.vertex_embedding_model,
        project=settings.gcp_project_id,
    )

    logger.info(
        "Initialising vector store (dir=%s, collection=%s)",
        settings.chroma_persist_dir,
        settings.chroma_collection_name,
    )
    _app.state.vector_store = ChromaVectorStore(
        persist_dir=settings.chroma_persist_dir,
        collection_name=settings.chroma_collection_name,
        embeddings=embedding_service.get_embeddings(),
    )

    logger.info("Application startup complete")
    yield

    logger.info("Application shutdown")


app = FastAPI(
    title="Enterprise AI Knowledge Assistant API",
    description="RAG-powered enterprise knowledge assistant built on Vertex AI + ChromaDB",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")
