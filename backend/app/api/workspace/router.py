from fastapi import APIRouter, Depends

from app.db.models.user import User
from app.dependencies import get_current_user

router = APIRouter()


@router.get("/{document_id}/summary")
async def get_summary(
    document_id: str,
    user: User = Depends(get_current_user),
):
    """Get or generate document summary."""
    # Implementation in M3
    return {"ok": True, "summary": None}


@router.post("/{document_id}/chat")
async def chat(
    document_id: str,
    user: User = Depends(get_current_user),
):
    """RAG chat with the document."""
    # Implementation in M3
    return {"ok": True, "message": None}


@router.post("/{document_id}/flashcards")
async def generate_flashcards(
    document_id: str,
    user: User = Depends(get_current_user),
):
    """Generate flashcards from the document."""
    # Implementation in M4
    return {"ok": True, "flashcards": []}
