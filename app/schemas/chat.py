from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class ChatType(StrEnum):
    """Тип чата: личный или групповой."""

    PERSONAL = "personal"
    GROUP = "group"


class WebSocketMessageType(StrEnum):
    """Типы сообщений WebSocket."""

    MESSAGE = "message"
    READ = "read"


class WebSocketMessageBase(BaseModel):
    """Базовая схема для WebSocket сообщений."""

    type: WebSocketMessageType = Field(
        description="Тип сообщения",
        examples=["message", "read"],
    )


class WebSocketMessageRequest(WebSocketMessageBase):
    """Схема для входящих WebSocket сообщений."""

    text: str | None = Field(
        default=None,
        description="Текст сообщения",
        examples=["Привет, как дела?"],
    )
    message_id: UUID | None = Field(
        default=None,
        description="ID сообщения (требуется только для отметки о прочтении)",
        examples=["123e4567-e89b-12d3-a456-426614174000"],
    )

    def is_valid(self) -> bool:
        """Проверяет валидность сообщения в зависимости от его типа."""
        if self.type == WebSocketMessageType.MESSAGE:
            return bool(self.text)
        if self.type == WebSocketMessageType.READ:
            return bool(self.message_id)
        return False


class WebSocketMessageResponse(WebSocketMessageBase):
    """Схема для исходящих WebSocket сообщений."""

    data: dict = Field(
        description="Данные сообщения",
    )

class ChatStatusResponse(BaseModel):
    """Базовая схема для чата."""

    message: str = Field(
        description="Сообщение о статусе.",
        examples=["Пользователь успешно добавлен в чат"],
    )


class ChatBase(BaseModel):
    """Базовая схема для чата."""

    name: str | None = Field(
        default=None,
        description="Название чата, может быть пустым для личных чатов",
        examples=["Рабочий чат", "Друзья"],
    )
    is_group: bool = Field(
        default=False,
        description="Флаг, указывающий, является ли чат групповым",
        examples=[True, False],
    )


class ChatCreate(ChatBase):
    """Схема для создания нового чата."""

    participant_ids: list[int] = Field(
        description="Список ID участников чата",
        examples=[1, 2, 3],
    )


class ChatParticipant(BaseModel):
    """Схема участника чата."""

    user_id: int = Field(
        description="ID пользователя",
        examples=[1],
    )
    username: str = Field(
        description="Имя пользователя",
        examples=["user123"],
    )


class MessageBase(BaseModel):
    """Базовая схема сообщения."""

    text: str = Field(
        description="Текст сообщения",
        examples=["Привет, как дела?"],
    )


class MessageCreate(MessageBase):
    """Схема для создания нового сообщения."""

    chat_id: int = Field(
        description="ID чата, в который отправляется сообщение",
        examples=[1],
    )


class MessageReadStatus(BaseModel):
    """Схема статуса прочтения сообщения."""

    user_id: int = Field(
        description="ID пользователя, прочитавшего сообщение",
        examples=[1],
    )
    username: str = Field(
        description="Имя пользователя",
        examples=["user123"],
    )
    read_at: datetime = Field(
        description="Дата и время прочтения сообщения",
        examples=["2023-06-15T14:30:15.123Z"],
    )


class MessageResponse(MessageBase):
    """Схема ответа с информацией о сообщении."""

    id: UUID = Field(
        description="Уникальный идентификатор сообщения",
        examples=["123e4567-e89b-12d3-a456-426614174000"],
    )
    chat_id: int = Field(
        description="ID чата, к которому относится сообщение",
        examples=[1],
    )
    sender_id: int = Field(
        description="ID отправителя сообщения",
        examples=[1],
    )
    created_at: datetime = Field(
        description="Дата и время создания сообщения",
        examples=["2023-06-15T14:30:15.123Z"],
    )
    read_by: list[MessageReadStatus] = Field(
        description="Список пользователей, прочитавших сообщение",
        default_factory=list,
    )

    model_config = {"from_attributes": True}


class ChatResponse(ChatBase):
    """Схема ответа с информацией о чате."""

    id: int = Field(
        description="Уникальный идентификатор чата",
        examples=[1],
    )
    created_at: datetime = Field(
        description="Дата и время создания чата",
        examples=["2023-06-15T14:30:15.123Z"],
    )
    participants: list[ChatParticipant] = Field(
        description="Список участников чата",
    )
    last_message: MessageResponse | None = Field(
        default=None,
        description="Последнее сообщение в чате",
    )

    model_config = {"from_attributes": True}
