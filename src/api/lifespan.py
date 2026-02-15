import asyncio
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI
from langchain_mongodb import MongoDBAtlasVectorSearch
from pymongo.asynchronous.database import AsyncDatabase

from src.api.dependencies.injectables import get_embedding_model
from src.api.schemas import RecordData
from src.api.services.indexing_service import IndexingService
from src.core.config import settings
from src.mongo import get_asyncmongo_db, get_mongo_db
from src.mongo.models import (
    CalendarEvent,
    Candidacy,
    Election,
    ElectoralCalendar,
    NewsVerification,
    QuestionsAndAnswers,
)


async def watch_collection(collection_name: str, service: IndexingService, async_db: AsyncDatabase):
    coleccion = async_db[collection_name]
    actions = {
        "insert": service.index_record,
        "update": service.index_record,
        "delete": service.delete_index,
    }
    async with await coleccion.watch() as stream:
        async for change in stream:
            try:
                data = RecordData(
                    _ids=[str(change["documentKey"]["_id"])],
                    collection_name=collection_name,
                )
                action = actions.get(change["operationType"])

                if action is None:
                    continue
                await action(data)

            except Exception as e:
                print(
                    f"Error processing {change.get('operationType', 'unknown')} operation in '{collection_name}': {e}"
                )
                print(f"Change data: {change}")
                print("Full traceback:")
                traceback.print_exc()

                continue


@asynccontextmanager
async def lifespan(app: FastAPI):
    async_db = await get_asyncmongo_db()
    db = get_mongo_db()
    emb_model = get_embedding_model()
    collection = db.get_collection(settings.mongo.collection_name)
    vectordb = MongoDBAtlasVectorSearch(
        collection=collection,
        embedding=emb_model,
        index_name=settings.mongo.index_name,
        relevance_score_fn="cosine",
    )
    service = IndexingService(vectordb)

    tasks = [
        NewsVerification.__collection_name__,
        Election.__collection_name__,
        ElectoralCalendar.__collection_name__,
        CalendarEvent.__collection_name__,
        Candidacy.__collection_name__,
        QuestionsAndAnswers.__collection_name__,
    ]
    print("Initializing database monitoring...")
    background_tasks = [
        asyncio.create_task(watch_collection(coll, service, async_db)) for coll in tasks
    ]
    yield
    for task in background_tasks:
        task.cancel()
    print("Stopping database monitoring...")
