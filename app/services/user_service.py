from datetime import UTC, datetime, timedelta

from core.config import get_app_settings, get_pwd_context
from fastapi import HTTPException, status
from jose import jwt
from repositories.user_repository import UserRepository
from schemas.user import (
    TokenResponse,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from sqlalchemy.ext.asyncio import AsyncSession

pwd_context = get_pwd_context()
settings = get_app_settings()


class UserService:
    """Сервис для работы с пользователями."""

    def __init__(self, db_session: AsyncSession) -> None:
        self.user_repository = UserRepository(db_session)

    def hash_password(self, password: str) -> str:
        """Хеширует пароль."""
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Проверяет правильность пароля."""
        return pwd_context.verify(plain_password, hashed_password)

    async def create_user(self, user_data: UserCreate) -> UserResponse:
        """Создает нового пользователя."""
        hashed_password = self.hash_password(user_data.password)
        user = await self.user_repository.create_user(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
        )
        return UserResponse.model_validate(user)

    async def get_user(self, user_id: int) -> UserResponse:
        """Получает пользователя по ID."""
        user = await self.user_repository.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден",
            )

        return UserResponse.model_validate(user)

    async def get_user_by_email(self, email: str) -> UserResponse | None:
        """Получает пользователя по email."""
        user = await self.user_repository.get_user_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден",
            )

        return UserResponse.model_validate(user) if user else None

    async def get_users(self, skip: int = 0, limit: int = 100) -> list[UserResponse]:
        """Получает список пользователей с пагинацией."""
        users = await self.user_repository.get_users(skip, limit)
        return [UserResponse.model_validate(user) for user in users]

    async def if_email_exists(self, email: str) -> bool:
        """Проверяет, существует ли пользователь с таким email."""
        return await self.user_repository.email_exists(email)

    async def if_username_exists(self, username: str) -> bool:
        """Проверяет, существует ли пользователь с таким именем."""
        return await self.user_repository.username_exists(username)

    async def update_user(self, user_id: int, user_data: UserUpdate) -> UserResponse:
        """Обновляет данные пользователя."""
        update_data = user_data.model_dump(exclude_unset=True)

        if user_data.password:
            update_data["hashed_password"] = self.hash_password(user_data.password)
            update_data.pop("password", None)

        updated_user = await self.user_repository.update_user(user_id, update_data)

        return UserResponse.model_validate(updated_user)

    async def delete_user(self, user_id: int) -> bool:
        """Удаляет пользователя."""
        return await self.user_repository.delete_user(user_id)

    async def authenticate_user(self, email: str, password: str) -> UserResponse:
        """Аутентифицирует пользователя по email и паролю."""
        user = await self.user_repository.get_user_by_email(email)
        if not user:
            return None

        if not self.verify_password(password, user.hashed_password):
            return None

        return UserResponse.model_validate(user)

    def create_access_token(self, email: str) -> str:
        """Создает JWT access токен."""
        expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        payload = {
            "sub": email,
            "exp": expire,
            "type": "access",
        }

        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    def create_refresh_token(self, email: str) -> str:
        """Создает JWT refresh токен."""
        expire = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        payload = {
            "sub": email,
            "exp": expire,
            "type": "refresh",
        }

        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    async def generate_tokens(self, email: str) -> TokenResponse:
        """Генерирует пару токенов access и refresh."""
        access_token = self.create_access_token(email)
        refresh_token = self.create_refresh_token(email)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )
