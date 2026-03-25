import json
import re
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.errors import AppError, NotFoundError, RateLimitError
from app.db.models.chat import ChatMessage, ChatSession, MessageRole
from app.db.models.chunk import Chunk
from app.db.models.usage_log import UsageAction, UsageLog
from app.services import llm
from app.services.retrieval import retrieve_relevant_chunks
from app.services.usage import log_usage

logger = structlog.get_logger()

CITATION_PATTERN = re.compile(r"\[CHUNK:([a-f0-9-]+)\]")

RAG_SYSTEM_PROMPT = """You are a knowledgeable study assistant helping a student understand a document.

RULES:
1. Answer based ONLY on the provided context chunks below.
2. When you reference information from a specific chunk, cite it using [CHUNK:chunk_id] format, where chunk_id is the exact ID shown in the chunk header.
3. If the answer is not in the provided context, say so clearly — do not make up information.
4. Be concise, accurate, and helpful.

CONTEXT CHUNKS:
{context}"""


@dataclass(frozen=True)
class CitationData:
    chunk_id: str
    page_start: int | None
    page_end: int | None
    snippet: str


@dataclass(frozen=True)
class ChatResult:
    content: str
    citations: list[CitationData]
    input_tokens: int
    output_tokens: int


async def send_message(
    db: AsyncSession,
    user_id: uuid.UUID,
    document_id: uuid.UUID,
    session_id: uuid.UUID | None,
    user_message: str,
) -> tuple[ChatSession, ChatMessage, ChatResult]:
    """Process a user message: check limits, retrieve context, call LLM, save messages.

    Returns (session, assistant_message, chat_result).
    """
    log = logger.bind(
        user_id=str(user_id),
        document_id=str(document_id),
    )

    # 1. Rate limit check
    await check_daily_limit(db, user_id)

    # 2. Get or create session
    session = await get_or_create_session(db, user_id, document_id, session_id)
    log = log.bind(session_id=str(session.id))

    # 3. Save user message
    user_msg = ChatMessage(
        session_id=session.id,
        role=MessageRole.USER,
        content=user_message,
    )
    db.add(user_msg)
    await db.flush()

    # 4. Load recent history (excluding the message we just saved)
    history = await _load_history(db, session.id, limit=settings.rag_max_history_messages)

    # 5. Retrieve relevant chunks
    retrieval = await retrieve_relevant_chunks(db, document_id, user_message)

    # 6. Build messages for LLM
    system_prompt, llm_messages = _build_rag_messages(
        history=history,
        context_chunks=retrieval.chunks,
        user_message=user_message,
    )

    # 7. Call LLM
    log.info("chat_llm_call", context_chunks=len(retrieval.chunks))
    response = await llm.complete(
        system_prompt=system_prompt,
        messages=llm_messages,
    )

    # 8. Extract citations
    citations = _extract_citations(response.content, retrieval.chunks)

    # 9. Clean citation markers from displayed content
    clean_content = CITATION_PATTERN.sub("", response.content).strip()
    # Collapse multiple spaces left by removed markers
    clean_content = re.sub(r"  +", " ", clean_content)

    # 10. Save assistant message
    citations_json = json.dumps([
        {
            "chunk_id": c.chunk_id,
            "page_start": c.page_start,
            "page_end": c.page_end,
            "snippet": c.snippet,
        }
        for c in citations
    ]) if citations else None

    assistant_msg = ChatMessage(
        session_id=session.id,
        role=MessageRole.ASSISTANT,
        content=clean_content,
        citations=citations_json,
        token_count=response.total_tokens,
    )
    db.add(assistant_msg)
    await db.flush()

    # 11. Log usage
    await log_usage(
        db=db,
        user_id=user_id,
        action=UsageAction.CHAT,
        tokens_used=response.total_tokens,
        document_id=document_id,
        metadata={
            "model": settings.anthropic_model,
            "query_tokens": retrieval.query_tokens,
            "context_chunks": len(retrieval.chunks),
        },
    )

    log.info(
        "chat_message_processed",
        input_tokens=response.input_tokens,
        output_tokens=response.output_tokens,
        citations_count=len(citations),
    )

    return session, assistant_msg, ChatResult(
        content=clean_content,
        citations=citations,
        input_tokens=response.input_tokens,
        output_tokens=response.output_tokens,
    )


async def get_or_create_session(
    db: AsyncSession,
    user_id: uuid.UUID,
    document_id: uuid.UUID,
    session_id: uuid.UUID | None,
) -> ChatSession:
    """Get existing session or create a new one."""
    if session_id:
        result = await db.execute(
            select(ChatSession).where(
                ChatSession.id == session_id,
                ChatSession.user_id == user_id,
                ChatSession.document_id == document_id,
            )
        )
        session = result.scalar_one_or_none()
        if not session:
            raise NotFoundError("Chat session")
        return session

    # Create new session
    session = ChatSession(
        user_id=user_id,
        document_id=document_id,
        title="New Chat",
    )
    db.add(session)
    await db.flush()
    return session


async def check_daily_limit(db: AsyncSession, user_id: uuid.UUID) -> None:
    """Raise RateLimitError if user exceeded daily_chat_limit."""
    today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)

    result = await db.execute(
        select(func.count())
        .select_from(UsageLog)
        .where(
            UsageLog.user_id == user_id,
            UsageLog.action == UsageAction.CHAT,
            UsageLog.created_at >= today_start,
        )
    )
    count = result.scalar() or 0

    if count >= settings.daily_chat_limit:
        raise RateLimitError(
            f"Daily chat limit ({settings.daily_chat_limit}) reached. Try again tomorrow."
        )


async def get_document_sessions(
    db: AsyncSession,
    document_id: uuid.UUID,
    user_id: uuid.UUID,
) -> list[ChatSession]:
    """List all chat sessions for a document belonging to a user."""
    result = await db.execute(
        select(ChatSession)
        .where(
            ChatSession.document_id == document_id,
            ChatSession.user_id == user_id,
        )
        .order_by(ChatSession.created_at.desc())
    )
    return list(result.scalars().all())


async def get_session_with_messages(
    db: AsyncSession,
    session_id: uuid.UUID,
    user_id: uuid.UUID,
) -> tuple[ChatSession, list[ChatMessage]]:
    """Load a chat session with all its messages."""
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise NotFoundError("Chat session")

    msg_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    )
    messages = list(msg_result.scalars().all())

    return session, messages


async def _load_history(
    db: AsyncSession,
    session_id: uuid.UUID,
    limit: int,
) -> list[ChatMessage]:
    """Load the most recent messages from a session for context."""
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
    )
    messages = list(result.scalars().all())
    # Reverse to get chronological order
    messages.reverse()
    return messages


def _build_rag_messages(
    history: list[ChatMessage],
    context_chunks: list[Chunk],
    user_message: str,
) -> tuple[str, list[dict[str, str]]]:
    """Build system prompt and message list for the LLM call.

    Returns (system_prompt, messages).
    """
    # Build context block from chunks
    context_parts: list[str] = []
    for chunk in context_chunks:
        page_info = _page_label(chunk.page_start, chunk.page_end)
        # Truncate chunk content if needed
        content = chunk.content
        if chunk.token_count > settings.rag_max_chunk_tokens:
            # Rough truncation — take first portion
            char_limit = settings.rag_max_chunk_tokens * 4  # ~4 chars per token
            content = content[:char_limit] + "..."

        context_parts.append(
            f"[CHUNK:{chunk.id}] ({page_info})\n{content}"
        )

    context_block = "\n---\n".join(context_parts) if context_parts else "(No relevant content found)"
    system_prompt = RAG_SYSTEM_PROMPT.format(context=context_block)

    # Build message history
    messages: list[dict[str, str]] = []
    for msg in history:
        # Skip the current user message if it's in history (we add it fresh below)
        messages.append({
            "role": msg.role.value,
            "content": msg.content,
        })

    # Add current user message
    messages.append({"role": "user", "content": user_message})

    return system_prompt, messages


def _extract_citations(
    response_text: str,
    context_chunks: list[Chunk],
) -> list[CitationData]:
    """Extract citations from the LLM response by matching [CHUNK:id] markers."""
    chunk_map = {str(chunk.id): chunk for chunk in context_chunks}
    seen: set[str] = set()
    citations: list[CitationData] = []

    for match in CITATION_PATTERN.finditer(response_text):
        chunk_id = match.group(1)
        if chunk_id in seen or chunk_id not in chunk_map:
            continue

        seen.add(chunk_id)
        chunk = chunk_map[chunk_id]
        citations.append(CitationData(
            chunk_id=chunk_id,
            page_start=chunk.page_start,
            page_end=chunk.page_end,
            snippet=chunk.content[:200],
        ))

    return citations


def _page_label(page_start: int | None, page_end: int | None) -> str:
    """Format a human-readable page label."""
    if page_start is None:
        return "Pages unknown"
    if page_end is None or page_start == page_end:
        return f"Page {page_start}"
    return f"Pages {page_start}-{page_end}"
