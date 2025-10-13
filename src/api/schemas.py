from typing import Literal, Optional

from openai import BaseModel
from pydantic import Field


class ApiMessage(BaseModel):
    message: str = Field(
        ..., description="The content of the message", examples=["Hello, how are you?"]
    )


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

class RegisterRequest(BaseModel):
    email: str = Field(..., examples=["user@example.com"])
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = Field(default=None)
    role: Literal["Admin", "User"] = Field(default="User")

class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str = Field(alias="_id")
    email: str
    full_name: Optional[str] = None
    role: Literal["Admin", "User"]
    is_active: bool
