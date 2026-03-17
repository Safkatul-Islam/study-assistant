import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.db.models.document import Document, DocumentStatus


async def create_document(
    db: AsyncSession,
    user_id: uuid.UUID,
    title: str,
    file_name: str,
    file_size: int,
    s3_key: str,
    doc_id: uuid.UUID,
) -> Document:
    document = Document(
        id=doc_id,
        user_id=user_id,
        title=title,
        file_name=file_name,
        file_size=file_size,
        s3_key=s3_key,
        status=DocumentStatus.UPLOADED,
    )
    db.add(document)
    await db.flush()
    return document


async def get_user_documents(db: AsyncSession, user_id: uuid.UUID) -> list[Document]:
    result = await db.execute(
        select(Document)
        .where(Document.user_id == user_id)
        .order_by(Document.created_at.desc())
    )
    return list(result.scalars().all())


async def get_user_document(
    db: AsyncSession, document_id: uuid.UUID, user_id: uuid.UUID
) -> Document:
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.user_id == user_id)
    )
    document = result.scalar_one_or_none()
    if not document:
        raise NotFoundError("Document")
    return document


async def update_document_status(
    db: AsyncSession, document: Document, status: DocumentStatus
) -> Document:
    document.status = status
    await db.flush()
    return document


async def delete_user_document(
    db: AsyncSession, document_id: uuid.UUID, user_id: uuid.UUID
) -> Document:
    document = await get_user_document(db, document_id, user_id)
    db.delete(document)
    await db.flush()
    return document
