from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import Mapped, relationship

from .base import Base

if TYPE_CHECKING:
    from models.chat import Chat, Message, MessageRead


class User(Base):
    """Модель пользователя."""

    __tablename__ = "users"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    email: Mapped[str] = Column(String, unique=True, index=True, nullable=False)
    username: Mapped[str] = Column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = Column(String, nullable=False)
    is_active: Mapped[bool] = Column(Boolean, default=True)
    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC),
    )

    messages: Mapped[list["Message"]] = relationship("Message", back_populates="sender")
    chats: Mapped[list["Chat"]] = relationship(
        "Chat", secondary="chat_participants", back_populates="participants",
    )
    read_messages: Mapped[list["MessageRead"]] = relationship("MessageRead", back_populates="user")
