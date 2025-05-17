from models.chat import Chat, Message, MessageRead
from models.user import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class ChatRepository:
    """Репозиторий для работы с чатами."""

    def __init__(self, db_session: AsyncSession) -> None:
        self.db_session = db_session

    async def create_chat(
        self,
        name: str,
        *,
        is_group_chat: bool,
        participant_ids: list[int],
        ) -> Chat:
        """Создает новый чат с указанными участниками."""
        stmt = select(User).where(User.id.in_(participant_ids))
        result = await self.db_session.execute(stmt)
        users = result.scalars().all()

        chat = Chat(
            name=name,
            is_group=is_group_chat,
            participants=users,
        )

        self.db_session.add(chat)
        await self.db_session.commit()

        stmt = (
            select(Chat)
            .options(
                selectinload(Chat.participants),
                selectinload(Chat.messages),
            )
            .where(Chat.id == chat.id)
        )
        result = await self.db_session.execute(stmt)
        return result.scalar_one()

    async def get_chat(self, chat_id: int) -> Chat:
        """Получает чат по ID с данными об участниках."""
        stmt = (
            select(Chat)
            .options(
                selectinload(Chat.participants),
                selectinload(Chat.messages).selectinload(Message.read_by).selectinload(MessageRead.user),
            )
            .where(Chat.id == chat_id)
        )
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_chats(self, user_id: int) -> list[Chat]:
        """Получает список чатов, в которых участвует пользователь."""
        stmt = (
            select(Chat)
            .options(
                selectinload(Chat.participants),
                selectinload(Chat.messages).selectinload(Message.read_by).selectinload(MessageRead.user),
            )
            .join(Chat.participants)
            .where(User.id == user_id)
        )
        result = await self.db_session.execute(stmt)
        return result.scalars().all()

    async def add_user_to_chat(self, chat_id: int, user_id: int) -> bool:
        """Добавляет пользователя в чат."""
        chat = await self.get_chat(chat_id)
        if not chat:
            return False

        user = await self.db_session.get(User, user_id)
        if not user:
            return False

        if user in chat.participants:
            return True

        chat.participants.append(user)
        await self.db_session.commit()

        return True

    async def remove_user_from_chat(self, chat_id: int, user_id: int) -> bool:
        """Удаляет пользователя из чата."""
        chat = await self.get_chat(chat_id)
        if not chat:
            return False

        user = await self.db_session.get(User, user_id)
        if not user:
            return False

        if user not in chat.participants:
            return False

        chat.participants.remove(user)
        await self.db_session.commit()

        return True

    async def get_message_read_info(self, message_id: str) -> list[MessageRead]:
        """Получает информацию о прочтении сообщения."""
        stmt = (
            select(MessageRead)
            .options(selectinload(MessageRead.user))
            .where(MessageRead.message_id == message_id)
        )
        result = await self.db_session.execute(stmt)
        return result.scalars().all()

    async def get_chat_messages(
        self,
        chat_id: int,
        limit: int = 50,
        offset: int = 0,
        ) -> list[Message]:
        """Получает последние сообщения из чата."""
        stmt = (
            select(Message)
            .options(
                selectinload(Message.sender),
                selectinload(Message.read_by).selectinload(MessageRead.user),
            )
            .where(Message.chat_id == chat_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db_session.execute(stmt)
        messages = result.scalars().all()

        return list(reversed(messages))
