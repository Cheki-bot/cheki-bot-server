# Verification Entities
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List


class NewsClassification(Enum):
    FALSE = "falso"
    TRUE = "verdadero"
    MISLEADING = "engañoso"
    PHOTO_MONTAGE = "foto montaje"
    FALSE_BUT = "falso pero ..."  # preguntar si podemos cambiar el termino
    TRUE_BUT = "verdadero pero ..."  # aquí tambien


@dataclass
class NewsTag:
    name: str
    url: str


@dataclass
class NewsVerification:
    id: int
    title: int
    classified_as: NewsClassification
    section_url: str
    summary: str
    body: str
    url: str
    publication_date: datetime
    tags: List[NewsTag]
