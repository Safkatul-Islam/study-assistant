import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKey


class DocumentStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class Document(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "documents"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    file_name: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    s3_key: Mapped[str] = mapped_column(String(1000), nullable=False)
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus), default=DocumentStatus.UPLOADED, nullable=False
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary_cache: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    user = relationship("User", back_populates="documents")
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")
    chat_sessions = relationship(
        "ChatSession", back_populates="document", cascade="all, delete-orphan"
    )
    flashcards = relationship("Flashcard", back_populates="document", cascade="all, delete-orphan")
