from fastapi import APIRouter

from .chatbot import chatbot_router
from .auth import router as auth_router

api = APIRouter(prefix="/api")
api.include_router(auth_router)
api.include_router(chatbot_router)