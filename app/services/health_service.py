from repositories.health_repository import HealthRepository
from schemas.liveness import LivenessReadinessSchema, LivenessReadinessStatus
from sqlalchemy.ext.asyncio import AsyncSession


class HealthService:
    """Сервис для проверки доступности базы данных."""

    def __init__(self, db_session: AsyncSession) -> None:
        self.health_repository = HealthRepository(db_session=db_session)

    async def check_db_connection(self) -> LivenessReadinessSchema:
        """Проверяет доступность базы данных и возвращает соответствующий статус."""
        is_available = await self.health_repository.check_db_connection()
        return LivenessReadinessSchema(
            status=LivenessReadinessStatus.READY if is_available
            else LivenessReadinessStatus.ERROR,
        )

