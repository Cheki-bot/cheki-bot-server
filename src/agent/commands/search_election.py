from datetime import datetime
from typing import Optional

from langchain.chat_models.base import BaseChatModel
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableSerializable
from pydantic import TypeAdapter
from pymongo.database import Database

from src.agent.context_managers.prompts import SEARCH_ELECTION_PROMPT
from src.agent.interfaces.command import AsyncCommand
from src.agent.schemas import TopicSelection
from src.mongo.models.candidacies_models import Election


class SearchElection(AsyncCommand):
    def __init__(self, chat_model: BaseChatModel, db: Database) -> None:
        self.__chat_model = chat_model
        self.__db = db
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

    def __get_elections(
        self,
        election_name: Optional[str] = None,
        year: Optional[str] = None,
    ) -> list[Election]:
        if not election_name and not year:
            return []
        if not year:
            cursor = self.__db["elections"].find().sort("election_date").limit(4)
            return TypeAdapter(list[Election]).validate_python(cursor)

        from_date = datetime(int(year), 1, 1)
        to_date = datetime(int(year), 12, 31)
        cursor = self.__db["elections"].find(
            {
                "election_date": {"$gte": from_date, "$lte": to_date},
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
                "messages": [HumanMessage(content=election_name)],
                "elections_list": elections_list,
            }
        )
        obj = self.__db["elections"].find_one({"_id": res.get("_id")}) if res.get("_id") else None
        return Election.model_validate(obj) if obj else None

    def run(self, topic_selection: TopicSelection) -> Optional[Election]:
        election_name = topic_selection.extra_params.get("election_name")
        year = topic_selection.extra_params.get("year")
        elections = self.__get_elections(election_name, year)
        election_name = election_name or topic_selection.optimized_query
        election = self.__select_election(elections, election_name)
        return election
