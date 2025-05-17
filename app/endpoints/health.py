from typing import Annotated

from core.dependencies import get_health_service
from fastapi import APIRouter, Depends, status
from schemas.liveness import LivenessReadinessSchema, LivenessReadinessStatus
from schemas.problem import ProblemDetail
from sqlalchemy.orm import Session

router = APIRouter(prefix="/health", tags=["Доступность и читаемость"])


@router.get(
    "/liveness",
    status_code=status.HTTP_200_OK,
    summary="Проверка доступности приложения",
    responses={
        200: {
            "model": LivenessReadinessSchema,
            "description": "Приложение доступно и работает.",
        },
        500: {"description": "Внутренняя ошибка сервера.", "model": ProblemDetail},
    },
)
async def liveness() -> LivenessReadinessSchema:
    """Эндпоинт для проверки на доступность приложения."""
    return LivenessReadinessSchema(status=LivenessReadinessStatus.ALIVE)


@router.get(
    "/readiness",
    status_code=status.HTTP_200_OK,
    summary="Проверка доступности базы данных на чтение.",
    responses={
        200: {
            "model": LivenessReadinessSchema,
            "description": "Статус доступности к базе данных.",
        },
        500: {"description": "Внутренняя ошибка сервера.", "model": ProblemDetail},
    },
)
async def readiness(
    health_service: Annotated[Session, Depends(get_health_service)],
) -> LivenessReadinessSchema:
    """Эндпоинт для проверки на читаемость из базы данных."""
    return await health_service.check_db_connection()
