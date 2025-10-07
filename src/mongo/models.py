from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from src.core.entities import Candidacy, Election, NewsVerification
from src.mongo.types import PyObjectId


class MongoModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    model_config = ConfigDict(
        use_enum_values=True,
        validate_assignment=True,
        populate_by_name=True,
        loc_by_alias=True,
    )


class CandidacyModel(Candidacy, MongoModel):
    election_id: PyObjectId = Field(...)


class ElectionModel(Election, MongoModel):
    candidacies: List[CandidacyModel] = Field(default_factory=list, exclude=True)


class NewsVerificationModel(NewsVerification, MongoModel):
    pass
