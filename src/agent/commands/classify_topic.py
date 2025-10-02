from typing import Sequence

from langchain.chat_models.base import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableSerializable

from src.agent.context_managers.prompts import TOPIC_SELECTION_PROMPT, get_topics
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
                ("system", TOPIC_SELECTION_PROMPT),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        return prompt | self.__model | json_parser

    async def run(self, messages: Sequence[BaseMessage]) -> TopicSelection:
        topics = get_topics()
        result = await self.__chain.ainvoke(
            {
                "topics": topics,
                "messages": messages,
            }
        )
        return TopicSelection(**result)

    async def __call__(self, messages: Sequence[BaseMessage]) -> TopicSelection:
        return await self.run(messages)
