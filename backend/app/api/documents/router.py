import asyncio
import re
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.documents.schemas import (
    CompleteUploadRequest,
    DocumentListResponse,
    DocumentOut,
    DocumentResponse,
    InitUploadRequest,
    InitUploadResponse,
)
from app.api.documents.service import (
    create_document,
    delete_user_document,
    get_user_document,
    get_user_documents,
    update_document_status,
)
from app.config import settings
from app.core.errors import AppError
from app.db.models.document import DocumentStatus
from app.db.models.user import User
from app.db.session import get_db
from app.dependencies import get_current_user
from app.services.storage import delete_s3_object, generate_presigned_upload_url
from app.workers.tasks.ingestion import process_document

router = APIRouter()

ALLOWED_CONTENT_TYPES = {"application/pdf"}


def _sanitize_filename(name: str) -> str:
    """Strip path components and dangerous characters from filename."""
    # Take only the basename (strip any directory traversal)
    name = name.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    # Allow only alphanumeric, hyphens, underscores, dots, spaces
    name = re.sub(r"[^\w.\- ]", "_", name)
    # Collapse multiple underscores/dots
    name = re.sub(r"[_.]{2,}", "_", name)
    return name or "document.pdf"


@router.post("/init-upload", response_model=InitUploadResponse, status_code=201)
async def init_upload(
    body: InitUploadRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Validate file size
    if body.file_size > settings.max_file_size_bytes:
        raise AppError(
            status_code=422,
            message=f"File too large. Maximum size is {settings.max_file_size_mb}MB",
        )

    # Validate content type
    if body.content_type not in ALLOWED_CONTENT_TYPES:
        raise AppError(status_code=422, message="Only PDF files are supported")

    # Generate IDs and S3 key
    doc_id = uuid.uuid4()
    safe_name = _sanitize_filename(body.file_name)
    s3_key = f"{user.id}/{doc_id}/{safe_name}"

    # Derive title from filename (strip extension)
    title = safe_name.rsplit(".", 1)[0] if "." in safe_name else safe_name

    # Create document record
    document = await create_document(
        db=db,
        user_id=user.id,
        title=title,
        file_name=body.file_name,
        file_size=body.file_size,
        s3_key=s3_key,
        doc_id=doc_id,
    )

    # Generate presigned URL
    upload_url = await asyncio.to_thread(generate_presigned_upload_url, s3_key, body.content_type)

    return InitUploadResponse(
        document_id=str(document.id),
        upload_url=upload_url,
        s3_key=s3_key,
    )


@router.post("/complete-upload", response_model=DocumentResponse)
async def complete_upload(
    body: CompleteUploadRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    document = await get_user_document(db, uuid.UUID(body.document_id), user.id)

    if document.status != DocumentStatus.UPLOADED:
        raise AppError(status_code=409, message="Document upload already completed")

    document = await update_document_status(db, document, DocumentStatus.PROCESSING)

    # Dispatch Celery task
    try:
        process_document.delay(str(document.id), str(user.id))
    except Exception:
        await update_document_status(db, document, DocumentStatus.UPLOADED)
        raise AppError(status_code=503, message="Processing service unavailable. Please try again.")

    return DocumentResponse(document=DocumentOut.model_validate(document))


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    documents = await get_user_documents(db, user.id)
    return DocumentListResponse(
        documents=[DocumentOut.model_validate(doc) for doc in documents]
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    document = await get_user_document(db, document_id, user.id)
    return DocumentResponse(document=DocumentOut.model_validate(document))


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    document = await get_user_document(db, document_id, user.id)
    # Delete from S3 first (if this fails, DB record survives for retry)
    await asyncio.to_thread(delete_s3_object, document.s3_key)
    await delete_user_document(db, document_id, user.id)
    return None
