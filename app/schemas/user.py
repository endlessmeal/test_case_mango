from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserStatus(StrEnum):
    """Статус пользователя в системе."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    BANNED = "banned"


class UserBase(BaseModel):
    """Базовая схема пользователя."""

    email: EmailStr = Field(
        description="Email пользователя",
        examples=["user@example.com"],
    )
    username: str = Field(
        description="Имя пользователя",
        examples=["johnsmith"],
        min_length=3,
        max_length=50,
    )


class UserCreate(UserBase):
    """Схема для создания пользователя."""

    password: str = Field(
        description="Пароль пользователя",
        min_length=8,
        max_length=100,
    )

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        """Проверяет, что имя пользователя состоит только из букв, цифр и знаков подчеркивания."""
        if not v.replace("_", "").isalnum():
            raise ValueError(
                "Имя пользователя должно содержать только буквы, цифры и знаки подчеркивания",
            )
        return v


class UserUpdate(BaseModel):
    """Схема для обновления пользователя."""

    email: EmailStr | None = Field(
        default=None,
        description="Email пользователя",
        examples=["user@example.com"],
    )
    username: str | None = Field(
        default=None,
        description="Имя пользователя",
        examples=["johnsmith"],
        min_length=3,
        max_length=50,
    )
    password: str | None = Field(
        default=None,
        description="Пароль пользователя",
        min_length=8,
        max_length=100,
    )
    is_active: bool | None = Field(
        default=None,
        description="Статус активности пользователя",
        examples=[True, False],
    )

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v: str | None) -> str | None:
        """Проверяет, что имя пользователя состоит только из букв, цифр и знаков подчеркивания."""
        if v is not None and not v.replace("_", "").isalnum():
            raise ValueError(
                "Имя пользователя должно содержать только буквы, цифры и знаки подчеркивания",
            )
        return v


class UserResponse(UserBase):
    """Схема ответа с информацией о пользователе."""

    id: int = Field(
        description="Уникальный идентификатор пользователя",
        examples=[1, 42, 1337],
    )
    is_active: bool = Field(
        description="Статус активности пользователя",
        examples=[True, False],
    )
    created_at: datetime = Field(
        description="Дата и время создания пользователя",
        examples=["2023-06-15T14:30:15.123Z"],
    )

    model_config = {"from_attributes": True}


class UserInDB(UserResponse):
    """Расширенная схема пользователя с хэшем пароля (для внутреннего использования)."""

    hashed_password: str = Field(
        description="Хэшированный пароль пользователя",
    )

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    """Схема для аутентификации пользователя."""

    email: EmailStr = Field(..., description="Email пользователя")
    password: str = Field(..., description="Пароль пользователя")


class TokenResponse(BaseModel):
    """Схема ответа с токенами."""

    access_token: str = Field(..., description="JWT токен доступа")
    refresh_token: str = Field(..., description="JWT токен обновления")
    token_type: str = Field(default="bearer", description="Тип токена")



class RefreshTokenRequest(BaseModel):
    """Схема для обновления токенов."""

    refresh_token: str = Field(..., description="Refresh токен для обновления")
