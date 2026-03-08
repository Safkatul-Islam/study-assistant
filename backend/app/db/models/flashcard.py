import enum
import uuid

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKey


class FlashcardDifficulty(str, enum.Enum):
    UNRATED = "unrated"
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class Flashcard(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "flashcards"

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
    front: Mapped[str] = mapped_column(Text, nullable=False)
    back: Mapped[str] = mapped_column(Text, nullable=False)
    source_chunk_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    difficulty: Mapped[FlashcardDifficulty] = mapped_column(
        Enum(FlashcardDifficulty), default=FlashcardDifficulty.UNRATED, nullable=False
    )

    # Relationships
    document = relationship("Document", back_populates="flashcards")
