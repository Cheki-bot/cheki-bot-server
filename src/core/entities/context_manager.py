from abc import ABC, abstractmethod

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage


class ContextManager(ABC):
    @abstractmethod
    async def retrieve_context(
        self,
        query: str,
        history: BaseChatMessageHistory,
    ) -> list[BaseMessage]:
        pass

    @abstractmethod
    async def build_system_message(self, query: str) -> BaseMessage:
        pass

    @abstractmethod
    async def trim_context(self, context: list[BaseMessage]) -> list[BaseMessage]:
        pass
