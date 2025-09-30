from enum import Enum
from typing import Optional

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
    ELECTORAL_INFORMATION = "ELECTORAL_INFORMATION"
    CANDIDATES = "CANDIDATES"
    GOVERNMENT_PROPOSALS = "GOVERNMENT_PROPOSALS"
    ELECTORAL_CALENDAR = "ELECTORAL_CALENDAR"
    QUESTIONS_AND_ANSWERS = "QUESTIONS_AND_ANSWERS"
    CAPABILITIES = "CAPABILITIES"
    GENERAL_INFO = "GENERAL_INFO"
    INSTRUCTIONS = "INSTRUCTIONS"
    NOT_FOUND = "NOT_FOUND"
    OTHERS = "OTHERS"


class TopicSelection(BaseModel):
    topic: Topic
    description: str
    user_query: Optional[str] = None
    optimized_query: Optional[str] = None
    additional_topics: list[Topic] = Field(default_factory=list)
