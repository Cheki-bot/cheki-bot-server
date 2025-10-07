from collections import defaultdict

from langchain_core.documents import Document

from src.agent.interfaces.build_topic_prompt import BuildTopicPrompt
from src.agent.interfaces.command import AsyncCommand
from src.agent.schemas import Topic


class BuildTopicPrompts(AsyncCommand):
    def __init__(self, build_commands: dict[Topic, BuildTopicPrompt[Document]]) -> None:
        self.__build_commands = build_commands

    @property
    def build_commands(self) -> dict[Topic, BuildTopicPrompt[Document]]:
        return self.__build_commands

    async def run(self, documents: list[Document]) -> list[str]:
        grouped_docs = defaultdict(list[Document])
        for doc in documents:
            topic = doc.metadata.get("topic")
            if topic is None:
                continue
            grouped_docs[topic].append(doc)

        prompts = []

        for topic, docs in grouped_docs.items():
            command = self.build_commands.get(topic)
            prompt = (
                command
                and (await command(docs))
                or "## Información encontrada\n" + "\n".join([f"### {doc.page_content}" for doc in docs])
            )
            prompts.append(prompt)
        return prompts

    async def __call__(self, documents: list[Document]) -> list[str]:
        return await self.run(documents)
