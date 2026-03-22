from datetime import datetime

from bson import ObjectId
from langchain_mongodb import MongoDBAtlasVectorSearch
from pydantic import TypeAdapter
from pymongo.database import Database

from src.agent.context_managers.context_builder import ContextBuilder
from src.agent.interfaces import BuildContext
from src.agent.schemas import TopicSelection
from src.core.tools import get_bo_current_datetime
from src.mongo.models import NewsVerification


class BuildNewsVerificatiosContext(BuildContext):
    def __init__(self, vector_db: MongoDBAtlasVectorSearch) -> None:
        self.__db = vector_db.collection.database
        self.__vec_db = vector_db

    @property
    def db(self) -> Database:
        return self.__db

    async def run(self, topic_selection: TopicSelection, context_builder: ContextBuilder):
        collection = self.db.get_collection(NewsVerification.__collection_name__)
        search_kwargs = {
            "k": 5,
            "pre_filter": {
                "topic": topic_selection.topic.value,
                "collection_name": NewsVerification.__collection_name__,
            },
        }

        retriever = self.__vec_db.as_retriever(search_kwargs=search_kwargs)
        docs = await retriever.ainvoke(topic_selection.optimized_query)

        ids = {
            ObjectId(doc.metadata.get("data_id"))
            for doc in docs
            if doc.metadata.get("data_id") is not None
        }
        filters: dict = {"_id": {"$in": list(ids)}}

        year_str = str(topic_selection.params.get("year", ""))
        year = int(year_str) if year_str.isnumeric() else get_bo_current_datetime().year

        if year:
            from_date = datetime(year, 1, 1)
            to_date = datetime(year, 12, 31)

            filters.update({"publication_date": {"$gte": from_date, "$lte": to_date}})

        articles = TypeAdapter(list[NewsVerification]).validate_python(
            collection.find(filters).sort({"publication_date": -1})
        )

        context_builder.add_news_verifications(articles)

        return context_builder
