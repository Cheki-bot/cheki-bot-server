import os
import re
import json
import traceback
import requests
from telegram import Bot
from json import JSONDecodeError
from typing import Annotated, Any, Dict

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
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

def clear_markdown_whatsapp(texto: str) -> str:
    texto = re.sub(r'\*\*(.*?)\*\*', r'*\1*', texto)
    texto = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'_\1_', texto)
    texto = re.sub(r'#+\s+(.*)', r'*\1*', texto)
    texto = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\2', texto)
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
       
def send_whatsapp_message(to: str, message: str):
    token = os.getenv("WHATSAPP_TOKEN")
    phone_number_id = os.getenv("WHATSAPP_PHONE_ID")
    if not token or not phone_number_id:
        print("ERROR: WhatsApp environment variables not set.")
        return

    url = f"https://graph.facebook.com/v23.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {"messaging_product": "whatsapp", "to": to, "text": {"body": message}}
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error sending WhatsApp message: {e}")
        return None

@chatbot_router.get("/webhook/whatsapp")
async def verify_whatsapp_webhook(request: Request):
    verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN")
    params = request.query_params
    if (
        params.get("hub.mode") == "subscribe"
        and params.get("hub.verify_token") == verify_token
    ):
        challenge = params.get("hub.challenge")
        if challenge:
            return int(challenge)
    raise HTTPException(status_code=403, detail="Verification failed")


@chatbot_router.post("/webhook/whatsapp")
async def whatsapp_webhook(
    request: Request,
    agent: Annotated[Agent, Depends(get_agent)],
):
    try:
        data = await request.json()

        changes = data.get("entry", [{}])[0].get("changes", [{}])[0]
        if (
            "value" not in changes
            or "messages" not in changes["value"]
            or not changes["value"]["messages"]
        ):
            return {"status": "ok", "detail": "No message found"}

        message = changes["value"]["messages"][0]
        sender = message["from"]
        text = message.get("text", {}).get("body")

        if not text:
            return {"status": "ok", "detail": "Empty text message"}

        response_de_la_ia = await agent.invoke(text, [])
        texto_para_whatsapp = clear_markdown_whatsapp(response_de_la_ia)
        send_whatsapp_message(sender, texto_para_whatsapp)

        return {"status": "success"}

    except Exception as e:
        print(f"Error processing WhatsApp message: {e}")
        traceback.print_exc()
        return {"status": "error"}