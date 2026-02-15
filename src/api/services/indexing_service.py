from typing import Any, Callable

import tiktoken
from bson import ObjectId
from langchain_core.documents import Document
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from pydantic import TypeAdapter
from pymongo.database import Database

from src.agent.schemas import Topic
from src.api.schemas import RecordData
from src.core.config import settings
from src.core.tools import sanitize_text_input
from src.mongo.models.calendar_models import CalendarEvent, ElectoralCalendar
from src.mongo.models.candidacies_models import Candidacy, Election
from src.mongo.models.qa_model import QuestionsAndAnswers
from src.mongo.models.verifications_models import NewsVerification


class IndexingService:
    def __init__(self, vector_db: MongoDBAtlasVectorSearch):
        self.__vector_db = vector_db

        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
            ("####", "Header 4"),
        ]
        self.__encoding = tiktoken.encoding_for_model("text-embedding-3-small")
        self.__markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=headers_to_split_on
        )
        self.__splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=100,
            length_function=lambda text: len(self.__encoding.encode(text)),
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    @property
    def db(self) -> Database[dict[str, Any]]:
        return self.__vector_db.collection.database

    @property
    def vector_db(self):
        return self.__vector_db

    def __find_records(self, data: RecordData):
        ids = [ObjectId(_id) for _id in data.ids]
        records = self.db[data.collection_name].find({"_id": {"$in": ids}})
        return records.to_list()

    def __index_new_verification(self, records: list[dict]) -> list[Document]:
        verifications = TypeAdapter(list[NewsVerification]).validate_python(records)

        base_metadata = {
            "collection_name": NewsVerification.__collection_name__,
            "topic": Topic.VERIFICATION_OF_NEWS.value,
        }
        documents = []
        for verification in verifications:
            metadata = {"data_id": ObjectId(str(verification.id)), **base_metadata}
            title = sanitize_text_input(verification.title)
            body = sanitize_text_input(verification.body)
            summary = sanitize_text_input(verification.summary)
            news_documents = [
                Document(page_content=title, metadata=metadata),
                Document(page_content=body, metadata=metadata),
                Document(page_content=summary, metadata=metadata),
            ]
            documents.extend(news_documents)

        return self.__splitter.split_documents(documents)

    def __index_election(self, records: list[dict]) -> list[Document]:
        elections = TypeAdapter(list[Election]).validate_python(records)
        base_metadata = {"collection_name": Election.__collection_name__}
        documents = []
        for election in elections:
            name = sanitize_text_input(f"{election.name} {election.active_round} {election.status}")
            description = sanitize_text_input(election.description)
            result = sanitize_text_input(election.description)
            content = f"{name}\n\n{description}\n\n{result}\n"
            metadata = {"data_id": election.id, **base_metadata}
            documents.append(Document(page_content=content, metadata=metadata))

        return documents

    def __index_electoral_calendar(self, records: list[dict]):
        for record in records:
            del record["events"]
        calendars = TypeAdapter(list[ElectoralCalendar]).validate_python(records)
        base_metadata = {
            "topic": Topic.ELECTORAL_CALENDAR.value,
            "collection_name": ElectoralCalendar.__collection_name__,
        }

        documents = []
        for calendar in calendars:
            title = sanitize_text_input(calendar.title)
            date = calendar.date.strftime("%a, %m/%d/%Y - %H:%M")
            resolution = sanitize_text_input(calendar.resolution)
            introduction = sanitize_text_input(calendar.introduction or "")
            content = f"{title} - {date} - {resolution}\n\n{introduction}\n"
            metadata = {"data_id": calendar.id, **base_metadata}
            documents.append(Document(page_content=content, metadata=metadata))

        return documents

    def __index_calendar_event(self, records: list[dict]):
        events = TypeAdapter(list[CalendarEvent]).validate_python(records)

        documents = []
        base_metadata = {
            "topic": Topic.ELECTORAL_CALENDAR.value,
            "collection_name": CalendarEvent.__collection_name__,
        }
        for event in events:
            activity = sanitize_text_input(event.activity)
            metadata = {"data_id": event.id, "calendar_id": event.calendar_id, **base_metadata}
            documents.append(Document(page_content=activity, metadata=metadata))
        return documents

    def __index_candidacy(self, records: list[dict]):
        candidacies = TypeAdapter(list[Candidacy]).validate_python(records)

        all_documents = []
        for candidacy in candidacies:
            metadata = {
                "data_id": candidacy.id,
                "topic": Topic.CANDIDACIES.value,
                "collection_name": Candidacy.__collection_name__,
                "election_id": candidacy.election_id,
            }

            content = f"partido {candidacy.party.name} {candidacy.party.sigla}"
            content = sanitize_text_input(content)

            all_documents.append(Document(content, metadata=metadata))

            for politician in candidacy.candidates:
                content = f"{politician.full_name} como {politician.position}"
                all_documents.append(Document(content, metadata=metadata))

            gov_program_docs = self.__markdown_splitter.split_text(candidacy.government_plan)

            metadata = {
                **metadata,
                "data_id": candidacy.id,
                "topic": Topic.GOVERNMENT_PROPOSALS.value,
            }

            for doc in gov_program_docs:
                if len(self.__encoding.encode(doc.page_content)) > 1000:
                    sub_docs = self.__splitter.split_documents([doc])
                else:
                    sub_docs = [doc]

                for sub_doc in sub_docs:
                    content = "\n".join([v for v in sub_doc.metadata.values()])
                    content = f"{content}\n\n{sub_doc.page_content}"
                    all_documents.append(Document(page_content=content, metadata=metadata))

        return all_documents

    def __index_qa(self, records: list[dict]):
        questions_and_answers = TypeAdapter(list[QuestionsAndAnswers]).validate_python(records)

        documents = []
        base_metadata = {
            "topic": Topic.QUESTIONS_AND_ANSWERS.value,
            "collection_name": QuestionsAndAnswers.__collection_name__,
        }
        for qa in questions_and_answers:
            question = sanitize_text_input(qa.question)
            documents.append(
                Document(
                    page_content=question,
                    metadata={"data_id": qa.id, **base_metadata},
                )
            )

        return documents

    async def index_record(self, data: RecordData) -> list[str]:
        records = self.__find_records(data)

        indexers: dict[str, Callable[[list[dict]], list[Document]]] = {
            NewsVerification.__collection_name__: self.__index_new_verification,
            Election.__collection_name__: self.__index_election,
            ElectoralCalendar.__collection_name__: self.__index_electoral_calendar,
            CalendarEvent.__collection_name__: self.__index_calendar_event,
            Candidacy.__collection_name__: self.__index_candidacy,
            QuestionsAndAnswers.__collection_name__: self.__index_qa,
        }
        if data.collection_name not in indexers:
            return []
        documents = indexers[data.collection_name](records)
        await self.delete_index(data)
        ids = await self.vector_db.aadd_documents(documents)
        return ids

    async def delete_index(self, data: RecordData):
        collection = self.db[settings.mongo.collection_name]
        ids = [ObjectId(_id) for _id in data.ids]

        collection.delete_many(
            {
                "data_id": {"$in": ids},
                "collection_name": data.collection_name,
            }
        )
