from fastapi import APIRouter

from .chatbot import chatbot_router
from .webhook import webhook_router

api = APIRouter(prefix="/api")
api.include_router(chatbot_router)
api.include_router(webhook_router)
