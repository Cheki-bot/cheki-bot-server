# Calendar Entities
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class CalendarSignature(BaseModel):
    full_name: str
    possition: str


class Event(BaseModel):
    scenery: str
    no: int
    activity: str
    days: int
    from_date: datetime
    to_date: datetime
    duration: int
    reference: str
    place: str


class ElectoralCalendar(BaseModel):
    filename: str
    title: str
    resolution: str
    date: datetime
    introduction: Optional[str] = None
    signatures: List[CalendarSignature] = []
    events: List[Event] = []
