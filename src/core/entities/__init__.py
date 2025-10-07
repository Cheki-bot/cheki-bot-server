# Entity package initialization

# Import all entities for easy access
from .calendar_entities import CalendarSignature, ElectoralCalendar, Event
from .election_entities import Election, Status
from .political_entities import Candidacy, GovernmentItem, GovernmentProgram, PoliticalParty, Politician
from .verification_entities import NewsTag, NewsVerification

__all__ = [
    "CalendarSignature",
    "Candidacy",
    "Election",
    "ElectoralCalendar",
    "Event",
    "GovernmentItem",
    "GovernmentProgram",
    "NewsTag",
    "NewsVerification",
    "PoliticalParty",
    "Politician",
    "Status",
]
