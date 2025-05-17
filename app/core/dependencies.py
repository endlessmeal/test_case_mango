from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Annotated

from core.config import Settings, get_app_settings
from fastapi import Depends, HTTPException, Request, WebSocket, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from pydantic import ValidationError
from schemas.user import TokenPayloadSchema, UserBase
from services.chat_service import ChatService
from services.health_service import HealthService
from services.user_service import UserService
from services.websocket import WebSocketService
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

oauth_scheme = OAuth2PasswordBearer(tokenUrl="token")

app_settings: Settings = get_app_settings()

pg_connection_string = (
    f"postgresql+asyncpg://{app_settings.POSTGRES_USER}:{app_settings.POSTGRES_PASSWORD}@"
    f"{app_settings.POSTGRES_HOST}:{app_settings.POSTGRES_PORT}/{app_settings.POSTGRES_DB}"
)

async_engine = create_async_engine(
    pg_connection_string,
    pool_pre_ping=True,
    pool_size=app_settings.POOL_SIZE,
)

async_session = async_sessionmaker(
    async_engine, expire_on_commit=False, class_=AsyncSession, autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Зависимость для получения сессии с базой данных."""
    db = async_session()
    try:
        yield db
    finally:
        await db.close()


async def get_health_service(db: Annotated[AsyncSession, Depends(get_db)]) -> HealthService:
    """Возвращает экземпляр HealthService."""
    return HealthService(db_session=db)


def get_websocket_service(db: Annotated[AsyncSession, Depends(get_db)]) -> WebSocketService:
    """Возвращает экземпляр WebSocket."""
    return WebSocketService(db)


async def get_user_service(db: Annotated[AsyncSession, Depends(get_db)]) -> UserService:
    """Возвращает экземпляр сервиса для работы с пользователями."""
    return UserService(db_session=db)


async def get_chat_service(db: Annotated[AsyncSession, Depends(get_db)]) -> ChatService:
    """Возвращает экземпляр сервиса для работы с чатами."""
    return ChatService(db_session=db)


async def get_current_user(
    request: Request,
    token: Annotated[str, Depends(oauth_scheme)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserBase:
    """Зависимость для получения текущего пользователя из HTTP запроса."""
    is_refresh_endpoint = request.url.path == "/api/v1/users/refresh"

    secret_key = (
        app_settings.REFRESH_SECRET_KEY if is_refresh_endpoint else app_settings.SECRET_KEY
    )
    try:
        payload = jwt.decode(
            token, secret_key, algorithms=[app_settings.ALGORITHM],
        )
        token_data = TokenPayloadSchema(**payload)

        # Если это не /refresh и токен не является access-токеном, выбрасываем ошибку
        if not is_refresh_endpoint and secret_key == app_settings.REFRESH_SECRET_KEY:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Если это /refresh и токен не является refresh-токеном
        if is_refresh_endpoint and secret_key == app_settings.SECRET_KEY:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type for refresh",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if datetime.fromtimestamp(token_data.exp, tz=UTC) < datetime.now(UTC):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except (jwt.JWTError, ValidationError) as err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from err

    user: UserBase = await user_service.get_user_by_email(email=token_data.sub)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Could not find user",
        )

    return user


async def get_current_user_ws(
    websocket: WebSocket,
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserBase:
    """Зависимость для получения текущего пользователя из WebSocket соединения."""
    token = websocket.query_params.get("token")

    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )

    try:
        payload = jwt.decode(
            token, app_settings.SECRET_KEY, algorithms=[app_settings.ALGORITHM],
        )
        token_data = TokenPayloadSchema(**payload)

        if datetime.fromtimestamp(token_data.exp, tz=UTC) < datetime.now(UTC):
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
            )
    except (jwt.JWTError, ValidationError) as err:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        ) from err

    user: UserBase = await user_service.get_user_by_email(email=token_data.sub)

    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Could not find user",
        )

    return user
