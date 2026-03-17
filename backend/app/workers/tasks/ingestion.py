import uuid

import structlog
from sqlalchemy import delete

from app.config import settings
from app.db.models.chunk import Chunk
from app.db.models.document import Document, DocumentStatus
from app.db.models.usage_log import UsageAction, UsageLog
from app.db.session import get_sync_db
from app.services.chunking import chunk_pages
from app.services.embedding import generate_embeddings
from app.services.pdf_extraction import extract_text_from_pdf
from app.services.storage import download_file_bytes
from app.workers.celery_app import celery_app

logger = structlog.get_logger()


def _mark_failed(document_id: str, error_message: str) -> None:
    """Mark document as FAILED using its own DB session (safe in exception handlers)."""
    truncated = error_message[:2000]
    try:
        with get_sync_db() as db:
            doc = db.query(Document).filter(Document.id == uuid.UUID(document_id)).first()
            if doc:
                doc.status = DocumentStatus.FAILED
                doc.error_message = truncated
    except Exception:
        logger.exception("mark_failed_error", document_id=document_id)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def process_document(self, document_id: str, user_id: str):
    """
    Full ingestion pipeline:
    1. Download PDF from S3
    2. Extract text
    3. Chunk text deterministically
    4. Generate embeddings
    5. Store chunks + embeddings
    6. Update document status to ready
    """
    log = logger.bind(document_id=document_id, user_id=user_id, task_id=self.request.id)
    log.info("ingestion_started")

    try:
        with get_sync_db() as db:
            # 1. Load document and verify ownership
            doc = (
                db.query(Document)
                .filter(Document.id == uuid.UUID(document_id))
                .first()
            )
            if doc is None:
                raise ValueError(f"Document {document_id} not found")
            if str(doc.user_id) != user_id:
                raise ValueError(f"Document {document_id} not owned by user {user_id}")

            doc.status = DocumentStatus.PROCESSING
            db.commit()

            # Clean up partial chunks from previous failed attempts
            db.execute(
                delete(Chunk).where(Chunk.document_id == uuid.UUID(document_id))
            )
            db.commit()

            # 2. Download PDF from S3
            log.info("downloading_pdf", s3_key=doc.s3_key)
            pdf_bytes = download_file_bytes(doc.s3_key)

            # 3. Extract text
            log.info("extracting_text")
            extraction = extract_text_from_pdf(pdf_bytes, max_pages=settings.max_page_count)
            doc.page_count = extraction.page_count
            db.commit()
            log.info(
                "extraction_complete",
                page_count=extraction.page_count,
                total_chars=extraction.total_chars,
                pages_with_text=len(extraction.pages),
            )

            # 4. Chunk text
            log.info("chunking_text")
            chunks = chunk_pages(
                extraction.pages,
                target_tokens=settings.chunk_target_tokens,
                overlap_tokens=settings.chunk_overlap_tokens,
            )
            log.info("chunking_complete", chunk_count=len(chunks))

            # 5. Generate embeddings
            log.info("generating_embeddings", chunk_count=len(chunks))
            texts = [c.content for c in chunks]
            embedding_result = generate_embeddings(
                texts,
                model=settings.embedding_model,
                batch_size=settings.embedding_batch_size,
                dimensions=settings.embedding_dimensions,
            )
            log.info("embeddings_complete", total_tokens=embedding_result.total_tokens)

            # 6. Store chunks with embeddings
            log.info("storing_chunks")
            chunk_models = [
                Chunk(
                    document_id=uuid.UUID(document_id),
                    user_id=uuid.UUID(user_id),
                    chunk_index=c.chunk_index,
                    content=c.content,
                    page_start=c.page_start,
                    page_end=c.page_end,
                    token_count=c.token_count,
                    embedding=embedding_result.embeddings[i],
                )
                for i, c in enumerate(chunks)
            ]
            db.add_all(chunk_models)

            # 7. Log usage
            usage_log = UsageLog(
                user_id=uuid.UUID(user_id),
                action=UsageAction.EMBEDDING,
                tokens_used=embedding_result.total_tokens,
                document_id=uuid.UUID(document_id),
            )
            db.add(usage_log)

            # 8. Mark READY
            doc.status = DocumentStatus.READY
            doc.error_message = None
            db.commit()

            log.info(
                "ingestion_completed",
                chunk_count=len(chunks),
                total_tokens=embedding_result.total_tokens,
            )

    except ValueError as exc:
        # Permanent failure — no retry
        log.error("ingestion_permanent_failure", error=str(exc))
        _mark_failed(document_id, str(exc))
        return

    except Exception as exc:
        # Transient failure — retry with exponential backoff
        log.warning(
            "ingestion_transient_failure",
            error=str(exc),
            attempt=self.request.retries + 1,
        )
        try:
            self.retry(exc=exc, countdown=10 * (2 ** self.request.retries))
        except self.MaxRetriesExceededError:
            log.error("ingestion_max_retries_exceeded", error=str(exc))
            _mark_failed(document_id, f"Max retries exceeded: {str(exc)[:1900]}")
