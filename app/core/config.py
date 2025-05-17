import os
from functools import lru_cache

from passlib.context import CryptContext
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Конфигурация приложения."""

    PROJECT_NAME: str = "Messenger"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    POSTGRES_HOST: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = "messenger"
    POSTGRES_PORT: int = 5432
    POOL_SIZE: int = 20
    SQLALCHEMY_DATABASE_URI: str | None = None

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "access_secret_key")
    REFRESH_SECRET_KEY: str = os.getenv("REFRESH_SECRET_KEY", "refresh_secret_key")

    model_config = SettingsConfigDict(env_file=os.getenv("ENV_FILE", ".env"))

@lru_cache
def get_app_settings() -> Settings:
    """Retrieve the application settings.

    Returns
    -------
        Settings: The application settings.

    """
    return Settings()


def get_settings_no_cache() -> Settings:
    """Получение настроек без кеша."""
    return Settings()

def get_pwd_context() -> CryptContext:
    """Получение контекста хеширования паролей."""
    return CryptContext(schemes=["bcrypt"], deprecated="auto")
