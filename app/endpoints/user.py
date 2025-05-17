from typing import Annotated

from core.dependencies import get_current_user, get_user_service
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from schemas.problem import ProblemDetail
from schemas.user import (
    LoginRequest,
    TokenResponse,
    UserBase,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Пользователи"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Создание нового пользователя",
    responses={
        201: {
            "model": UserResponse,
            "description": "Пользователь успешно создан.",
        },
        400: {
            "model": ProblemDetail,
            "description": "Некорректные данные или пользователь с такими данными уже существует.",
        },
    },
)
async def create_user(
    user_data: UserCreate,
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserResponse:
    """Создает нового пользователя в системе.

    Требуется email, имя пользователя и пароль. Email и имя пользователя должны быть уникальными.
    """
    if await user_service.if_email_exists(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже существует",
        )
    if await user_service.if_username_exists(user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким именем уже существует",
        )
    return await user_service.create_user(user_data)


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="Получение списка пользователей",
    responses={
        200: {
            "model": list[UserResponse],
            "description": "Список пользователей.",
        },
    },
)
async def get_users(
    user_service: Annotated[UserService, Depends(get_user_service)],
    skip: Annotated[int, Query(description="Количество записей для пропуска", ge=0)] = 0,
    limit: Annotated[int, Query(
        description="Максимальное количество записей", ge=1, le=100)] = 100,
) -> list[UserResponse]:
    """Возвращает список пользователей с возможностью пагинации."""
    return await user_service.get_users(skip=skip, limit=limit)


@router.get(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Получение пользователя по ID",
    responses={
        200: {
            "model": UserResponse,
            "description": "Данные пользователя.",
        },
        404: {
            "model": ProblemDetail,
            "description": "Пользователь не найден.",
        },
    },
)
async def get_user(
    user_id: Annotated[int, Path(description="ID пользователя", ge=1)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserResponse:
    """Возвращает данные пользователя по его ID."""
    return await user_service.get_user(user_id)


@router.put(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Обновление данных пользователя",
    responses={
        200: {
            "model": UserResponse,
            "description": "Обновленные данные пользователя.",
        },
        400: {
            "model": ProblemDetail,
            "description": "Некорректные данные или пользователь с такими данными уже существует.",
        },
        404: {
            "model": ProblemDetail,
            "description": "Пользователь не найден.",
        },
    },
)
async def update_user(
    user_id: Annotated[int, Path(description="ID пользователя", ge=1)],
    user_data: UserUpdate,
    user_service: Annotated[UserService, Depends(get_user_service)],
    current_user: Annotated[UserBase, Depends(get_current_user)],
) -> UserResponse:
    """Обновляет данные пользователя.

    Можно обновить email, имя пользователя, пароль или статус активности.
    """
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет прав для обновления данных другого пользователя",
        )

    user = await user_service.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )
    return await user_service.update_user(user_id, user_data)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаление пользователя",
    responses={
        204: {
            "description": "Пользователь успешно удален.",
        },
        404: {
            "model": ProblemDetail,
            "description": "Пользователь не найден.",
        },
    },
)
async def delete_user(
    user_id: Annotated[int, Path(description="ID пользователя", ge=1)],
    user_service: Annotated[UserService, Depends(get_user_service)],
    current_user: Annotated[UserBase, Depends(get_current_user)],
) -> None:
    """Удаляет пользователя из системы.

    Доступно только для самого пользователя или администратора.
    """
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет прав для удаления другого пользователя",
        )

    user = await user_service.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )
    await user_service.delete_user(user_id)


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    summary="Вход в систему",
    responses={
        200: {
            "model": TokenResponse,
            "description": "Успешная аутентификация с токенами.",
        },
        401: {
            "model": ProblemDetail,
            "description": "Неверные учетные данные.",
        },
    },
)
async def login(
    login_data: LoginRequest,
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> TokenResponse:
    """Аутентифицирует пользователя и выдает токены доступа."""
    user = await user_service.authenticate_user(login_data.email, login_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return await user_service.generate_tokens(user.email)


@router.post(
    "/refresh",
    status_code=status.HTTP_200_OK,
    summary="Обновление токенов",
    responses={
        200: {
            "model": TokenResponse,
            "description": "Новая пара токенов.",
        },
        401: {
            "model": ProblemDetail,
            "description": "Неверный refresh токен.",
        },
    },
)
async def refresh_tokens(
    current_user: Annotated[UserBase, Depends(get_current_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> TokenResponse:
    """Обновляет пару access/refresh токенов используя refresh токен."""
    return await user_service.generate_tokens(current_user.email)
