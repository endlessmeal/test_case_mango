from typing import Annotated

from core.dependencies import get_chat_service, get_current_user
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from schemas.chat import ChatCreate, ChatResponse, ChatStatusResponse, MessageResponse
from schemas.problem import ProblemDetail
from schemas.user import UserBase
from services.chat_service import ChatService

router = APIRouter(prefix="/chats", tags=["Чаты и сообщения"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Создание нового чата",
    responses={
        201: {
            "model": ChatResponse,
            "description": "Чат успешно создан.",
        },
        400: {
            "model": ProblemDetail,
            "description": "Некорректные данные.",
        },
    },
)
async def create_chat(
    chat_data: ChatCreate,
    current_user: Annotated[UserBase, Depends(get_current_user)],
    chat_service: Annotated[ChatService, Depends(get_chat_service)],
) -> ChatResponse:
    """Создает новый чат.

    Для личных чатов достаточно указать ID собеседника в participant_ids.
    Для групповых чатов необходимо указать имя чата и список ID участников.
    """
    return await chat_service.create_chat(chat_data, current_user.id)


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="Получение списка чатов пользователя",
    responses={
        200: {
            "model": list[ChatResponse],
            "description": "Список чатов пользователя.",
        },
    },
)
async def get_user_chats(
    current_user: Annotated[UserBase, Depends(get_current_user)],
    chat_service: Annotated[ChatService, Depends(get_chat_service)],
) -> list[ChatResponse]:
    """Возвращает список чатов, в которых участвует пользователь."""
    return await chat_service.get_user_chats(current_user.id)


@router.get(
    "/{chat_id}",
    status_code=status.HTTP_200_OK,
    summary="Получение информации о чате",
    responses={
        200: {
            "model": ChatResponse,
            "description": "Информация о чате.",
        },
        404: {
            "model": ProblemDetail,
            "description": "Чат не найден.",
        },
    },
)
async def get_chat(
    chat_id: Annotated[int, Path(description="ID чата", ge=1)],
    current_user: Annotated[UserBase, Depends(get_current_user)],
    chat_service: Annotated[ChatService, Depends(get_chat_service)],
) -> ChatResponse:
    """Возвращает информацию о конкретном чате."""
    chat = await chat_service.get_chat(chat_id)

    if current_user.id not in [int(p.user_id) for p in chat.participants]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет доступа к этому чату",
        )

    return chat


@router.get(
    "/{chat_id}/messages",
    status_code=status.HTTP_200_OK,
    summary="Получение сообщений из чата",
    responses={
        200: {
            "model": list[MessageResponse],
            "description": "Список сообщений чата.",
        },
        404: {
            "model": ProblemDetail,
            "description": "Чат не найден.",
        },
    },
)
async def get_chat_messages(
    chat_id: Annotated[int, Path(description="ID чата", ge=1)],
    current_user: Annotated[UserBase, Depends(get_current_user)],
    chat_service: Annotated[ChatService, Depends(get_chat_service)],
    limit: Annotated[int, Query(description="Количество сообщений", ge=1, le=100)] = 50,
    offset: Annotated[int, Query(description="Смещение", ge=0)] = 0,
) -> list[MessageResponse]:
    """Возвращает сообщения из конкретного чата с поддержкой пагинации."""
    chat = await chat_service.get_chat(chat_id)
    if current_user.id not in [int(p.user_id) for p in chat.participants]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет доступа к этому чату",
        )

    return await chat_service.get_chat_messages(chat_id, limit, offset)


@router.post(
    "/{chat_id}/participants/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Добавление пользователя в чат",
    responses={
        200: {
            "description": "Пользователь успешно добавлен в чат.",
        },
        403: {
            "model": ProblemDetail,
            "description": "Нет прав для добавления пользователя.",
        },
        404: {
            "model": ProblemDetail,
            "description": "Чат или пользователь не найден.",
        },
    },
)
async def add_user_to_chat(
    chat_id: Annotated[int, Path(description="ID чата", ge=1)],
    user_id: Annotated[int, Path(description="ID пользователя для добавления", ge=1)],
    current_user: Annotated[UserBase, Depends(get_current_user)],
    chat_service: Annotated[ChatService, Depends(get_chat_service)],
) -> ChatStatusResponse:
    """Добавляет пользователя в чат. Доступно только для групповых чатов."""
    chat = await chat_service.get_chat(chat_id)
    if current_user.id not in [int(p.user_id) for p in chat.participants]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет доступа к этому чату",
        )

    if not chat.is_group:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя добавлять участников в личный чат",
        )

    success = await chat_service.add_user_to_chat(chat_id, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Не удалось добавить пользователя",
        )

    return ChatStatusResponse(message="Пользователь успешно добавлен в чат")


@router.delete(
    "/{chat_id}/participants/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Удаление пользователя из чата",
    responses={
        200: {
            "description": "Пользователь успешно удален из чата.",
        },
        403: {
            "model": ProblemDetail,
            "description": "Нет прав для удаления пользователя.",
        },
        404: {
            "model": ProblemDetail,
            "description": "Чат или пользователь не найден.",
        },
    },
)
async def remove_user_from_chat(
    chat_id: Annotated[int, Path(description="ID чата", ge=1)],
    user_id: Annotated[int, Path(description="ID пользователя для удаления", ge=1)],
    current_user: Annotated[UserBase, Depends(get_current_user)],
    chat_service: Annotated[ChatService, Depends(get_chat_service)],
) -> ChatStatusResponse:
    """Удаляет пользователя из чата."""
    chat = await chat_service.get_chat(chat_id)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Чат не найден",
        )

    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет прав для удаления другого пользователя",
        )

    success = await chat_service.remove_user_from_chat(chat_id, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Не удалось удалить пользователя из чата",
        )

    return ChatStatusResponse(message="Пользователь успешно удален из чата")
