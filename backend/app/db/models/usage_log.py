import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKey


class UsageAction(str, enum.Enum):
    EMBEDDING = "embedding"
    CHAT = "chat"
    SUMMARY = "summary"
    FLASHCARD_GENERATION = "flashcard_generation"


class UsageLog(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "usage_logs"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    action: Mapped[UsageAction] = mapped_column(Enum(UsageAction), nullable=False)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    document_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    # Relationships
    user = relationship("User", back_populates="usage_logs")
