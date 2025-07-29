from typing import Literal

from openai import BaseModel
from pydantic import Field


class ApiMessage(BaseModel):
    message: str = Field(
        ..., description="The content of the message", examples=["Hello, how are you?"]
    )


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class QueryRequest(BaseModel):
    content: str
    history: list[ChatMessage]
