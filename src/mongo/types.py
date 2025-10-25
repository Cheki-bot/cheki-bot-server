from typing import Annotated

from bson import ObjectId
from pydantic import BeforeValidator

PyObjectId = Annotated[ObjectId, BeforeValidator(lambda v: ObjectId(str(v)))]
