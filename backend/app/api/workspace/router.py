import json
import uuid

import structlog
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
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
    DeleteFlashcardsResponse,
    FlashcardDetailResponse,
    FlashcardGenerateRequest,
    FlashcardGenerateResponse,
    FlashcardListResponse,
    FlashcardOut,
    FlashcardStatsOut,
    FlashcardUpdateRequest,
    StudyQueueResponse,
    SummaryOut,
    SummaryResponse,
)
from app.core.errors import AppError
from app.db.models.document import DocumentStatus
from app.db.models.flashcard import Flashcard, FlashcardDifficulty
from app.db.models.user import User
from app.db.session import get_db
from app.dependencies import get_current_user
from app.services import chat as chat_service
from app.services import flashcard as flashcard_service
from app.services import summary as summary_service

logger = structlog.get_logger()

router = APIRouter()


async def _get_ready_document(db: AsyncSession, document_id: str, user_id: uuid.UUID):
    """Verify document exists, belongs to user, and is READY."""
    doc = await get_user_document(db, uuid.UUID(document_id), user_id)
    if doc.status != DocumentStatus.READY:
        raise AppError(status_code=422, message="Document is not ready for analysis")
    return doc


def _flashcard_to_out(card: Flashcard) -> FlashcardOut:
    """Convert a Flashcard ORM instance to the response schema."""
    return FlashcardOut(
        id=str(card.id),
        front=card.front,
        back=card.back,
        difficulty=card.difficulty.value,
        source_chunk_id=str(card.source_chunk_id) if card.source_chunk_id else None,
        last_reviewed_at=card.last_reviewed_at.isoformat() if card.last_reviewed_at else None,
        created_at=card.created_at.isoformat(),
        updated_at=card.updated_at.isoformat(),
    )


# --- Summary ---


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


# --- Chat ---


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


# --- Flashcards ---


@router.post("/{document_id}/flashcards", response_model=FlashcardGenerateResponse)
async def generate_flashcards(
    document_id: str,
    body: FlashcardGenerateRequest = FlashcardGenerateRequest(),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate flashcards from the document."""
    document = await _get_ready_document(db, document_id, user.id)
    result = await flashcard_service.generate_flashcards(
        db, document, user.id, regenerate=body.regenerate,
    )

    return FlashcardGenerateResponse(
        flashcards=[_flashcard_to_out(c) for c in result.flashcards],
        generated_count=result.generated_count,
        was_cached=result.was_cached,
    )


@router.get("/{document_id}/flashcards", response_model=FlashcardListResponse)
async def list_flashcards(
    document_id: str,
    difficulty: str | None = Query(None, pattern="^(unrated|easy|medium|hard)$"),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List flashcards for a document with optional filtering."""
    await _get_ready_document(db, document_id, user.id)

    difficulty_enum = FlashcardDifficulty(difficulty) if difficulty else None
    cards, total = await flashcard_service.list_flashcards(
        db,
        uuid.UUID(document_id),
        user.id,
        difficulty=difficulty_enum,
        offset=offset,
        limit=limit,
    )

    return FlashcardListResponse(
        flashcards=[_flashcard_to_out(c) for c in cards],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/{document_id}/flashcards/study", response_model=StudyQueueResponse)
async def get_study_queue(
    document_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a prioritized study queue with stats."""
    await _get_ready_document(db, document_id, user.id)

    doc_uuid = uuid.UUID(document_id)
    queue = await flashcard_service.get_study_queue(db, doc_uuid, user.id)

    # Compute stats across all flashcards for this document
    stats_result = await db.execute(
        select(
            func.count().label("total"),
            func.count().filter(Flashcard.difficulty == FlashcardDifficulty.UNRATED).label("unrated"),
            func.count().filter(Flashcard.difficulty == FlashcardDifficulty.EASY).label("easy"),
            func.count().filter(Flashcard.difficulty == FlashcardDifficulty.MEDIUM).label("medium"),
            func.count().filter(Flashcard.difficulty == FlashcardDifficulty.HARD).label("hard"),
        )
        .select_from(Flashcard)
        .where(Flashcard.document_id == doc_uuid, Flashcard.user_id == user.id)
    )
    row = stats_result.one()

    return StudyQueueResponse(
        flashcards=[_flashcard_to_out(c) for c in queue],
        stats=FlashcardStatsOut(
            total=row.total,
            unrated=row.unrated,
            easy=row.easy,
            medium=row.medium,
            hard=row.hard,
        ),
    )


@router.get("/{document_id}/flashcards/{flashcard_id}", response_model=FlashcardDetailResponse)
async def get_flashcard(
    document_id: str,
    flashcard_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single flashcard."""
    await _get_ready_document(db, document_id, user.id)
    card = await flashcard_service.get_flashcard(db, uuid.UUID(flashcard_id), user.id)

    return FlashcardDetailResponse(flashcard=_flashcard_to_out(card))


@router.patch("/{document_id}/flashcards/{flashcard_id}", response_model=FlashcardDetailResponse)
async def update_flashcard(
    document_id: str,
    flashcard_id: str,
    body: FlashcardUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a flashcard's content or difficulty."""
    await _get_ready_document(db, document_id, user.id)

    difficulty_enum = FlashcardDifficulty(body.difficulty) if body.difficulty else None
    card = await flashcard_service.update_flashcard(
        db,
        uuid.UUID(flashcard_id),
        user.id,
        front=body.front,
        back=body.back,
        difficulty=difficulty_enum,
    )

    return FlashcardDetailResponse(flashcard=_flashcard_to_out(card))


@router.delete("/{document_id}/flashcards/{flashcard_id}")
async def delete_flashcard(
    document_id: str,
    flashcard_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a single flashcard."""
    await _get_ready_document(db, document_id, user.id)
    await flashcard_service.delete_flashcard(db, uuid.UUID(flashcard_id), user.id)
    return {"ok": True}


@router.delete("/{document_id}/flashcards", response_model=DeleteFlashcardsResponse)
async def delete_all_flashcards(
    document_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete all flashcards for a document."""
    await _get_ready_document(db, document_id, user.id)
    deleted = await flashcard_service.delete_all_flashcards(db, uuid.UUID(document_id), user.id)

    return DeleteFlashcardsResponse(deleted_count=deleted)
