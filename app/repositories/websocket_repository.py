from datetime import UTC, datetime
from uuid import UUID

from models.chat import Chat, Message, MessageRead
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class WebSocketRepository:
    """Репозиторий для работы с WebSocket сообщениями."""

    def __init__(self, db_session: AsyncSession) -> None:
        self.db_session = db_session

    async def get_chat(self, chat_id: int) -> Chat:
        """Получает чат по ID с данными об участниках."""
        stmt = (
            select(Chat)
            .options(selectinload(Chat.participants))
            .where(Chat.id == chat_id)
        )
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_message(
        self,
        chat_id: int,
        sender_id: int,
        text: str,
        message_id: UUID,
        ) -> Message:
        """Создает новое сообщение в базе данных."""
        message = Message(
            id=message_id,
            chat_id=chat_id,
            sender_id=sender_id,
            text=text,
            created_at=datetime.now(UTC),
        )
        self.db_session.add(message)
        await self.db_session.commit()
        await self.db_session.refresh(message)
        return message

    async def create_message_read(self, message_id: UUID, user_id: int) -> MessageRead:
        """Создает запись о прочтении сообщения."""
        message_read = MessageRead(
            message_id=message_id,
            user_id=user_id,
        )
        self.db_session.add(message_read)
        await self.db_session.commit()
        await self.db_session.refresh(message_read)
        return message_read

    async def get_message(self, message_id: UUID) -> Message:
        """Получает сообщение по ID."""
        return await self.db_session.get(Message, message_id)
