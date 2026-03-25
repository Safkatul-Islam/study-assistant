import json
import uuid
from dataclasses import dataclass

import structlog
from pydantic import BaseModel, ValidationError as PydanticValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.errors import AppError
from app.db.models.chunk import Chunk
from app.db.models.document import Document
from app.db.models.usage_log import UsageAction
from app.services import llm
from app.services.usage import log_usage

logger = structlog.get_logger()

SUMMARY_SYSTEM_PROMPT = """You are a study assistant. Analyze the following document content and produce a structured summary.

Return ONLY valid JSON matching this exact schema (no markdown, no code fences, no extra text):
{
  "executive_summary": ["bullet point 1", "bullet point 2", "..."],
  "key_concepts": ["concept 1", "concept 2", "..."],
  "definitions": {"term1": "definition1", "term2": "definition2"},
  "possible_questions": ["question 1", "question 2", "..."]
}

Guidelines:
- executive_summary: 3-5 concise bullet points capturing the document's main ideas
- key_concepts: 5-10 important topics or themes
- definitions: key terms with clear, concise definitions
- possible_questions: 5-8 study questions a student might be asked"""


class SummarySchema(BaseModel):
    """Validation schema for LLM-generated summaries."""
    executive_summary: list[str]
    key_concepts: list[str]
    definitions: dict[str, str]
    possible_questions: list[str]


@dataclass(frozen=True)
class StructuredSummary:
    executive_summary: list[str]
    key_concepts: list[str]
    definitions: dict[str, str]
    possible_questions: list[str]


async def get_or_generate_summary(
    db: AsyncSession,
    document: Document,
    user_id: uuid.UUID,
) -> tuple[StructuredSummary, bool]:
    """Return cached summary or generate a new one.

    Returns (summary, was_cached).
    """
    log = logger.bind(document_id=str(document.id), user_id=str(user_id))

    # Check cache
    if document.summary_cache:
        log.info("summary_cache_hit")
        data = json.loads(document.summary_cache)
        return StructuredSummary(**data), True

    log.info("summary_cache_miss")

    # Fetch all chunks ordered by index
    result = await db.execute(
        select(Chunk)
        .where(Chunk.document_id == document.id)
        .order_by(Chunk.chunk_index)
    )
    chunks = list(result.scalars().all())

    if not chunks:
        raise AppError(status_code=422, message="Document has no content to analyze")

    # Build document content from chunks, respecting token limit
    content_parts: list[str] = []
    total_tokens = 0

    for chunk in chunks:
        if total_tokens + chunk.token_count > settings.summary_max_context_tokens:
            log.warning(
                "summary_content_truncated",
                included_chunks=len(content_parts),
                total_chunks=len(chunks),
                token_limit=settings.summary_max_context_tokens,
            )
            break

        page_label = _page_label(chunk.page_start, chunk.page_end)
        content_parts.append(f"[Chunk {chunk.chunk_index}, {page_label}]\n{chunk.content}")
        total_tokens += chunk.token_count

    document_content = "\n\n---\n\n".join(content_parts)

    # Generate summary via LLM
    messages = [{"role": "user", "content": document_content}]

    response = await llm.complete(
        system_prompt=SUMMARY_SYSTEM_PROMPT,
        messages=messages,
    )

    # Parse and validate JSON response
    summary = _parse_summary_json(response.content, log)

    # Cache the result
    cache_json = json.dumps({
        "executive_summary": summary.executive_summary,
        "key_concepts": summary.key_concepts,
        "definitions": summary.definitions,
        "possible_questions": summary.possible_questions,
    })
    document.summary_cache = cache_json
    await db.flush()

    # Log usage
    await log_usage(
        db=db,
        user_id=user_id,
        action=UsageAction.SUMMARY,
        tokens_used=response.total_tokens,
        document_id=document.id,
        metadata={"model": settings.anthropic_model},
    )

    log.info(
        "summary_generated",
        input_tokens=response.input_tokens,
        output_tokens=response.output_tokens,
    )

    return summary, False


def _parse_summary_json(content: str, log: structlog.stdlib.BoundLogger) -> StructuredSummary:
    """Parse and validate the LLM response as a structured summary."""
    # Strip markdown code fences if present
    text = content.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first and last lines (code fences)
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        text = text.strip()

    try:
        data = json.loads(text)
        validated = SummarySchema.model_validate(data)
        return StructuredSummary(
            executive_summary=validated.executive_summary,
            key_concepts=validated.key_concepts,
            definitions=validated.definitions,
            possible_questions=validated.possible_questions,
        )
    except (json.JSONDecodeError, PydanticValidationError) as exc:
        log.error("summary_json_parse_error", error=str(exc), raw_content=text[:500])
        raise AppError(
            status_code=503,
            message="AI service returned an invalid response",
        ) from exc


def _page_label(page_start: int | None, page_end: int | None) -> str:
    """Format a human-readable page label."""
    if page_start is None:
        return "Pages unknown"
    if page_end is None or page_start == page_end:
        return f"Page {page_start}"
    return f"Pages {page_start}-{page_end}"
