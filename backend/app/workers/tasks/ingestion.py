import structlog

from app.workers.celery_app import celery_app

logger = structlog.get_logger()


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

    Implementation in M2.
    """
    logger.info("ingestion_started", document_id=document_id, user_id=user_id)
    # Placeholder — full implementation in M2
    pass
