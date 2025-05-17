from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession


class HealthRepository:
    """Репозиторий для проверки доступности базы данных."""

    def __init__(self, db_session: AsyncSession) -> None:
        self.db_session = db_session

    async def check_db_connection(self) -> bool:
        """Проверяет доступность базы данных."""
        try:
            await self.db_session.execute(text("SELECT 1"))
        except SQLAlchemyError:
            return False
        return True
