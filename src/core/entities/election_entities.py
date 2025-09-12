from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from src.core.entities.calendar_entities import ElectoralCalendar
from src.core.entities.political_entities import Candidacy


@dataclass
class Election:
    id: int
    name: str
    election_date: datetime
    electoral_calendar: ElectoralCalendar
    candidacies: List[Candidacy]
    status: str  # "active", "completed" or "upcoming"
    winner: Optional[Candidacy] = None
