from fastapi import APIRouter

from app.api.routes import pets, login, private, users, utils, chat, food_scan_results
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(users.router)
api_router.include_router(login.router)
api_router.include_router(utils.router)
api_router.include_router(pets.router)
api_router.include_router(chat.router)
api_router.include_router(food_scan_results.router)


if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)

