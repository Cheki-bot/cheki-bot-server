from fastapi import APIRouter

from .chatbot import chatbot_router

api = APIRouter(prefix="/v1")
api.include_router(chatbot_router)
