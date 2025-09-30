from typing import Literal

from langchain_core.messages import HumanMessage
from openai import BaseModel
from pydantic import Field


class ApiMessage(BaseModel):
    message: str = Field(..., description="The content of the message", examples=["Hello, how are you?"])


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(
        ...,
        description="The content of the message",
        examples=["Tengo una pregunta"],
    )


class QueryRequest(BaseModel):
    content: str = Field(
        ...,
        max_length=500,
        description="The content of the query",
        examples=["Hola, como estas?"],
    )
    history: list[ChatMessage] = Field(..., max_length=50)


class ApiUserMessage(HumanMessage):
    content: str = Field(
        ...,
        max_length=500,
        description="The content of the query",
        examples=["Hola, como estas?"],
    )


class WebsocketResponse(BaseModel):
    content: str = Field(
        ...,
        description="The content of the response",
        examples=["Estoy bien, gracias por preguntar"],
    )
    type: Literal["text", "error", "info"] = Field(
        ...,
        description="The type of the response",
        examples=["text"],
    )
    done: bool = Field(
        default=False,
        description="Whether the response is complete",
        examples=[True],
    )
