# Political Entities
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class PoliticalParty:
    id: int
    name: str
    sigla: str
    description: Optional[str] = None


@dataclass
class Politician:
    id: int
    full_name: str
    position: str
    party: PoliticalParty
    photo_url: Optional[str] = None
    social_media: Optional[dict[str, str]] = None
    political_history: Optional[List[dict[str, str]]] = None


@dataclass
class GovernmentItem:
    header: str
    content: str
    summary: Optional[str] = None


@dataclass
class GovernmentProgram:
    id: int
    title: str
    description: Optional[str] = None
    government_plan: List[GovernmentItem] = field(default_factory=list)


@dataclass
class Candidacy:
    party: PoliticalParty
    candidates: List[Politician]
    election_year: int
    status: str
    government_program: Optional[GovernmentProgram] = None
