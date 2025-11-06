from bson import ObjectId
from fastapi import HTTPException
from langchain_core.documents import Document
from langchain_mongodb import MongoDBAtlasVectorSearch

from src.agent.schemas import Topic
from src.api.schemas import RecordData
from src.core.config import settings
from src.core.tools import sanitize_text_input
from src.mongo.models.verifications_models import NewsVerification


class IndexingService:
    def __init__(self, vector_db: MongoDBAtlasVectorSearch):
        self.__vector_db = vector_db

    @property
    def db(self):
        return self.__vector_db.collection.database

    @property
    def vector_db(self):
        return self.__vector_db

    def __index_new_verification(self, data: RecordData) -> list[Document]:
        record = self.db[data.collection_name].find_one({"_id": ObjectId(data.id)})

        if record is None:
            raise HTTPException(status_code=404, detail="Record not found")

        verification = NewsVerification.model_validate(record)

        metadata = {
            "data_id": ObjectId(str(verification.id)),
            "collection_name": NewsVerification.__collection_name__,
            "topic": Topic.VERIFICATION_OF_NEWS.value,
        }

        title = sanitize_text_input(verification.title)
        body = sanitize_text_input(verification.body)
        summary = sanitize_text_input(verification.summary)
        documents = [
            Document(page_content=title, metadata=metadata),
            Document(page_content=body, metadata=metadata),
            Document(page_content=summary, metadata=metadata),
        ]
        return documents

    async def index_record(self, data: RecordData):
        indexers = {NewsVerification.__collection_name__: self.__index_new_verification}

        if data.collection_name not in indexers:
            raise HTTPException(400, f"Collection {data.collection_name} not supported")  # type: ignore

        documents = indexers[data.collection_name](data)
        self.db[settings.mongo.collection_name].delete_many({"data_id": ObjectId(data.id)})
        ids = await self.vector_db.aadd_documents(documents)
        return ids
