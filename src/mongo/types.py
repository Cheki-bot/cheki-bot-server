from typing import Annotated

from bson import ObjectId
from pydantic import BeforeValidator, PlainSerializer

PyObjectId = Annotated[
    ObjectId,
    BeforeValidator(lambda v: ObjectId(str(v))),
    PlainSerializer(lambda v: str(v), return_type=str, when_used="json"),
]
