import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKey


class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"


class ChatSession(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "chat_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(500), default="New Chat", nullable=False)

    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    document = relationship("Document", back_populates="chat_sessions")
    messages = relationship(
        "ChatMessage", back_populates="session", cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
    )


class ChatMessage(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "chat_messages"

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[MessageRole] = mapped_column(Enum(MessageRole), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    citations: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON string of chunk refs
    token_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    session = relationship("ChatSession", back_populates="messages")
