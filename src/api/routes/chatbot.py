from typing import Annotated

from fastapi import APIRouter, Depends, WebSocket
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.messages import AIMessage, HumanMessage
from pydantic import ValidationError

from src.api.deps import get_agent
from src.core.agent import Agent

from ..models import ApiMessage, QueryRequest

chatbot_router = APIRouter(prefix="/chatbot", tags=["Chatbot"])


@chatbot_router.get("/")
async def get_chatbot() -> ApiMessage:
    return ApiMessage(message="Welcome to the chat bot")


@chatbot_router.websocket("/ws", name="chatbot-websocket")
async def websocket_endpoint(
    websocket: WebSocket,
    agent: Annotated[Agent, Depends(get_agent)],
):
    await websocket.accept()
    try:
        data = await websocket.receive_json()
        query = QueryRequest.model_validate(data)

        messages = [
            HumanMessage(content=msg.content)
            if msg.role == "user"
            else AIMessage(content=msg.content)
            for msg in query.history
        ]

        history = InMemoryChatMessageHistory()
        await history.aadd_messages(messages)
        async for token in agent.stream(query.content, history):
            await websocket.send_text(token)
        await websocket.close()
    except ValidationError as e:
        await websocket.send_text(f"Error de validación: {e}")
        await websocket.close(code=1001)
    except Exception as e:
        await websocket.send_text(f"Error inesperado: {str(e)}")
        await websocket.close(code=1001)
