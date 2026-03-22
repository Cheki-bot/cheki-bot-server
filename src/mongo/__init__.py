from typing import AsyncGenerator, Optional

from pymongo import AsyncMongoClient, MongoClient
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.database import Database

from src import ENV
from src.core.config import settings

client: Optional[MongoClient] = None
db: Optional[Database] = None


def init_mongo():
    client = MongoClient(ENV.mongo.uri)
    db = client.get_database(ENV.mongo.db_name)
    return client, db


def close_mongo():
    global client
    if client:
        client.close()


async def get_async_mongo_db() -> AsyncGenerator[Database, None]:
    yield get_mongo_db()


def get_mongo_db() -> Database:
    global client, db
    if db is None or client is None:
        client, db = init_mongo()
        return db
    else:
        try:
            # Verificar si el cliente sigue activo intentando acceder a su estado
            client.admin.command("ping")
            return db
        except Exception:
            # Si hay un error, reinicializar la conexión
            client, db = init_mongo()
            return db


async def get_asyncmongo_db() -> AsyncDatabase:
    client = AsyncMongoClient(settings.mongo.uri)
    db = client.get_database(settings.mongo.db_name)
    return db
