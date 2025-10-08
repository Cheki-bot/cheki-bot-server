# Verification Entities
from datetime import datetime
from typing import List

from pydantic import BaseModel


class NewsTag(BaseModel):
    name: str
    url: str


class NewsVerification(BaseModel):
    title: str
    classified_as: str
    section_url: str
    summary: str
    body: str
    url: str
    publication_date: datetime
    tags: List[NewsTag]
