from datetime import datetime
from typing import Optional

from bson import ObjectId
from langchain.chat_models.base import BaseChatModel
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableSerializable
from langchain_mongodb import MongoDBAtlasVectorSearch
from pydantic import TypeAdapter

from src.agent.context_managers.prompts import SEARCH_ELECTION_PROMPT
from src.agent.interfaces.command import AsyncCommand
from src.agent.schemas import TopicSelection
from src.core.tools import get_bo_current_datetime_str
from src.mongo.models.candidacies_models import Election


class SearchElection(AsyncCommand):
    def __init__(self, chat_model: BaseChatModel, vector_db: MongoDBAtlasVectorSearch) -> None:
        self.__chat_model = chat_model
        self.__db = vector_db.collection.database
        self.__vec_db = vector_db
        self.__chain: Optional[RunnableSerializable] = None

    @property
    def chain(self) -> RunnableSerializable:
        if self.__chain:
            return self.__chain
        json_parser = JsonOutputParser()
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SEARCH_ELECTION_PROMPT),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )
        self.__chain = prompt | self.__chat_model | json_parser
        return self.__chain

    async def __get_elections(
        self,
        topic_selection: TopicSelection,
        year: Optional[str] = None,
    ) -> list[Election]:
        if not year:
            cursor = self.__db["elections"].find().sort("election_date").limit(2)
            return TypeAdapter(list[Election]).validate_python(cursor)

        retriever = self.__vec_db.as_retriever(
            search_kwargs={
                "k": 2,
                "pre_filter": {
                    "topic": topic_selection.topic.value,
                    "collection_name": Election.__collection_name__,
                },
            }
        )
        docs = await retriever.ainvoke(topic_selection.optimized_query)

        _ids = [
            ObjectId(doc.metadata.get("data_id")) for doc in docs if doc.metadata.get("data_id")
        ]

        from_date = datetime(int(year), 1, 1)
        to_date = datetime(int(year), 12, 31)

        cursor = self.__db["elections"].find(
            {
                "election_date": {"$gte": from_date, "$lte": to_date},
                "_id": {"$in": _ids},
            }
        )
        return TypeAdapter(list[Election]).validate_python(cursor)

    def __select_election(
        self,
        elections: list[Election],
        election_name: str,
    ) -> Optional[Election]:
        if not elections:
            obj = self.__db["elections"].find_one({}, sort={"election_date": -1})
            return Election.model_validate(obj)
        elections_list = "\n".join(
            [f"{str(e.id)} - {e.name} - {e.election_date}" for e in elections]
        )

        res = self.chain.invoke(
            {
                "date": get_bo_current_datetime_str(),
                "messages": [HumanMessage(content=election_name)],
                "elections_list": elections_list,
            }
        )

        if res.get("_id") is None:
            return None

        obj = self.__db["elections"].find_one({"_id": ObjectId(res.get("_id"))})
        return Election.model_validate(obj) if obj else None

    async def run(self, topic_selection: TopicSelection) -> Optional[Election]:
        year = topic_selection.params.get("year")
        elections = await self.__get_elections(topic_selection, year)
        election = self.__select_election(elections, topic_selection.optimized_query)
        return election

    async def __call__(self, topic_selection: TopicSelection) -> Optional[Election]:
        return await self.run(topic_selection)
