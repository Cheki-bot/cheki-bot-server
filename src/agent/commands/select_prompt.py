from langchain_core.prompts import PromptTemplate

from src.agent.interfaces.command import AsyncCommand
from src.agent.schemas import TopicSelection


class AsyncSelectPrompt(AsyncCommand):
    async def run(self, topic_selection: TopicSelection) -> PromptTemplate:
        # TODO: Implement the prompt selector logic
        return PromptTemplate.from_template("{topic}")

    async def __call__(self, *args, **kwargs) -> PromptTemplate:
        return await super().__call__(*args, **kwargs)
