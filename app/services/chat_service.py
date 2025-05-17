from fastapi import HTTPException, status
from models.chat import Chat
from repositories.chat_repository import ChatRepository
from schemas.chat import ChatCreate, ChatParticipant, ChatResponse, MessageResponse
from sqlalchemy.ext.asyncio import AsyncSession


class ChatService:
    """Сервис для работы с чатами."""

    def __init__(self, db_session: AsyncSession) -> None:
        self.chat_repository = ChatRepository(db_session)

    async def create_chat(self, data: ChatCreate, creator_id: int) -> ChatResponse:
        """Создает новый чат."""
        if creator_id not in data.participant_ids:
            data.participant_ids.append(creator_id)

        chat = await self.chat_repository.create_chat(
            name=data.name,
            is_group=data.is_group,
            participant_ids=data.participant_ids,
        )

        return self._prepare_chat_response(chat)

    async def get_chat(self, chat_id: int) -> ChatResponse:
        """Получает информацию о чате."""
        chat = await self.chat_repository.get_chat(chat_id)
        if not chat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Чат не найден",
            )

        return self._prepare_chat_response(chat)

    async def get_user_chats(self, user_id: int) -> list[ChatResponse]:
        """Получает список чатов, в которых участвует пользователь."""
        chats = await self.chat_repository.get_user_chats(user_id)
        return [self._prepare_chat_response(chat) for chat in chats]

    async def add_user_to_chat(self, chat_id: int, user_id: int) -> bool:
        """Добавляет пользователя в чат."""
        return await self.chat_repository.add_user_to_chat(chat_id, user_id)

    async def remove_user_from_chat(self, chat_id: int, user_id: int) -> bool:
        """Удаляет пользователя из чата."""
        return await self.chat_repository.remove_user_from_chat(chat_id, user_id)

    def _prepare_message_response(self, message) -> MessageResponse:  # noqa: ANN001
        """Подготавливает данные сообщения для ответа."""
        return MessageResponse(
            id=str(message.id),
            chat_id=str(message.chat_id),
            sender_id=str(message.sender_id),
            text=message.text,
            created_at=message.created_at,
            read_by=[
                {
                    "user_id": str(read.user.id),
                    "username": read.user.username,
                    "read_at": read.read_at,
                }
                for read in message.read_by
            ],
        )

    async def get_chat_messages(
        self,
        chat_id: int,
        limit: int = 50,
        offset: int = 0,
        ) -> list[MessageResponse]:
        """Получает сообщения из чата."""
        chat = await self.chat_repository.get_chat(chat_id)
        if not chat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Чат не найден",
            )

        messages = await self.chat_repository.get_chat_messages(
            chat_id=chat_id,
            limit=limit,
            offset=offset,
        )
        return [self._prepare_message_response(message) for message in messages]

    def _prepare_chat_response(self, chat: Chat) -> ChatResponse:
        """Подготавливает данные чата для ответа."""
        participants = [
            ChatParticipant(
                user_id=str(user.id),
                username=user.username,
            )
            for user in chat.participants
        ]

        last_message = None
        if chat.messages and len(chat.messages) > 0:
            latest_message = max(chat.messages, key=lambda m: m.created_at)
            last_message = self._prepare_message_response(latest_message)

        return ChatResponse(
            id=str(chat.id),
            name=chat.name,
            is_group=chat.is_group,
            created_at=chat.created_at,
            participants=participants,
            last_message=last_message,
        )
