from bson import ObjectId
from fastapi import HTTPException
from langchain_core.documents import Document
from langchain_mongodb import MongoDBAtlasVectorSearch

from src.agent.schemas import Topic
from src.api.schemas import RecordData
from src.core.config import settings
from src.core.tools import sanitize_text_input
from src.mongo.models.calendar_models import CalendarEvent, ElectoralCalendar
from src.mongo.models.candidacies_models import Election
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

    def __find_record(self, data: RecordData):
        record = self.db[data.collection_name].find_one({"_id": ObjectId(data.id)})
        if record is None:
            raise HTTPException(
                status_code=404,
                detail=f"Record with ID {data.id} not found in collection {data.collection_name}",
            )

        return record

    def __index_new_verification(self, data: RecordData) -> list[Document]:
        record = self.__find_record(data)

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

    def __index_election(self, data: RecordData) -> list[Document]:
        record = self.__find_record(data)
        election = Election.model_validate(record)
        metadata = {
            "data_id": election.id,
            "collection_name": Election.__collection_name__,
        }
        name = sanitize_text_input(election.name)
        description = sanitize_text_input(election.description)
        result = sanitize_text_input(election.description)
        content = f"{name}\n\n{description}\n\n{result}\n"

        document = Document(page_content=content, metadata=metadata)
        return [document]

    def __index_electoral_calendar(self, data: RecordData):
        record = self.__find_record(data)
        calendar = ElectoralCalendar.model_validate(record)
        metadata = {
            "data_id": calendar.id,
            "topic": Topic.ELECTORAL_CALENDAR.value,
            "collection_name": ElectoralCalendar.__collection_name__,
        }
        title = sanitize_text_input(calendar.title)
        date = calendar.date.strftime("%a, %m/%d/%Y - %H:%M")
        resolution = sanitize_text_input(calendar.resolution)
        introduction = sanitize_text_input(calendar.introduction or "")
        content = f"{title} - {date} - {resolution}\n\n{introduction}\n"
        return [Document(page_content=content, metadata=metadata)]

    async def __index_calendar_event(self, data: RecordData):
        record = self.__find_record(data)
        event = CalendarEvent.model_validate(record)
        metadata = {
            "data_id": event.id,
            "calendar_id": event.calendar_id,
            "topic": Topic.ELECTORAL_CALENDAR.value,
            "collection_name": CalendarEvent.__collection_name__,
        }
        activity = sanitize_text_input(event.activity)
        return [Document(page_content=activity, metadata=metadata)]

    async def index_record(self, data: RecordData):
        indexers = {
            NewsVerification.__collection_name__: self.__index_new_verification,
            Election.__collection_name__: self.__index_election,
            ElectoralCalendar.__collection_name__: self.__index_electoral_calendar,
            CalendarEvent.__collection_name__: self.__index_calendar_event,
            # Candidacy.__collection_name__: self.__index_candidacy,
            # QuestionsAndAnswers.__collection_name__: self.__index_qa,
        }

        if data.collection_name not in indexers:
            raise HTTPException(400, f"Collection {data.collection_name} not supported")  # type: ignore

        documents = indexers[data.collection_name](data)
        self.db[settings.mongo.collection_name].delete_many({"data_id": ObjectId(data.id)})
        ids = await self.vector_db.aadd_documents(documents)
        return ids
