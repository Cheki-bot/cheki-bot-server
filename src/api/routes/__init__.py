from fastapi import APIRouter

from .chatbot import chatbot_router

api = APIRouter(prefix="/api")
api.include_router(chatbot_router)
