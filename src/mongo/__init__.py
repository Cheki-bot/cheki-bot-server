from typing import AsyncGenerator, Optional

from pymongo import MongoClient
from pymongo.database import Database

from src import ENV

client: Optional[MongoClient] = None
db: Optional[Database] = None


def init_mongo():
    client = MongoClient(ENV.mongo.uri)
    db = client.get_database(ENV.mongo.db_name)
    print("MongoDB connected successfully")
    return client, db


def close_mongo():
    global client
    if client:
        client.close()
        print("MongoDB connection closed")


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
