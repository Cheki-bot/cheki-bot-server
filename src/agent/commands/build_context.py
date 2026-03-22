from src.agent.context_managers.context_builder import ContextBuilder
from src.agent.interfaces import AsyncCommand, BuildContext
from src.agent.schemas import Topic, TopicSelection


class BuildTopicContext(AsyncCommand):
    def __init__(self, build_commands: dict[Topic, BuildContext]) -> None:
        self.__build_commands = build_commands
        self.__context_builder: ContextBuilder | None = None

    @property
    def build_commands(self) -> dict[Topic, BuildContext]:
        return self.__build_commands

    @property
    def context_builder(self) -> ContextBuilder:
        if not self.__context_builder:
            self.__context_builder = ContextBuilder()
        return self.__context_builder

    @context_builder.setter
    def context_builder(self, value: ContextBuilder) -> None:
        if value is not self.__context_builder:
            raise ValueError("ContextBuilder must be the same instance as the existing one")
        self.__context_builder = value

    async def run(self, topic_selections: list[TopicSelection]) -> str:
        for topic_selection in topic_selections:
            if topic_selection.topic not in self.build_commands:
                continue

            self.context_builder = await self.build_commands[topic_selection.topic](
                topic_selection,
                self.context_builder,
            )

        return self.context_builder.build_context()

    async def __call__(self, topic_selections: list[TopicSelection]) -> str:
        return await self.run(topic_selections)
