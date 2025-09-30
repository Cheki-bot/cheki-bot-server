from typing import Sequence

from langchain.chat_models.base import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnableSequence

from src.agent.schemas import TopicSelection


class TopicSelector:
    def __init__(self, model=BaseChatModel) -> None:
        self.__model = model
        self.__chain = self.__build_chain()

    def __build_chain(self) -> RunnableSequence:
        json_parser = JsonOutputParser()
        return self.__model | json_parser

    async def run(self, messages: Sequence[BaseMessage]) -> TopicSelection:
        result = await self.__chain.ainvoke(messages)
        return TopicSelection(**result)

    async def __call__(self, messages: Sequence[BaseMessage]) -> TopicSelection:
        return await self.run(messages)
