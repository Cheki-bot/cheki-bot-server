import os
import re
import json
import traceback
from telegram import Bot
from json import JSONDecodeError
from typing import Annotated, Any, Dict

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
)
from langchain_core.messages import AIMessage, HumanMessage
from pydantic import ValidationError

from src.api.deps import get_agent
from src.api.models import QueryRequest
from src.core.agent import Agent

def limpiar_markdown(texto: str) -> str:
    texto = re.sub(r'(\*\*|__|\*|_)', '', texto)
    texto = re.sub(r'#+\s', '', texto)
    texto = re.sub(r'^\s*[\*\-]\s*|\d+\.\s*', '', texto, flags=re.MULTILINE)
    texto = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', texto)
    return texto.strip()


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

        async for token in agent.stream(query.content, messages):
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


@chatbot_router.post("/webhook")
async def telegram_webhook(
    update: Dict[str, Any],
    agent: Annotated[Agent, Depends(get_agent)],
):
    try:
        if not update or "message" not in update or "chat" not in update["message"]:
            return {"status": "ok", "detail": "Update no válido o sin mensaje."}

        message = update["message"]
        chat_id = message["chat"]["id"]
        text = message.get("text", "")

        if not text:
            return {"status": "ok", "detail": "Mensaje de texto vacío."}

        response_de_la_ia = await agent.invoke(text, [])

        texto_para_telegram = limpiar_markdown(response_de_la_ia)

        TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
        if TELEGRAM_TOKEN:
            bot = Bot(token=TELEGRAM_TOKEN)
            await bot.send_message(chat_id=chat_id, text=texto_para_telegram)
        else:
            print("ERROR: TELEGRAM_TOKEN no está configurado.")

        return {"status": "success"}

    except Exception as e:
        print("error")
        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail=f"Error processing message: {str(e)}"
        )
