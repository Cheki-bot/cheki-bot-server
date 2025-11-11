from datetime import datetime
from enum import Enum

from src.mongo.models.mongo_model import MongoModel


class Roles(str, Enum):
    ADMIN = "admin"
    USER = "user"


class User(MongoModel):
    __collection_name__ = "users"
    username: str
    email: str
    password_hash: str
    role: Roles
    is_active: bool
    created_at: datetime
    updated_at: datetime
    failed_attempts: int
