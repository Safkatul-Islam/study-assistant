from __future__ import annotations

import time
from dataclasses import dataclass

import structlog
from openai import OpenAI

from app.config import settings

logger = structlog.get_logger()

MAX_RETRIES = 3
BACKOFF_BASE = 1  # seconds


@dataclass(frozen=True)
class EmbeddingResult:
    embeddings: list[list[float]]
    total_tokens: int


def generate_embeddings(
    texts: list[str],
    model: str = settings.embedding_model,
    batch_size: int = settings.embedding_batch_size,
    dimensions: int = settings.embedding_dimensions,
) -> EmbeddingResult:
    """Generate embeddings for a list of texts using the OpenAI API.

    Batches requests and retries on transient failures (429, 5xx).
    Raises RuntimeError on permanent failure.
    """
    if not texts:
        return EmbeddingResult(embeddings=[], total_tokens=0)

    client = OpenAI(api_key=settings.openai_api_key)
    all_embeddings: list[list[float]] = []
    total_tokens = 0

    for batch_start in range(0, len(texts), batch_size):
        batch = texts[batch_start : batch_start + batch_size]
        batch_embeddings = _embed_batch_with_retry(
            client, batch, model, dimensions, batch_start, len(texts)
        )
        all_embeddings.extend(batch_embeddings.embeddings)
        total_tokens += batch_embeddings.total_tokens

    return EmbeddingResult(embeddings=all_embeddings, total_tokens=total_tokens)


def _embed_batch_with_retry(
    client: OpenAI,
    batch: list[str],
    model: str,
    dimensions: int,
    batch_start: int,
    total_texts: int,
) -> EmbeddingResult:
    """Embed a single batch with retry logic for transient errors."""
    last_error: Exception | None = None

    for attempt in range(MAX_RETRIES):
        try:
            response = client.embeddings.create(
                input=batch,
                model=model,
                dimensions=dimensions,
            )
            embeddings = [item.embedding for item in response.data]
            return EmbeddingResult(
                embeddings=embeddings,
                total_tokens=response.usage.total_tokens,
            )
        except Exception as exc:
            last_error = exc
            error_str = str(exc)
            is_retryable = "429" in error_str or "5" in error_str[:1] or "server" in error_str.lower()

            if not is_retryable or attempt == MAX_RETRIES - 1:
                break

            wait_time = BACKOFF_BASE * (2 ** attempt)
            logger.warning(
                "embedding_retry",
                attempt=attempt + 1,
                max_retries=MAX_RETRIES,
                wait_seconds=wait_time,
                batch_start=batch_start,
                total_texts=total_texts,
                error=error_str,
            )
            time.sleep(wait_time)

    raise RuntimeError(
        f"Embedding failed after {MAX_RETRIES} attempts: {last_error}"
    ) from last_error
