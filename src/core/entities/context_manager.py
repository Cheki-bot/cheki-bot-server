from abc import ABC, abstractmethod
from typing import Sequence

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
    async def build_system_messages(self, query: str) -> Sequence[BaseMessage]:
        pass

    @abstractmethod
    async def trim_context(self, context: list[BaseMessage]) -> list[BaseMessage]:
        pass
