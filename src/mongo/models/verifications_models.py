# Verification Entities
from datetime import datetime
from typing import List

from pydantic import BaseModel

from .mongo_model import MongoModel


class NewsTag(BaseModel):
    name: str
    url: str


class NewsVerification(MongoModel):
    __collection_name__ = "news_verifications"
    title: str
    classified_as: str
    section_url: str
    summary: str
    body: str
    url: str
    publication_date: datetime
    tags: List[NewsTag]
