from endpoints import chat, health, user, websocket
from fastapi import APIRouter

routers = APIRouter()

routers.include_router(health.router)
routers.include_router(websocket.router)
routers.include_router(user.router)
routers.include_router(chat.router)
