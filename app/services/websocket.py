from uuid import UUID, uuid4

from fastapi import WebSocket
from models.chat import Message, MessageRead
from repositories.websocket_repository import WebSocketRepository
from schemas.chat import (
    MessageResponse,
    WebSocketMessageRequest,
    WebSocketMessageResponse,
    WebSocketMessageType,
)
from services.chat_service import ChatService
from sqlalchemy.ext.asyncio import AsyncSession


class WebSocketService:
    """Сервис для управления WebSocket подключениями и сообщениями."""

    def __init__(self, db_session: AsyncSession) -> None:
        self.websocket_repository = WebSocketRepository(db_session)
        self.active_connections: dict[int, WebSocket] = {}
        self.user_chats: dict[int, set[int]] = {}
        self.last_message_ids: dict[int, UUID] = {}

    async def connect(self, websocket: WebSocket, user_id: int) -> None:
        """Подключает пользователя к WebSocket."""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        self.user_chats[user_id] = set()

    def disconnect(self, user_id: int) -> None:
        """Отключает пользователя от WebSocket."""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        if user_id in self.user_chats:
            del self.user_chats[user_id]

    async def add_user_to_chat(self, user_id: int, chat_id: int) -> None:
        """Добавляет пользователя в чат."""
        if user_id in self.user_chats:
            self.user_chats[user_id].add(chat_id)

    async def remove_user_from_chat(self, user_id: int, chat_id: int) -> None:
        """Удаляет пользователя из чата."""
        if user_id in self.user_chats:
            self.user_chats[user_id].discard(chat_id)

    async def broadcast_to_chat(self, chat_id: int, message: WebSocketMessageResponse) -> None:
        """Отправляет сообщение всем участникам чата."""
        for user_id, websocket in self.active_connections.items():
            if user_id in self.user_chats and chat_id in self.user_chats[user_id]:
                await websocket.send_json(message.model_dump(mode="json"))

    async def send_personal_message(self, user_id: int, message: WebSocketMessageResponse) -> None:
        """Отправляет личное сообщение конкретному пользователю."""
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(message.model_dump(mode="json"))

    async def handle_websocket_message(
        self,
        chat_id: int,
        sender_id: int,
        message: WebSocketMessageRequest,
    ) -> None:
        """Обрабатывает входящее WebSocket сообщение."""
        if not message.is_valid():
            return

        if message.type == WebSocketMessageType.MESSAGE:
            await self.handle_message(
                chat_id=chat_id,
                sender_id=sender_id,
                message_text=message.text,
            )
        elif message.type == WebSocketMessageType.READ:
            if not message.message_id:
                return
            await self.handle_read_status(
                message_id=message.message_id,
                reader_id=sender_id,
            )

    async def handle_message(
        self,
        chat_id: int,
        sender_id: int,
        message_text: str,
    ) -> Message | None:
        """Обрабатывает новое сообщение."""
        message_id = uuid4()

        if chat_id in self.last_message_ids and self.last_message_ids[chat_id] == message_id:
            return None

        message = await self.websocket_repository.create_message(
            chat_id=chat_id,
            sender_id=sender_id,
            text=message_text,
            message_id=message_id,
        )

        self.last_message_ids[chat_id] = message_id

        await self.broadcast_to_chat(chat_id, WebSocketMessageResponse(
            type=WebSocketMessageType.MESSAGE,
            data=MessageResponse(
                id=message.id,
                chat_id=message.chat_id,
                sender_id=message.sender_id,
                text=message.text,
                created_at=message.created_at,
                read_by=[],
            ).model_dump(mode="json"),
        ))

        return message

    async def handle_read_status(self, message_id: UUID, reader_id: int) -> MessageRead:
        """Обрабатывает статус прочтения сообщения."""
        # Создаем запись о прочтении через репозиторий
        message_read = await self.websocket_repository.create_message_read(
            message_id=message_id,
            user_id=reader_id,
        )

        # Получаем информацию о сообщении
        message = await self.websocket_repository.get_message(message_id)
        if message:
            # Отправляем уведомление отправителю
            await self.send_personal_message(message.sender_id, WebSocketMessageResponse(
                type=WebSocketMessageType.READ,
                data={
                    "message_id": str(message_id),
                    "reader_id": reader_id,
                    "read_at": message_read.read_at.isoformat(),
                },
            ))

        return message_read

    async def validate_chat_access(
        self,
        chat_id: int,
        user_id: int,
        chat_service: ChatService,
        ) -> bool:
        """Проверяет доступ пользователя к чату."""
        chat = await chat_service.get_chat(chat_id)
        if not chat:
            return False

        return user_id in [p.user_id for p in chat.participants]
