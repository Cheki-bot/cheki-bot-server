import uuid
from typing import TypedDict

from fastapi import APIRouter

webhook = APIRouter(prefix="/webhook", tags=["Webhook"])


class Metadata(TypedDict):
    _id: uuid.UUID
    topic: str


@webhook.post("/")
async def webhook_handler(metadata: dict):
    pass
