# Calendar Entities
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from src.mongo.models.mongo_model import MongoModel
from src.mongo.types import PyObjectId


class CalendarSignature(BaseModel):
    full_name: str
    position: str


class CalendarEvent(MongoModel):
    __collection_name__ = "calendar_events"
    scenery: str
    no: int
    activity: str
    days: int
    from_date: datetime
    to_date: datetime
    duration: int
    reference: str
    place: str
    calendar_id: PyObjectId


class ElectoralCalendar(MongoModel):
    __collection_name__ = "calendars"
    pdf_url: str
    title: str
    resolution: str
    date: datetime
    introduction: Optional[str] = None
    signatures: List[CalendarSignature] = []
    events: List[CalendarEvent] = Field(default_factory=list, exclude=True)
    election_id: PyObjectId
