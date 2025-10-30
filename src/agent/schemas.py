from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class DocType(Enum):
    VERIFICATIONS = "verifications"
    GOV_PROGRAMS = "government_programs"
    CALENDAR_META = "calendar_metadata"
    CALENDAR = "calendar"
    CANDIDATES = "candidates"
    Q_A = "questions_and_answers"


class Topic(str, Enum):
    VERIFICATION_OF_NEWS = "VERIFICATION_OF_NEWS"
    CANDIDATES = "CANDIDATES"
    GOVERNMENT_PROPOSALS = "GOVERNMENT_PROPOSALS"
    ELECTORAL_CALENDAR = "ELECTORAL_CALENDAR"
    QUESTIONS_AND_ANSWERS = "QUESTIONS_AND_ANSWERS"
    CAPABILITIES = "CAPABILITIES"
    GENERAL_INFO = "GENERAL_INFO"
    INSTRUCTIONS = "INSTRUCTIONS"


class Platform(str, Enum):
    WEB = "web"
    TELEGRAM = "Telegram"
    WHATSAPP = "Whatsapp"


class TopicSelection(BaseModel):
    topic: Topic
    description: str
    user_query: str = Field("")
    optimized_query: str = Field("")
    additional_topics: list[Topic] = Field(default_factory=list)
    extra_params: dict = Field(default_factory=dict)


class AgentResponseChunk(BaseModel):
    content: str = Field(
        ...,
        description="The content of the response",
        examples=["Estoy bien, gracias por preguntar"],
    )
    type: Literal["text", "error", "info"] = Field(
        default="info",
        description="The type of the response",
        examples=["text"],
    )
    done: bool = Field(
        default=False,
        description="Whether the response is complete",
        examples=[True],
    )
