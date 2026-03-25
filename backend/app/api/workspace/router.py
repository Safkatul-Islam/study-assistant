import json
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.documents.service import get_user_document
from app.api.workspace.schemas import (
    ChatHistoryResponse,
    ChatMessageOut,
    ChatRequest,
    ChatResponse,
    ChatSessionOut,
    ChatSessionsResponse,
    CitationOut,
    SummaryOut,
    SummaryResponse,
)
from app.core.errors import AppError
from app.db.models.document import DocumentStatus
from app.db.models.user import User
from app.db.session import get_db
from app.dependencies import get_current_user
from app.services import chat as chat_service
from app.services import summary as summary_service

router = APIRouter()


async def _get_ready_document(db: AsyncSession, document_id: str, user_id: uuid.UUID):
    """Verify document exists, belongs to user, and is READY."""
    doc = await get_user_document(db, uuid.UUID(document_id), user_id)
    if doc.status != DocumentStatus.READY:
        raise AppError(status_code=422, message="Document is not ready for analysis")
    return doc


@router.get("/{document_id}/summary", response_model=SummaryResponse)
async def get_summary(
    document_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get or generate document summary."""
    document = await _get_ready_document(db, document_id, user.id)
    summary, was_cached = await summary_service.get_or_generate_summary(db, document, user.id)

    return SummaryResponse(
        summary=SummaryOut(
            executive_summary=summary.executive_summary,
            key_concepts=summary.key_concepts,
            definitions=summary.definitions,
            possible_questions=summary.possible_questions,
        ),
        cached=was_cached,
    )


@router.post("/{document_id}/chat", response_model=ChatResponse)
async def chat(
    document_id: str,
    body: ChatRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """RAG chat with the document."""
    await _get_ready_document(db, document_id, user.id)

    session_uuid = uuid.UUID(body.session_id) if body.session_id else None
    session, assistant_msg, result = await chat_service.send_message(
        db=db,
        user_id=user.id,
        document_id=uuid.UUID(document_id),
        session_id=session_uuid,
        user_message=body.message,
    )

    # Parse citations from stored JSON
    citations = None
    if assistant_msg.citations:
        raw_citations = json.loads(assistant_msg.citations)
        citations = [CitationOut(**c) for c in raw_citations]

    return ChatResponse(
        session_id=str(session.id),
        message=ChatMessageOut(
            id=str(assistant_msg.id),
            role=assistant_msg.role.value,
            content=assistant_msg.content,
            citations=citations,
            created_at=assistant_msg.created_at.isoformat(),
        ),
    )


@router.get("/{document_id}/chat", response_model=ChatSessionsResponse)
async def list_chat_sessions(
    document_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List chat sessions for a document."""
    await _get_ready_document(db, document_id, user.id)
    sessions = await chat_service.get_document_sessions(db, uuid.UUID(document_id), user.id)

    return ChatSessionsResponse(
        sessions=[
            ChatSessionOut(
                id=str(s.id),
                title=s.title,
                created_at=s.created_at.isoformat(),
            )
            for s in sessions
        ],
    )


@router.get("/{document_id}/chat/{session_id}", response_model=ChatHistoryResponse)
async def get_chat_history(
    document_id: str,
    session_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get chat history for a session."""
    await _get_ready_document(db, document_id, user.id)
    session, messages = await chat_service.get_session_with_messages(
        db, uuid.UUID(session_id), user.id,
    )

    return ChatHistoryResponse(
        session=ChatSessionOut(
            id=str(session.id),
            title=session.title,
            created_at=session.created_at.isoformat(),
        ),
        messages=[
            ChatMessageOut(
                id=str(m.id),
                role=m.role.value,
                content=m.content,
                citations=[CitationOut(**c) for c in json.loads(m.citations)] if m.citations else None,
                created_at=m.created_at.isoformat(),
            )
            for m in messages
        ],
    )


@router.post("/{document_id}/flashcards")
async def generate_flashcards(
    document_id: str,
    user: User = Depends(get_current_user),
):
    """Generate flashcards from the document."""
    # Implementation in M4
    return {"ok": True, "flashcards": []}
