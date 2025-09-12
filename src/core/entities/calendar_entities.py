# Calendar Entities
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class CalendarSignature:
    full_name: str
    possition: str


@dataclass
class Event:
    scenery: str
    no: int
    activity: str
    days: int
    from_date: datetime
    to_date: datetime
    duration: int
    reference: str
    place: str


@dataclass
class ElectoralCalendar:
    id: int
    filename: str
    title: str
    resolution: str
    date: datetime
    introduction: Optional[str] = None
    signatures: List[CalendarSignature] = []
    events: List[Event] = []
