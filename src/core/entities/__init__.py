# Entity package initialization

# Import all entities for easy access
from .calendar_entities import CalendarSignature, ElectoralCalendar, Event

__all__ = [
    "CalendarSignature",
    "ElectoralCalendar",
    "Event",
]
