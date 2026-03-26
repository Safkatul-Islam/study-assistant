import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

import structlog
from pydantic import BaseModel, ValidationError as PydanticValidationError
from sqlalchemy import case, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.errors import AppError, NotFoundError, RateLimitError
from app.db.models.chunk import Chunk
from app.db.models.document import Document
from app.db.models.flashcard import Flashcard, FlashcardDifficulty
from app.db.models.usage_log import UsageAction, UsageLog
from app.services import llm
from app.services.usage import log_usage

logger = structlog.get_logger()

FLASHCARD_SYSTEM_PROMPT = """You are a study assistant. Generate flashcards from the document content below.

Return ONLY valid JSON matching this exact schema (no markdown, no code fences):
{{
  "flashcards": [
    {{"front": "Question or prompt", "back": "Answer or explanation", "chunk_index": 0}}
  ]
}}

Guidelines:
- Generate up to {max_cards} flashcards
- front: specific question — definitions, comparisons, cause-effect, applications
- back: clear, self-contained answer (student should understand without seeing the document)
- chunk_index: integer index of the source chunk
- Cover breadth across the document, avoid redundant cards
- Vary question types: "Define X", "What is the relationship between X and Y?", "Explain...", etc.
- Do NOT generate trivially obvious or overly broad questions"""


class FlashcardItemSchema(BaseModel):
    """Validation schema for a single LLM-generated flashcard."""

    front: str
    back: str
    chunk_index: int | None = None


class FlashcardListSchema(BaseModel):
    """Validation schema for LLM-generated flashcard list."""

    flashcards: list[FlashcardItemSchema]


@dataclass(frozen=True)
class GenerationResult:
    flashcards: list[Flashcard]
    generated_count: int
    was_cached: bool
    input_tokens: int
    output_tokens: int


async def generate_flashcards(
    db: AsyncSession,
    document: Document,
    user_id: uuid.UUID,
    *,
    regenerate: bool = False,
) -> GenerationResult:
    """Generate flashcards for a document, or return cached ones."""
    log = logger.bind(document_id=str(document.id), user_id=str(user_id))

    await _check_daily_limit(db, user_id)

    # Check for existing flashcards
    existing_count_result = await db.execute(
        select(func.count())
        .select_from(Flashcard)
        .where(Flashcard.document_id == document.id, Flashcard.user_id == user_id)
    )
    existing_count = existing_count_result.scalar_one()

    if existing_count > 0 and not regenerate:
        log.info("flashcards_cache_hit", count=existing_count)
        result = await db.execute(
            select(Flashcard)
            .where(Flashcard.document_id == document.id, Flashcard.user_id == user_id)
            .order_by(Flashcard.created_at)
        )
        cached_cards = list(result.scalars().all())
        return GenerationResult(
            flashcards=cached_cards,
            generated_count=len(cached_cards),
            was_cached=True,
            input_tokens=0,
            output_tokens=0,
        )

    if existing_count > 0 and regenerate:
        log.info("flashcards_regenerate", deleted=existing_count)
        await db.execute(
            delete(Flashcard).where(
                Flashcard.document_id == document.id,
                Flashcard.user_id == user_id,
            )
        )

    # Fetch chunks ordered by index
    result = await db.execute(
        select(Chunk)
        .where(Chunk.document_id == document.id)
        .order_by(Chunk.chunk_index)
    )
    chunks = list(result.scalars().all())

    if not chunks:
        raise AppError(status_code=422, message="Document has no content to generate flashcards from")

    # Build document content respecting token limit
    content_parts: list[str] = []
    total_tokens = 0

    for chunk in chunks:
        if total_tokens + chunk.token_count > settings.summary_max_context_tokens:
            log.warning(
                "flashcard_content_truncated",
                included_chunks=len(content_parts),
                total_chunks=len(chunks),
                token_limit=settings.summary_max_context_tokens,
            )
            break

        page_label = _page_label(chunk.page_start, chunk.page_end)
        content_parts.append(f"[Chunk {chunk.chunk_index}, {page_label}]\n{chunk.content}")
        total_tokens += chunk.token_count

    document_content = "\n\n---\n\n".join(content_parts)

    # Interpolate max_cards into system prompt
    system_prompt = FLASHCARD_SYSTEM_PROMPT.format(max_cards=settings.flashcard_max_per_document)

    # Generate flashcards via LLM
    messages = [{"role": "user", "content": document_content}]

    response = await llm.complete(
        system_prompt=system_prompt,
        messages=messages,
        temperature=settings.flashcard_generation_temperature,
    )

    # Parse and validate JSON response
    parsed_items = _parse_flashcard_json(response.content, log)

    # Build chunk_index → chunk.id map
    chunk_id_map: dict[int, uuid.UUID] = {
        chunk.chunk_index: chunk.id for chunk in chunks
    }

    # Create Flashcard ORM instances
    created_cards: list[Flashcard] = []
    for item in parsed_items:
        source_chunk_id = (
            chunk_id_map.get(item.chunk_index)
            if item.chunk_index is not None
            else None
        )
        card = Flashcard(
            document_id=document.id,
            user_id=user_id,
            front=item.front,
            back=item.back,
            source_chunk_id=source_chunk_id,
            difficulty=FlashcardDifficulty.UNRATED,
        )
        db.add(card)
        created_cards.append(card)

    await db.flush()

    # Log usage
    await log_usage(
        db=db,
        user_id=user_id,
        action=UsageAction.FLASHCARD_GENERATION,
        tokens_used=response.total_tokens,
        document_id=document.id,
        metadata={"model": settings.anthropic_model, "card_count": len(created_cards)},
    )

    log.info(
        "flashcards_generated",
        count=len(created_cards),
        input_tokens=response.input_tokens,
        output_tokens=response.output_tokens,
    )

    return GenerationResult(
        flashcards=created_cards,
        generated_count=len(created_cards),
        was_cached=False,
        input_tokens=response.input_tokens,
        output_tokens=response.output_tokens,
    )


async def _check_daily_limit(db: AsyncSession, user_id: uuid.UUID) -> None:
    """Raise RateLimitError if user exceeded daily flashcard generation limit."""
    result = await db.execute(
        select(func.count())
        .select_from(UsageLog)
        .where(
            UsageLog.user_id == user_id,
            UsageLog.action == UsageAction.FLASHCARD_GENERATION,
            func.date(UsageLog.created_at) == func.current_date(),
        )
    )
    count = result.scalar_one()

    if count >= settings.daily_flashcard_generation_limit:
        raise RateLimitError(
            message=f"Daily flashcard generation limit reached ({settings.daily_flashcard_generation_limit})"
        )


def _parse_flashcard_json(
    content: str, log: structlog.stdlib.BoundLogger
) -> list[FlashcardItemSchema]:
    """Parse and validate the LLM response as a flashcard list."""
    text = content.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        text = text.strip()

    try:
        data = json.loads(text)
        validated = FlashcardListSchema.model_validate(data)
        # Truncate to max allowed
        return validated.flashcards[: settings.flashcard_max_per_document]
    except (json.JSONDecodeError, PydanticValidationError) as exc:
        log.error("flashcard_json_parse_error", error=str(exc), raw_content=text[:500])
        raise AppError(
            status_code=503,
            message="AI service returned an invalid response",
        ) from exc


async def list_flashcards(
    db: AsyncSession,
    document_id: uuid.UUID,
    user_id: uuid.UUID,
    *,
    difficulty: FlashcardDifficulty | None = None,
    offset: int = 0,
    limit: int = 50,
) -> tuple[list[Flashcard], int]:
    """List flashcards with optional difficulty filter and pagination."""
    where_clauses = [Flashcard.document_id == document_id, Flashcard.user_id == user_id]

    if difficulty is not None:
        where_clauses.append(Flashcard.difficulty == difficulty)

    # Total count
    count_result = await db.execute(
        select(func.count()).select_from(Flashcard).where(*where_clauses)
    )
    total = count_result.scalar_one()

    # Fetch page
    result = await db.execute(
        select(Flashcard)
        .where(*where_clauses)
        .order_by(Flashcard.created_at)
        .offset(offset)
        .limit(limit)
    )
    flashcards = list(result.scalars().all())

    return flashcards, total


async def get_flashcard(
    db: AsyncSession,
    flashcard_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Flashcard:
    """Get a single flashcard by id, scoped to user."""
    result = await db.execute(
        select(Flashcard).where(Flashcard.id == flashcard_id, Flashcard.user_id == user_id)
    )
    card = result.scalar_one_or_none()

    if card is None:
        raise NotFoundError("Flashcard")

    return card


async def update_flashcard(
    db: AsyncSession,
    flashcard_id: uuid.UUID,
    user_id: uuid.UUID,
    *,
    front: str | None = None,
    back: str | None = None,
    difficulty: FlashcardDifficulty | None = None,
) -> Flashcard:
    """Update a flashcard's content or difficulty."""
    card = await get_flashcard(db, flashcard_id, user_id)

    if front is not None:
        card.front = front
    if back is not None:
        card.back = back
    if difficulty is not None:
        card.difficulty = difficulty
        card.last_reviewed_at = datetime.now(timezone.utc)

    await db.flush()
    return card


async def delete_flashcard(
    db: AsyncSession,
    flashcard_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    """Delete a single flashcard."""
    card = await get_flashcard(db, flashcard_id, user_id)
    await db.delete(card)
    await db.flush()


async def delete_all_flashcards(
    db: AsyncSession,
    document_id: uuid.UUID,
    user_id: uuid.UUID,
) -> int:
    """Delete all flashcards for a document. Returns deleted count."""
    result = await db.execute(
        delete(Flashcard).where(
            Flashcard.document_id == document_id,
            Flashcard.user_id == user_id,
        )
    )
    return result.rowcount


async def get_study_queue(
    db: AsyncSession,
    document_id: uuid.UUID,
    user_id: uuid.UUID,
    *,
    limit: int = 20,
) -> list[Flashcard]:
    """Get a prioritized study queue: hard > medium > unrated > easy, then least recently reviewed."""
    priority = case(
        (Flashcard.difficulty == FlashcardDifficulty.HARD, 1),
        (Flashcard.difficulty == FlashcardDifficulty.MEDIUM, 2),
        (Flashcard.difficulty == FlashcardDifficulty.UNRATED, 3),
        (Flashcard.difficulty == FlashcardDifficulty.EASY, 4),
    )

    result = await db.execute(
        select(Flashcard)
        .where(Flashcard.document_id == document_id, Flashcard.user_id == user_id)
        .order_by(priority, Flashcard.last_reviewed_at.asc().nulls_first())
        .limit(limit)
    )
    return list(result.scalars().all())


def _page_label(page_start: int | None, page_end: int | None) -> str:
    """Format a human-readable page label."""
    if page_start is None:
        return "Pages unknown"
    if page_end is None or page_start == page_end:
        return f"Page {page_start}"
    return f"Pages {page_start}-{page_end}"
