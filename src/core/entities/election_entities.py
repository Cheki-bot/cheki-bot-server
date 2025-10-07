from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from src.core.entities.political_entities import Candidacy


class Status(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    UPCOMING = "upcoming"


class Election(BaseModel):
    name: str
    description: str
    election_date: datetime
    candidacies: List[Candidacy] = Field(default_factory=list)
    status: str  # "active", "completed" or "upcoming"
    winner: Optional[Candidacy] = None
    result: Optional[str] = None
