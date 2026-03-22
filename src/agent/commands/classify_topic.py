from typing import Sequence

from langchain.chat_models.base import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableSerializable

from src.agent.context_managers.prompts import (
    COMPLETE_QUERY_PROMPT,
    TOPIC_SELECTION_PROMPT,
)
from src.agent.interfaces.command import AsyncCommand
from src.agent.schemas import TopicSelection


class AsyncClassifyTopic(AsyncCommand):
    def __init__(self, model: BaseChatModel) -> None:
        self.__model = model
        self.__chain = self.__build_chain()

    def __build_chain(self) -> RunnableSerializable:
        json_parser = JsonOutputParser()
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "{prompt}"),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )
        return prompt | self.__model | json_parser

    async def run(self, messages: Sequence[BaseMessage]) -> list[TopicSelection]:
        if not messages:
            raise ValueError("No se recibieron mensajes")

        user_query = str(messages[-1].content)

        optimized_query: dict = await self.__chain.ainvoke(
            {
                "prompt": COMPLETE_QUERY_PROMPT,
                "messages": messages,
            }
        )

        completed_query: str | None = optimized_query.get("optimized_query")
        if not completed_query:
            raise ValueError("No se pudo obtener la consulta completa.")

        topics: list[dict] = await self.__chain.ainvoke(
            {
                "prompt": TOPIC_SELECTION_PROMPT,
                "messages": [HumanMessage(content=completed_query)],
            }
        )
        if not isinstance(topics, list):
            raise ValueError("No su pudo identificar el tema de la solicitud")

        topics_selections: list[TopicSelection] = []
        for topic in topics:
            topic_obj = {
                "user_query": user_query,
                **topic,
                **optimized_query,
            }
            topics_selections.append(TopicSelection.model_validate(topic_obj))

        return topics_selections

    async def __call__(self, messages: Sequence[BaseMessage]) -> list[TopicSelection]:
        return await self.run(messages)
