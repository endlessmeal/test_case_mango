from models.user import User
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import exists


class UserRepository:
    """Репозиторий для работы с пользователями."""

    def __init__(self, db_session: AsyncSession) -> None:
        self.db_session = db_session

    async def create_user(self, email: str, username: str, hashed_password: str) -> User:
        """Создает нового пользователя."""
        user = User(
            email=email,
            username=username,
            hashed_password=hashed_password,
        )
        self.db_session.add(user)
        await self.db_session.commit()
        await self.db_session.refresh(user)
        return user

    async def get_user_by_id(self, user_id: int) -> User | None:
        """Получает пользователя по ID."""
        return await self.db_session.get(User, user_id)

    async def get_user_by_email(self, email: str) -> User | None:
        """Получает пользователя по email."""
        query = select(User).where(User.email == email)
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> User | None:
        """Получает пользователя по имени пользователя."""
        query = select(User).where(User.username == username)
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def get_users(self, skip: int = 0, limit: int = 100) -> list[User]:
        """Получает список пользователей с пагинацией."""
        query = select(User).offset(skip).limit(limit)
        result = await self.db_session.execute(query)
        return list(result.scalars().all())

    async def update_user(self, user_id: int, update_data: dict) -> User | None:
        """Обновляет данные пользователя."""
        query = update(User).where(User.id == user_id).values(**update_data).returning(User)
        result = await self.db_session.execute(query)
        await self.db_session.commit()
        return result.scalar_one_or_none()

    async def delete_user(self, user_id: int) -> bool:
        """Удаляет пользователя."""
        query = delete(User).where(User.id == user_id).returning(User.id)
        result = await self.db_session.execute(query)
        deleted_id = result.scalar_one_or_none()
        await self.db_session.commit()
        return deleted_id is not None

    async def email_exists(self, email: str) -> bool:
        """Проверяет, существует ли пользователь с указанным email."""
        query = select(exists().where(User.email == email))
        result = await self.db_session.execute(query)
        return result.scalar()

    async def username_exists(self, username: str) -> bool:
        """Проверяет, существует ли пользователь с указанным именем."""
        query = select(exists().where(User.username == username))
        result = await self.db_session.execute(query)
        return result.scalar()
