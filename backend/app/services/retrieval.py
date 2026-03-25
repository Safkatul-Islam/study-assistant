import asyncio
import uuid
from dataclasses import dataclass

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models.chunk import Chunk
from app.services.embedding import generate_embeddings

logger = structlog.get_logger()


@dataclass(frozen=True)
class RetrievalResult:
    chunks: list  # list[Chunk] — SQLAlchemy models
    query_tokens: int


async def retrieve_relevant_chunks(
    db: AsyncSession,
    document_id: uuid.UUID,
    query: str,
    top_k: int | None = None,
) -> RetrievalResult:
    """Embed the query and find top-K similar chunks using cosine distance.

    Uses the existing embedding service (sync) wrapped in asyncio.to_thread,
    then queries pgvector for nearest neighbours filtered by document_id.
    """
    top_k = top_k or settings.rag_top_k

    log = logger.bind(document_id=str(document_id), top_k=top_k)
    log.info("retrieval_started", query_length=len(query))

    # Embed the query using the same model as ingestion
    embedding_result = await asyncio.to_thread(
        generate_embeddings,
        [query],
        model=settings.embedding_model,
        batch_size=1,
        dimensions=settings.embedding_dimensions,
    )
    query_embedding = embedding_result.embeddings[0]

    # pgvector cosine distance search
    stmt = (
        select(Chunk)
        .where(Chunk.document_id == document_id)
        .where(Chunk.embedding.isnot(None))
        .order_by(Chunk.embedding.cosine_distance(query_embedding))
        .limit(top_k)
    )
    result = await db.execute(stmt)
    chunks = list(result.scalars().all())

    log.info("retrieval_complete", chunks_found=len(chunks))

    return RetrievalResult(
        chunks=chunks,
        query_tokens=embedding_result.total_tokens,
    )
