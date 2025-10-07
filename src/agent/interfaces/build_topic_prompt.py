from abc import abstractmethod

from src.agent.interfaces.command import AsyncCommand


class BuildTopicPrompt[Document](AsyncCommand):
    @abstractmethod
    async def run(self, documents: list[Document]) -> str:
        pass

    @abstractmethod
    async def __call__(self, documents: list[Document]):
        return await self.run(documents)
