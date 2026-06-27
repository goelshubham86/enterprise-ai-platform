"""Chat endpoints — stub for Phase 1."""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter()


class ChatRequest(BaseModel):
    sessionId: str | None = None
    question: str
    documentIds: list[str] = []


@router.post("")
async def chat(request: ChatRequest) -> dict:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="RAG chat will be implemented in Phase 1 backend.",
    )


@router.get("/sessions")
async def list_sessions() -> list:
    return []
