from datetime import datetime, timedelta

from bson import ObjectId
from langchain_mongodb import MongoDBAtlasVectorSearch
from pydantic import TypeAdapter
from pymongo.database import Database

from src.agent.commands.search_election import SearchElection
from src.agent.context_managers.context_builder import ContextBuilder
from src.agent.interfaces.build_context import BuildContext
from src.agent.schemas import TopicSelection
from src.core.tools import get_bo_current_datetime
from src.mongo.models.calendar_models import CalendarEvent, ElectoralCalendar
from src.mongo.models.candidacies_models import Election


class BuildCalendarContext(BuildContext):
    def __init__(
        self, vector_db: MongoDBAtlasVectorSearch, search_election: SearchElection
    ) -> None:
        self.__vector_db = vector_db
        self.__search_election = search_election

    @property
    def db(self) -> Database:
        return self.__vector_db.collection.database

    @property
    def vdb(self) -> MongoDBAtlasVectorSearch:
        return self.__vector_db

    @property
    def search_election(self) -> SearchElection:
        return self.__search_election

    async def run(
        self,
        topic_selection: TopicSelection,
        context_builder: ContextBuilder,
    ) -> ContextBuilder:
        election = await self.search_election(topic_selection)

        if not election:
            election = Election.model_validate(
                self.db[Election.__collection_name__].find_one({}, {}, sort=[("_id", -1)])
            )

        collection = self.db[ElectoralCalendar.__collection_name__]
        election_calendar = collection.find_one({"election_id": election.id})
        calendar = ElectoralCalendar.model_validate(election_calendar)

        search_kwargs = {
            "k": 10,
            "pre_filter": {
                "topic": topic_selection.topic,
                "calendar_id": calendar.id,
            },
        }
        retriever = self.vdb.as_retriever(search_kwargs=search_kwargs)
        docs = await retriever.ainvoke(topic_selection.optimized_query)
        ids = {
            ObjectId(doc.metadata.get("data_di"))
            for doc in docs
            if doc.metadata.get("data_id") is not None
        }
        filters: dict = {"_id": {"$in": list(ids)}}
        events_raw = self.db[CalendarEvent.__collection_name__].find(filters)
        events = TypeAdapter(list[CalendarEvent]).validate_python(events_raw)

        now = get_bo_current_datetime()
        default_from_date = now - timedelta(days=30)
        default_to_date = now + timedelta(days=30)

        start_date = topic_selection.params.get("start_date")
        end_date = topic_selection.params.get("end_date")

        try:
            from_date = datetime.fromisoformat(start_date) if start_date else default_from_date
            to_date = datetime.fromisoformat(end_date) if end_date else default_to_date
            to_date = to_date if to_date > from_date else from_date + timedelta(days=30)
        except ValueError:
            from_date = default_from_date
            to_date = default_to_date

        filters = {
            "from_date": {"$gte": from_date},
            "to_date": {"$lte": to_date},
            "calendar_id": calendar.id,
        }
        events_raw = self.db[CalendarEvent.__collection_name__].find(filters)
        events.extend(TypeAdapter(list[CalendarEvent]).validate_python(events_raw))

        context_builder.add_calendars([calendar])
        context_builder.add_events(events)

        return context_builder
