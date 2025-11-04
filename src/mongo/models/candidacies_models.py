from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from src.mongo.types import PyObjectId

from .mongo_model import MongoModel


class CandidacyStatus(str, Enum):
    ACTIVE = "habilitado"
    INACTIVE = "inhabilitado"
    WITHDRAWN = "se retiró"


class ElectionStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    UPCOMING = "upcoming"


class ElectionRound(str, Enum):
    FIRST_ROUND = "primera vuelta"
    SECOND_ROUND = "segunda vuelta"


class Politician(BaseModel):
    full_name: str
    position: str
    is_active: bool = Field(default=True)


class PoliticalParty(BaseModel):
    name: str
    sigla: str
    description: Optional[str] = None


class Candidacy(MongoModel):
    __collection_name__ = "candidacies"
    party: PoliticalParty
    candidates: list[Politician]
    status: CandidacyStatus = Field(default=CandidacyStatus.ACTIVE)
    government_plan: str  # in Markdown
    election_id: PyObjectId = Field(alias="election_id")
    source: str = Field("")


class Election(MongoModel):
    __collection_name__ = "elections"
    name: str
    description: str
    election_date: datetime
    candidacies: list[Candidacy] = Field(default_factory=list)
    status: ElectionStatus = Field(default=ElectionStatus.UPCOMING)
    active_round: ElectionRound = Field(default=ElectionRound.FIRST_ROUND)
    winner: Optional[Candidacy] = None
    result: Optional[str] = None
    source: str = Field("")
