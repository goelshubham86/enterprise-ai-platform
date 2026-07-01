"""Document management endpoints — stub for Phase 1."""
from fastapi import APIRouter, HTTPException, status

router = APIRouter()


@router.get("")
async def list_documents(page: int = 1, page_size: int = 20) -> dict:
    return {"items": [], "total": 0, "page": page, "pageSize": page_size, "hasNext": False}


@router.post("/upload")
async def upload_document() -> dict:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Document upload will be implemented in Phase 1 backend. ",
    )


@router.delete("/{document_id}")
async def delete_document(document_id: str) -> None:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not yet implemented.",
    )


@router.post("/{document_id}/reindex")
async def reindex_document(document_id: str) -> None:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not yet implemented.",
    )
