from core.config import Settings, get_app_settings
from endpoints.api import routers
from endpoints.websocket import router as websocket_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

settings: Settings = get_app_settings()

def create_application() -> FastAPI:
    """Создание приложения FastAPI."""
    application = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
    )

    # CORS middleware configuration
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routers with prefix
    application.include_router(routers, prefix=settings.API_V1_STR)

    # Include WebSocket router without prefix
    application.include_router(websocket_router)

    return application

app = create_application()
