import json
from json import JSONDecodeError
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    WebSocket,
    WebSocketDisconnect,
)
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.messages import AIMessage, HumanMessage
from pydantic import ValidationError

from src.api.deps import get_agent
from src.core.agent import Agent

from ..models import QueryRequest

chatbot_router = APIRouter(prefix="/chatbot", tags=["Chatbot"])


@chatbot_router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    agent: Annotated[Agent, Depends(get_agent)],
):
    """
    Handles WebSocket connections for real-time chatbot interaction.

    Args:
        websocket (WebSocket): The WebSocket connection.
        agent (Agent): The chatbot agent dependency.

    Raises:
        ValidationError: If the received data is not valid.
        JSONDecodeError: If the received data is not valid JSON.
        WebSocketDisconnect: If the WebSocket connection is disconnected.
        Exception: For any unexpected errors.
    """
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
        await websocket.send_text(f"ERROR de validación: {json.dumps(e.json())}")
        await websocket.close(code=1008)

    except JSONDecodeError as e:
        await websocket.send_text(f"ERROR de decodificación JSON: {e}")
        await websocket.close(code=1003)

    except WebSocketDisconnect:
        await websocket.close()

    except Exception as e:
        await websocket.send_text(f"ERROR inesperado: {str(e)}")
        await websocket.close(code=1011)
