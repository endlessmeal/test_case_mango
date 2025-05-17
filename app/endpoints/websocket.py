from typing import Annotated

from core.dependencies import get_chat_service, get_current_user_ws, get_websocket_service
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from pydantic import ValidationError
from schemas.chat import WebSocketMessageRequest
from schemas.user import UserBase
from services.chat_service import ChatService
from services.websocket import WebSocketService

router = APIRouter()

@router.websocket("/ws/{chat_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    chat_id: int,
    websocket_service: Annotated[WebSocketService, Depends(get_websocket_service)],
    current_user: Annotated[UserBase, Depends(get_current_user_ws)],
    chat_service: Annotated[ChatService, Depends(get_chat_service)],
) -> None:
    """WebSocket эндпоинт для подключения к чату.

    Позволяет пользователям обмениваться сообщениями в реальном времени и получать
    уведомления о прочтении сообщений. Поддерживает личные и групповые чаты.

    - Для отправки сообщения: `{"type": "message", "text": "Текст сообщения"}`
    - Для отметки сообщения прочитанным: `{"type": "read", "message_id": "uuid"}`

    Возможные ответы:
    - 200: Формат сообщений, отправляемых через WebSocket.
    - 403: Нет доступа к чату.
    """
    # Проверяем доступ пользователя к чату
    if not await websocket_service.validate_chat_access(chat_id, current_user.id, chat_service):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Подключаем пользователя к чату
    await websocket_service.connect(websocket, current_user.id)
    await websocket_service.add_user_to_chat(current_user.id, chat_id)

    try:
        while True:
            # Получаем сообщение от клиента
            data = await websocket.receive_json()
            message = WebSocketMessageRequest(**data)

            # Обрабатываем сообщение
            await websocket_service.handle_websocket_message(
                chat_id=chat_id,
                sender_id=current_user.id,
                message=message,
            )

    except WebSocketDisconnect:
        websocket_service.disconnect(current_user.id)
        await websocket_service.remove_user_from_chat(current_user.id, chat_id)
    except ValidationError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
