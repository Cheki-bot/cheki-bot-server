# Entity package initialization

# Import all entities for easy access
from .calendar_entities import CalendarSignature, ElectoralCalendar, Event
from .election_entities import Election
from .political_entities import Candidacy, GovernmentItem, GovernmentProgram, PoliticalParty, Politician
from .verification_entities import NewsClassification, NewsTag, NewsVerification

__all__ = [
    "PoliticalParty",
    "Politician",
    "GovernmentItem",
    "GovernmentProgram",
    "Candidacy",
    "CalendarSignature",
    "Event",
    "ElectoralCalendar",
    "Election",
    "NewsClassification",
    "NewsTag",
    "NewsVerification"
]