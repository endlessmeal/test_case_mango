from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Table
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, relationship

from .base import Base

if TYPE_CHECKING:
    from models.user import User

chat_participants = Table(
    "chat_participants",
    Base.metadata,
    Column("chat_id", Integer, ForeignKey("chats.id"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
)

class Chat(Base):
    """Модель чата."""

    __tablename__ = "chats"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    name: Mapped[str] = Column(String, nullable=True)
    is_group: Mapped[bool] = Column(Boolean, default=False)
    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC),
        )

    messages: Mapped[list["Message"]] = relationship(
        "Message", back_populates="chat", cascade="all, delete-orphan",
        )
    participants: Mapped[list["User"]] = relationship(
        "User", secondary=chat_participants, back_populates="chats",
    )

class Message(Base):
    """Модель сообщения."""

    __tablename__ = "messages"

    id: Mapped[UUID] = Column(PG_UUID, primary_key=True, default=lambda: str(uuid4()))
    chat_id: Mapped[int] = Column(Integer, ForeignKey("chats.id", ondelete="CASCADE"))
    sender_id: Mapped[int] = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    text: Mapped[str] = Column(String)
    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC),
        )

    chat: Mapped["Chat"] = relationship("Chat", back_populates="messages")
    sender: Mapped["User"] = relationship("User", back_populates="messages")
    read_by: Mapped[list["MessageRead"]] = relationship(
        "MessageRead", back_populates="message", cascade="all, delete-orphan",
        )

class MessageRead(Base):
    """Модель для отслеживания прочитанных сообщений."""

    __tablename__ = "message_reads"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    message_id: Mapped[UUID] = Column(PG_UUID, ForeignKey("messages.id", ondelete="CASCADE"))
    user_id: Mapped[int] = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    read_at: Mapped[datetime] = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    message: Mapped["Message"] = relationship("Message", back_populates="read_by")
    user: Mapped["User"] = relationship("User", back_populates="read_messages")
