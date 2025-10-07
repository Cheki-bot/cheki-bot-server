# Political Entities
from dataclasses import field
from typing import List, Optional

from pydantic import BaseModel


class PoliticalParty(BaseModel):
    name: str
    sigla: str
    description: Optional[str] = None


class Politician(BaseModel):
    full_name: str
    position: str
    social_media: Optional[dict[str, str]] = None
    political_history: Optional[List[dict[str, str]]] = None


class GovernmentItem(BaseModel):
    header: str
    content: str
    summary: Optional[str] = None


class GovernmentProgram(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    government_plan: List[GovernmentItem] = field(default_factory=list)


class Candidacy(BaseModel):
    party: PoliticalParty
    candidates: List[Politician]
    status: str
    government_program: Optional[GovernmentProgram] = None
