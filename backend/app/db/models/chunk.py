import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.db.base import Base, TimestampMixin, UUIDPrimaryKey

EMBEDDING_DIMENSION = 1536  # text-embedding-3-small


class Chunk(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "chunks"

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    page_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    embedding = mapped_column(Vector(EMBEDDING_DIMENSION), nullable=True)

    # Relationships
    document = relationship("Document", back_populates="chunks")
