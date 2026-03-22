from abc import abstractmethod

from src.agent.context_managers.context_builder import ContextBuilder
from src.agent.interfaces.command import AsyncCommand
from src.agent.schemas import TopicSelection


class BuildContext(AsyncCommand):
    @abstractmethod
    async def run(
        self,
        topic_selection: TopicSelection,
        context_builder: ContextBuilder,
    ) -> ContextBuilder:
        pass

    async def __call__(
        self,
        topic_selection: TopicSelection,
        context_builder: ContextBuilder,
    ) -> ContextBuilder:
        return await self.run(topic_selection, context_builder)
